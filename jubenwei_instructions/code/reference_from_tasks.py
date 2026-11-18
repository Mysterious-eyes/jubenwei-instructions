"""Recover the study reference from the public instruction dataset and its source-row index."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from build_dataset.build_common import new_output
from rebuild_normalized import archived_bytes


RESOURCE = Path(__file__).resolve().parents[1]
INDEX = RESOURCE / 'evaluation' / 'reference_selection.json'


def load_pairs(dataset):
    """Read the main task from the release ZIP or an extracted overall_1.json."""
    if dataset.suffix.lower() == '.zip':
        with ZipFile(dataset) as archive:
            rows = json.loads(archive.read('sft_tasks/overall_1.json'))
    else:
        rows = json.loads(dataset.read_bytes())
    if len(rows) != 5016:
        raise ValueError(f'Expected 5,016 main-task records in v1.0.0, found {len(rows):,}.')

    pairs = []
    for source_row, record in enumerate(rows, 1):
        explanation, closing_tag, xml = record['output'].rpartition('</think>')
        if not closing_tag or not explanation.startswith('<think>'):
            raise ValueError(f'Missing main-task explanation delimiters in source row {source_row}.')
        xml = xml.strip()
        sentence = ''.join(t.strip() for t in ET.fromstring(xml).itertext())
        if record['instruction'] != f'给出句子“{sentence}”的句本位标注结果。':
            raise ValueError(f'Instruction and XML text disagree in source row {source_row}.')
        pairs.append([sentence, xml])
    return pairs


def recover_reference(pairs):
    index = json.loads(INDEX.read_bytes())
    reference = []
    for expected, entry in enumerate(index['records'], 1):
        source = entry['full_source_row_1based']
        if entry['test_row_1based'] != expected or not (1 <= source <= len(pairs)):
            raise ValueError(f'Invalid source-row index for test record {expected}.')
        reference.append(pairs[source - 1])
    blob = archived_bytes(reference)
    if len(reference) != index['reference_records'] or sha256(blob).hexdigest() != index['reference_sha256']:
        raise ValueError('The reconstructed reference differs from the archived 1,200-record reference.')
    return reference


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', required=True, type=Path,
                        help='Zenodo instruction ZIP or its extracted sft_tasks/overall_1.json.')
    parser.add_argument('--output-dir', type=Path, default=RESOURCE / 'reproduced' / 'public_reference')
    parser.add_argument('--source-pairs', action='store_true',
                        help='Also write the 5,016 normalized sentence/XML pairs for training-set construction.')
    args = parser.parse_args()
    pairs = load_pairs(args.dataset)
    reference = recover_reference(pairs)
    out = new_output(args.output_dir)
    (out / 'reference.json').write_bytes(archived_bytes(reference))
    (out / 'sentences.txt').write_text(''.join(s + '\n' for s, _ in reference), encoding='utf-8')
    if args.source_pairs:
        (out / 'sentence_xml_pairs.json').write_bytes(archived_bytes(pairs))
    print(f'Recovered {len(reference):,} test records in {out}')


if __name__ == '__main__':
    main()
