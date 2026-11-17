"""Rebuild normalized sentence/XML pairs into a separate output directory."""
import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def build_pairs(source_directory):
    records = []
    for path in sorted(Path(source_directory).glob('*.xml')):
        root = ET.parse(path).getroot()
        for sentence in root.iter('ju'):
            plain = ''.join(part.strip() for part in sentence.itertext())
            # Serialize/reparse each sentence as in the recorded preprocessing.
            node = ET.fromstring(ET.tostring(sentence, encoding='unicode').strip())
            for element in node.iter():
                for attribute in list(element.attrib):
                    if attribute not in {'scp', 'fun', 'mod'}:
                        del element.attrib[attribute]
            xml = ET.tostring(node, encoding='unicode')
            xml = re.sub(r'>\s+<', '><', xml)
            xml = re.sub(r'\s+/>', '/>', xml)
            records.append([plain, xml])
    return records

def archived_bytes(records):
    # Preserve the historical serialization, including CRLF outside JSON strings.
    return json.dumps(records, ensure_ascii=False, indent=2).replace('\n', '\r\n').encode('utf-8')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='reproduced/sentence_xml_pairs.json')
    args = parser.parse_args()
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    allowed = (ROOT / 'reproduced').resolve()
    if not output.resolve().is_relative_to(allowed):
        parser.error('Output must stay inside the separate reproduced directory')
    if output.exists():
        parser.error('Output already exists; choose a new file name')
    records = build_pairs(ROOT / 'source_annotations')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(archived_bytes(records))
    print(json.dumps({'records': len(records), 'output': str(output.relative_to(ROOT))}, ensure_ascii=False))

if __name__ == '__main__':
    main()
