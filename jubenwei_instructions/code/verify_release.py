"""Verify the current full collection and the separately archived training instance."""
import hashlib
import json
from collections import Counter
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from rebuild_normalized import build_pairs, archived_bytes
from scoring import read_data_from_txt
from build_dataset.selection_rules import record_key, select_source

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def check_instruction_rows(rows):
    for row in rows:
        assert set(row) == {'instruction', 'input', 'output'}
        assert all(isinstance(value, str) for value in row.values())
        assert row['instruction'].strip() and row['output'].strip()
        assert row['input'] == ''

def main():
    manifest = read(ROOT / 'manifest.json')
    for entry in manifest['files']:
        path = ROOT / entry['path']
        assert path.resolve().is_relative_to(ROOT.resolve())
        blob = path.read_bytes()
        assert len(blob) == entry['bytes'], entry['path']
        assert hashlib.sha256(blob).hexdigest() == entry['sha256'], entry['path']
        if 'records' in entry:
            parsed = json.loads(blob.decode('utf-8-sig'))
            assert isinstance(parsed, list) and len(parsed) == entry['records'], entry['path']
        if 'json_top_level_entries' in entry:
            assert len(json.loads(blob.decode('utf-8-sig'))) == entry['json_top_level_entries'], entry['path']

    normalized = read(ROOT / 'normalized/sentence_xml_pairs.json')
    rebuilt = build_pairs(ROOT / 'source_annotations')
    assert rebuilt == normalized and len(normalized) == 5016
    normalization_byte_exact = archived_bytes(rebuilt) == (ROOT / 'normalized/sentence_xml_pairs.json').read_bytes()
    for sentence, xml in normalized:
        assert ''.join(part.strip() for part in ET.fromstring(xml).itertext()) == sentence

    task_counts = {}
    for path in sorted((ROOT / 'sft_tasks').glob('*.json')):
        rows = read(path)
        check_instruction_rows(rows)
        task_counts[path.stem] = len(rows)
        if path.stem == 'overall_1':
            assert len(rows) == len(normalized)
            assert all(row['output'].split('</think>', 1)[1] == pair[1] for row, pair in zip(rows, normalized))
    assert len(task_counts) == 15 and sum(task_counts.values()) == 392871
    assert task_counts['learn_tag_1'] == 54 and task_counts['learn_tag_2'] == 53

    instance_counts = {}
    for name in ['integrated_data', 'learn_tag_1', 'learn_tag_2', 'overall_1']:
        path = ROOT / 'training_instance' / (name + '.json')
        rows = read(path)
        check_instruction_rows(rows)
        instance_counts[name] = len(rows)
        if name in {'learn_tag_1', 'learn_tag_2'}:
            assert rows == read(ROOT / 'sft_tasks' / (name + '.json'))
    assert instance_counts == {'integrated_data': 12000, 'learn_tag_1': 54, 'learn_tag_2': 53, 'overall_1': 3816}
    assert sum(instance_counts.values()) == 15923
    # The training instance was regenerated after source selection. In particular,
    # controlled XML corruptions need not be identical to full-collection rows.
    # Do not impose a record-membership assertion on the integrated training file.

    gold = read(ROOT / 'evaluation/reference.json')
    assert len(gold) == 1200
    selection = read(ROOT / 'training_instance/split_report.json')
    training_source = read(ROOT / 'training_instance/training_source.json')
    assert len(training_source) == selection['selected_source_records'] == 3816
    assert training_source == [normalized[i-1] for i in selection['selected_source_rows_1based']]
    main_training = read(ROOT / 'training_instance/overall_1.json')
    assert all(row['output'].split('</think>',1)[1] == pair[1] for row,pair in zip(main_training,training_source))
    assert len(gold)+len(training_source)==len(normalized)==5016
    assert Counter(map(record_key,training_source))+Counter(map(record_key,gold))==Counter(map(record_key,normalized))
    selected,selected_indices,excluded=select_source(normalized,gold)
    assert selected==training_source and selected_indices==selection['selected_source_rows_1based']
    assert excluded==selection['excluded_records'] and len(excluded)==1200
    assert {item['test_row_1based'] for item in excluded}==set(range(1,1201))
    prediction_counts = {}
    for path in sorted((ROOT / 'evaluation/predictions').glob('*.txt')):
        predicted = read_data_from_txt(path)
        assert len(predicted) == len(gold)
        assert all(row['Instruction'] == f'给出句子“{pair[0]}”的句本位标注结果。' for pair, row in zip(gold, predicted))
        prediction_counts[path.name] = len(predicted)
    assert len(prediction_counts) == 6
    print(json.dumps({'status': 'passed', 'manifest_files_checked': len(manifest['files']),
                      'source_xml_files': len(list((ROOT / 'source_annotations').glob('*.xml'))),
                      'normalized_records': len(normalized), 'normalization_byte_exact': normalization_byte_exact,
                      'full_task_counts': task_counts, 'full_instruction_records': sum(task_counts.values()),
                      'training_instance_counts': instance_counts, 'training_instance_records': sum(instance_counts.values()),
                      'training_instance_exact_row_subset_assertion': False,
                      'training_source_indices_verified': True,
                      'training_source_record_multiset_conserved': True,
                      'deducted_reference_occurrences': 1200,
                      'reference_records': 1200, 'prediction_records': prediction_counts}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
