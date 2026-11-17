"""Recover the archived reference sample from its transparent source-location index."""
import argparse,hashlib,json,xml.etree.ElementTree as ET
from build_common import RELEASE,new_output,resolve
from preprocess import normalize_pairs

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index',default='evaluation/reference_selection.json')
    parser.add_argument('--output-dir',default='reproduced/evaluation_reference')
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args();index=json.loads(resolve(args.index).read_text(encoding='utf-8'))
    if args.dry_run:
        print(json.dumps({'records':index['reference_records'],'output':str(resolve(args.output_dir)),'random_resampling':False,'writes':False}));return
    trees={};pairs=[]
    for record in index['records']:
        name=record['source_file']
        if name not in trees:
            path=RELEASE/index['source_directory']/name
            trees[name]=list(ET.parse(path).getroot().iter('ju'))
        node=trees[name][record['ju_index_1based']-1]
        pairs.append([''.join(part.strip() for part in node.itertext()),ET.tostring(node,encoding='unicode').strip()])
    normalized=normalize_pairs(pairs)
    blob=json.dumps(normalized,ensure_ascii=False,indent=2).replace('\n','\r\n').encode('utf-8')
    assert len(normalized)==index['reference_records']==1200
    assert hashlib.sha256(blob).hexdigest()==index['reference_sha256']
    output=new_output(args.output_dir);(output/'reference.json').write_bytes(blob)
    print(json.dumps({'records':len(normalized),'sha256':hashlib.sha256(blob).hexdigest(),'exact_archived_reference':True,'random_resampling':False,'output':str(output)},ensure_ascii=False))

if __name__=='__main__':main()
