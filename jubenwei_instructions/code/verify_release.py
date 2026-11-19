"""Verify a complete archive or a training instance using its declared selection policy."""
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from rebuild_normalized import build_pairs, archived_bytes
from scoring import read_data_from_txt
from build_dataset.selection_rules import (
    LEGACY_POLICY, SELECTION_POLICIES, load_pairs, policy_from_report,
    select_source_for_policy, selection_summary,
)

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check_instruction_rows(rows):
    for row in rows:
        assert set(row) == {'instruction', 'input', 'output'}
        assert all(isinstance(value, str) for value in row.values())
        assert row['instruction'].strip() and row['output'].strip()
        assert row['input'] == ''

def verify_training_instance(source_path, reference_path, training_dir, symbol_dir=None, expected_policy=None):
    selection = read(training_dir / 'split_report.json')
    policy = policy_from_report(selection)
    if expected_policy is not None and policy != expected_policy:
        raise ValueError(f'Expected {expected_policy}, but split_report declares {policy}')
    source, reference = load_pairs(source_path), load_pairs(reference_path)
    assert selection['source_sha256'] == sha256(source_path)
    assert selection.get('reference_sha256', selection.get('test_sha256')) == sha256(reference_path)
    selected, indices, excluded = select_source_for_policy(source, reference, policy)
    training_source = load_pairs(training_dir / 'training_source.json')
    assert training_source == selected
    assert selection['selected_source_rows_1based'] == indices
    assert selection['excluded_records'] == excluded
    assert selection['source_records'] == len(source)
    assert selection['selected_source_records'] == len(selected)
    assert selection.get('reference_records', selection.get('test_records')) == len(reference)
    summary = selection_summary(source, reference, selected, excluded, policy)
    # Older reports may lack newer diagnostic fields, but must declare their rule.
    for key, value in summary.items():
        if key in selection:
            assert selection[key] == value, key

    counts = {}
    dictionary_checked = symbol_dir is not None
    for name in ['integrated_data', 'learn_tag_1', 'learn_tag_2', 'overall_1']:
        rows = read(training_dir / (name + '.json'))
        check_instruction_rows(rows)
        counts[name] = len(rows)
        if name == 'overall_1':
            assert len(rows) == len(selected)
            assert all(row['output'].split('</think>', 1)[1] == pair[1]
                       for row, pair in zip(rows, selected))
        if name in {'learn_tag_1', 'learn_tag_2'} and symbol_dir is not None:
            assert rows == read(symbol_dir / (name + '.json'))
    assert counts['learn_tag_1'] == 54 and counts['learn_tag_2'] == 53
    assert counts['integrated_data'] == selection['integrated_records']
    auxiliary = {k: v for k, v in selection['task_counts'].items()
                 if k not in {'overall_1.json', 'learn_tag_1.json', 'learn_tag_2.json'}}
    assert len(auxiliary) == 12
    assert sum(v['sampled'] for v in auxiliary.values()) == counts['integrated_data']
    assert all(v['sampled'] == min(selection['requested_per_task'], v['generated'])
               for v in auxiliary.values())
    file_counts = {name + '.json': count for name, count in counts.items()}
    if 'training_file_counts' in selection:
        assert selection['training_file_counts'] == file_counts
    if 'training_instance_records' in selection:
        assert selection['training_instance_records'] == sum(counts.values())
    for name, digest in selection.get('output_sha256', {}).items():
        path = (training_dir / name).resolve()
        assert path.is_relative_to(training_dir.resolve())
        assert sha256(path) == digest, name
    result = {
        'training_selection_policy': policy,
        'training_instance_counts': counts,
        'training_instance_records': sum(counts.values()),
        'training_instance_exact_row_subset_assertion': False,
        'training_source_indices_verified': True,
        'dictionary_reference_checked': dictionary_checked,
        'selection_checks': summary,
    }
    if policy == LEGACY_POLICY:
        result['training_source_record_multiset_conserved'] = True
        result['deducted_reference_occurrences'] = len(reference)
    return result


def verify_archive(root, expected_policy=None):
    manifest = read(root / 'manifest.json')
    for entry in manifest['files']:
        path = root / entry['path']
        assert path.resolve().is_relative_to(root.resolve())
        blob = path.read_bytes()
        assert len(blob) == entry['bytes'], entry['path']
        assert hashlib.sha256(blob).hexdigest() == entry['sha256'], entry['path']
        if 'records' in entry:
            parsed = json.loads(blob.decode('utf-8-sig'))
            assert isinstance(parsed, list) and len(parsed) == entry['records'], entry['path']
        if 'json_top_level_entries' in entry:
            assert len(json.loads(blob.decode('utf-8-sig'))) == entry['json_top_level_entries'], entry['path']

    normalized = read(root / 'normalized/sentence_xml_pairs.json')
    rebuilt = build_pairs(root / 'source_annotations')
    assert rebuilt == normalized and len(normalized) == 5016
    normalization_byte_exact = archived_bytes(rebuilt) == (root / 'normalized/sentence_xml_pairs.json').read_bytes()
    for sentence, xml in normalized:
        assert ''.join(part.strip() for part in ET.fromstring(xml).itertext()) == sentence

    task_counts = {}
    for path in sorted((root / 'sft_tasks').glob('*.json')):
        rows = read(path)
        check_instruction_rows(rows)
        task_counts[path.stem] = len(rows)
        if path.stem == 'overall_1':
            assert len(rows) == len(normalized)
            assert all(row['output'].split('</think>', 1)[1] == pair[1] for row, pair in zip(rows, normalized))
    assert len(task_counts) == 15 and sum(task_counts.values()) == 392871
    assert task_counts['learn_tag_1'] == 54 and task_counts['learn_tag_2'] == 53

    training = verify_training_instance(
        root / 'normalized/sentence_xml_pairs.json', root / 'evaluation/reference.json',
        root / 'training_instance', root / 'sft_tasks', expected_policy)
    gold = read(root / 'evaluation/reference.json')
    assert len(gold) == 1200
    if training['training_selection_policy'] == LEGACY_POLICY:
        selection = read(root / 'training_instance/split_report.json')
        assert {item['test_row_1based'] for item in selection['excluded_records']} == set(range(1,1201))
    prediction_counts = {}
    for path in sorted((root / 'evaluation/predictions').glob('*.txt')):
        predicted = read_data_from_txt(path)
        assert len(predicted) == len(gold)
        assert all(row['Instruction'] == f'给出句子“{pair[0]}”的句本位标注结果。' for pair, row in zip(gold, predicted))
        prediction_counts[path.name] = len(predicted)
    assert len(prediction_counts) == 6
    return {'status': 'passed', 'scope': 'complete_archive', 'manifest_files_checked': len(manifest['files']),
                      'source_xml_files': len(list((root / 'source_annotations').glob('*.xml'))),
                      'normalized_records': len(normalized), 'normalization_byte_exact': normalization_byte_exact,
                      'full_task_counts': task_counts, 'full_instruction_records': sum(task_counts.values()),
                      **training, 'reference_records': 1200, 'prediction_records': prediction_counts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT, help='Complete archive root for manifest verification')
    parser.add_argument('--training-dir', type=Path, help='Verify only an independently generated training instance')
    parser.add_argument('--source', type=Path, help='Normalized source pairs for training-only verification')
    parser.add_argument('--reference', type=Path, help='Test reference for training-only verification')
    parser.add_argument('--symbol-dir', type=Path, help='Optional independent directory containing learn_tag_1/2.json')
    parser.add_argument('--expect-selection-policy', choices=SELECTION_POLICIES)
    args = parser.parse_args()
    root = args.root.resolve()
    resolve = lambda p: p.resolve() if p.is_absolute() else (root / p).resolve()
    if args.training_dir:
        if not args.source or not args.reference:
            parser.error('--training-dir requires --source and --reference')
        result = {'status': 'passed', 'scope': 'training_instance_only', 'manifest_files_checked': None,
                  **verify_training_instance(resolve(args.source), resolve(args.reference), resolve(args.training_dir),
                      resolve(args.symbol_dir) if args.symbol_dir else None, args.expect_selection_policy)}
    else:
        if args.source or args.reference or args.symbol_dir:
            parser.error('--source, --reference and --symbol-dir require --training-dir')
        result = verify_archive(root, args.expect_selection_policy)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
