"""Generate and validate the complete15-task collection, not a training selection route."""
import argparse,json
from build_common import generate_tasks,new_output,resolve
from selection_rules import load_pairs

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',default='normalized/sentence_xml_pairs.json')
    parser.add_argument('--output-dir',default='reproduced/full_collection')
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args();source=resolve(args.source)
    if args.dry_run:
        print(json.dumps({'source':str(source),'output':str(resolve(args.output_dir)),'tasks':15,'writes':False}));return
    load_pairs(source);output=new_output(args.output_dir)
    report=generate_tasks(source,output/'sft_tasks',output/'generation_report.json')
    print(json.dumps({'task_files':len(report['datasets']),'records':sum(r['records'] for r in report['datasets'].values()),'output':str(output)},ensure_ascii=False))

if __name__=='__main__':main()
