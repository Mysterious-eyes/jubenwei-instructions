"""Recompute the six model evaluations from the public instruction and prediction archives."""
import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
import sys
from zipfile import ZipFile

from evaluate import summarize
from reference_from_tasks import RESOURCE, load_pairs, recover_reference
from scoring import evaluate_outputs


def read_outputs(archive, member):
    data = archive.read(member['file'])
    if sha256(data).hexdigest() != member['sha256']:
        raise ValueError(f"Contents differ from the released file: {member['file']}")
    answers = []
    for position, line in enumerate(data.splitlines(), 1):
        row = json.loads(line)
        if row['case_id'] != f'T{position:04d}' or not isinstance(row['output'], str):
            raise ValueError(f"Invalid row {position} in {member['file']}")
        answers.append(row['output'])
    if len(answers) != member['rows']:
        raise ValueError(f"Unexpected record count in {member['file']}")
    return answers


def score_row(condition, reference, outputs):
    s = summarize(evaluate_outputs(reference, outputs))
    mode = ('on' if condition['thinking_enabled'] else 'off') if 'thinking_enabled' in condition else 'not_applicable'
    return {
        'condition': condition['id'], 'model': condition['model'], 'project_sft': int(condition['task_sft']),
        'thinking_mode': mode, 'n_inputs': s['total'], 'n_xml_parsable': s['valid'],
        'n_xml_unparsable': s['invalid'], 'n_text_consistent': s['valid_text_consistent_count'],
        'n_text_inconsistent': s['text_mismatch_count'], 'n_f1_scored': s['valid'],
        'n_structure_comparable': s['structure_evaluated'], 'n_structure_exact': s['structure_correct'],
        'xml_parsable_pct': s['xml_valid_percent'],
        'text_consistent_pct_all': 100 * s['valid_text_consistent_count'] / s['total'],
        'segmentation_f1_pct': 100 * s['separated_f1'], 'pos_f1_pct': 100 * s['pos_f1'],
        'dynamic_f1_pct': 100 * s['dynamic_f1'], 'syntax_f1_pct': 100 * s['grammar_f1'],
        'structure_exact_pct_comparable': s['conditional_structure_percent'],
        'structure_exact_pct_all': s['all_record_structure_percent'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', required=True, type=Path)
    parser.add_argument('--outputs', required=True, type=Path)
    parser.add_argument('--check', action='store_true', help='Compare the recomputed scores with evaluation/summary.csv.')
    args = parser.parse_args()
    manifest = json.loads((RESOURCE / 'evaluation' / 'outputs_manifest.json').read_bytes())
    if sha256(args.outputs.read_bytes()).hexdigest() != manifest['sha256']:
        parser.error('Output archive checksum does not match outputs_manifest.json.')
    reference = recover_reference(load_pairs(args.dataset))
    conditions = json.loads((RESOURCE / 'evaluation/conditions.json').read_bytes())['conditions']
    if [c['id'] for c in conditions] != [c['condition'] for c in manifest['conditions']]:
        parser.error('The condition list differs from the output manifest.')
    rows = []
    with ZipFile(args.outputs) as archive:
        for condition, member in zip(conditions, manifest['conditions']):
            row = score_row(condition, reference, read_outputs(archive, member))
            rows.append({k: f'{v:.2f}' if 'pct' in k else str(v) for k, v in row.items()})
    if args.check:
        with (RESOURCE / 'evaluation/summary.csv').open(encoding='utf-8', newline='') as f:
            if rows != list(csv.DictReader(f)):
                parser.error('Computed scores differ from evaluation/summary.csv.')
        print(f'All {len(rows)} conditions match evaluation/summary.csv.')
    else:
        writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


if __name__ == '__main__':
    main()
