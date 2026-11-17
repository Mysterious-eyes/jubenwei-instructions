"""Formal entry: subtract fixed reference records by multiplicity, regenerate, sample."""
import argparse,json,random,shutil,sys
from collections import Counter
from pathlib import Path
from build_common import RELEASE,generate_tasks,new_output,resolve,sha256,write_json
from selection_rules import load_pairs,record_key,select_source

def generate_and_sample(source_path,reference_path,output_dir,per_task=1000,seed=0):
    source_path,reference_path=map(resolve,(source_path,reference_path))
    if per_task<1:raise ValueError('per_task must be positive')
    source,reference=load_pairs(source_path),load_pairs(reference_path)
    selected,selected_indices,excluded=select_source(source,reference)
    print(f'Source {len(source)}; reference {len(reference)}; selected {len(selected)}.',flush=True)
    output=new_output(output_dir)
    write_json(output/'training_source.json',selected)
    generation=generate_tasks(output/'training_source.json',output/'generated_tasks',output/'generation_report.json',reference_path)
    rng=random.Random(seed);sampled=[];task_counts={}
    for path in sorted((output/'generated_tasks').glob('*.json')):
        rows=json.loads(path.read_text(encoding='utf-8'));count=0
        if path.stem not in {'overall_1','learn_tag_1','learn_tag_2'}:
            count=min(per_task,len(rows));sampled.extend(rng.sample(rows,count))
        task_counts[path.name]={'generated':len(rows),'sampled':count}
    for name in ['overall_1.json','learn_tag_1.json','learn_tag_2.json']:
        shutil.copyfile(output/'generated_tasks'/name,output/name)
    write_json(output/'integrated_data.json',sampled)
    info={name:{'file_name':name+'.json','formatting':'alpaca','columns':{'prompt':'instruction','query':'input','response':'output'}} for name in ['integrated_data','learn_tag_1','learn_tag_2','overall_1']}
    write_json(output/'dataset_info.json',info)
    training_files=['integrated_data.json','learn_tag_1.json','learn_tag_2.json','overall_1.json']
    train_counts={name:len(json.loads((output/name).read_text(encoding='utf-8'))) for name in training_files}
    assert len(selected)+len(reference)==len(source)
    assert len(excluded)==len(reference)
    assert Counter(map(record_key,selected))+Counter(map(record_key,reference))==Counter(map(record_key,source))
    report={'source_sha256':sha256(source_path),'reference_sha256':sha256(reference_path),'source_file':source_path.name,'reference_file':reference_path.name,
        'python':sys.version,'seed':seed,'requested_per_task':per_task,'normalization':'remove whitespace only; preserve punctuation and case',
        'selection_policy':'subtract_test_records_by_multiplicity','record_matching':'normalized sentence + XML C14N with strip_text=True; identical records consumed in source order',
        'exclude_shared_clauses':False,'remove_all_text_duplicates':False,'record_multiset_conserved':True,
        'source_records':len(source),'reference_records':len(reference),'selected_source_records':len(selected),
        'excluded_test_record_count':len(excluded),'excluded_shared_clause_records':0,
        'selected_source_rows_1based':selected_indices,'excluded_records':excluded,'task_counts':task_counts,'integrated_records':len(sampled),
        'training_file_counts':train_counts,'training_instance_records':sum(train_counts.values()),'generation_validation':generation,
        'entry_script_sha256':sha256(Path(__file__)),'output_sha256':{name:sha256(output/name) for name in training_files+['training_source.json','dataset_info.json']},
        'status':'complete','algorithm_note':'Each fixed reference record consumes one equivalent source occurrence. All other records are retained. Task regeneration and sorted sampling use the established generators and random.Random(seed). Static dictionary outputs are published alongside the corpus-derived files.'}
    write_json(output/'split_report.json',report)
    print(json.dumps({'selected_source_records':len(selected),'integrated_records':len(sampled),'training_file_counts':train_counts,'training_instance_records':sum(train_counts.values()),'output':str(output)},ensure_ascii=False))
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',default='normalized/sentence_xml_pairs.json')
    parser.add_argument('--reference','--test',dest='reference',default='evaluation/reference.json')
    parser.add_argument('--output-dir',default='reproduced/training_instance')
    parser.add_argument('--per-task',type=int,default=1000);parser.add_argument('--seed',type=int,default=0)
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    if args.dry_run:
        print(json.dumps({'source':str(resolve(args.source)),'reference':str(resolve(args.reference)),'output':str(resolve(args.output_dir)),'per_task':args.per_task,'seed':args.seed,'selection_policy':'subtract_test_records_by_multiplicity','writes':False}));return
    generate_and_sample(args.source,args.reference,args.output_dir,args.per_task,args.seed)

if __name__=='__main__':main()
