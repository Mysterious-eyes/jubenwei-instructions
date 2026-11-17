"""Extract sentence XML and normalize its attributes into an independent directory."""
import argparse,json,re,xml.etree.ElementTree as ET
from pathlib import Path
from build_common import RELEASE,new_output,resolve,sha256,write_json

def extract_pairs(directory):
    pairs=[];files=[]
    for path in sorted(p for p in Path(directory).rglob('*') if p.is_file() and p.suffix.lower()=='.xml'):
        root=ET.parse(path).getroot();count=0
        for sentence in root.iter('ju'):
            pairs.append([''.join(part.strip() for part in sentence.itertext()),ET.tostring(sentence,encoding='unicode').strip()]);count+=1
        files.append({'file':str(path.relative_to(directory)),'sentences':count,'sha256':sha256(path)})
    if not pairs:raise ValueError('No sentence annotations found')
    return pairs,files

def normalize_pairs(pairs):
    result=[]
    for sentence,xml in pairs:
        root=ET.fromstring(xml)
        for node in root.iter():
            for attribute in list(node.attrib):
                if attribute not in {'scp','fun','mod'}:del node.attrib[attribute]
        normalized=ET.tostring(root,encoding='unicode')
        normalized=re.sub(r'>\s+<','><',normalized);normalized=re.sub(r'\s+/>','/>',normalized)
        result.append([sentence,normalized])
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir',default='source_annotations')
    parser.add_argument('--output-dir',default='reproduced/preprocessing')
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args();source=resolve(args.source_dir)
    if args.dry_run:
        print(json.dumps({'source_directory':str(source),'output_directory':str(resolve(args.output_dir)),'writes':False}));return
    output=new_output(args.output_dir);pairs,files=extract_pairs(source);normalized=normalize_pairs(pairs)
    # Historical JSON serialization: UTF-8, two-space indentation, platform text newlines.
    for name,data in [('extracted_pairs.json',pairs),('sentence_xml_pairs.json',normalized)]:
        (output/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    report={'source_xml_files':len(files),'sentence_records':len(pairs),'retained_attributes':['scp','fun','mod'],'source_files':files,'output_sha256':{name:sha256(output/name) for name in ['extracted_pairs.json','sentence_xml_pairs.json']}}
    write_json(output/'preprocess_report.json',report);print(json.dumps({'source_xml_files':len(files),'sentence_records':len(pairs),'output':str(output)},ensure_ascii=False))

if __name__=='__main__':main()
