"""Evaluate archived model outputs. Reads data only and prints JSON to stdout."""
import argparse
import hashlib
import json
from pathlib import Path
from scoring import evaluate, read_data_from_txt

ROOT = Path(__file__).resolve().parents[1]

def resolve(path):
    path = Path(path)
    return path if path.is_absolute() else ROOT / path

def summarize(result):
    valid = result['valid']
    comparable = result['structure_evaluated']
    total = result['total']
    report = {key: value for key, value in result.items()
              if key not in {'invalid_sentences', 'text_mismatches', 'conversion_errors'}}
    report['text_mismatch_count'] = len(result['text_mismatches'])
    report['valid_text_consistent_count'] = valid - len(result['text_mismatches'])
    report['xml_valid_percent'] = 100 * valid / total
    report['xml_invalid_percent'] = 100 * result['invalid'] / total
    report['conditional_structure_percent'] = 100 * result['structure_correct'] / comparable if comparable else None
    report['all_record_structure_percent'] = 100 * result['structure_correct'] / total
    # A zero-sized valid subset does not have an interpretable conditional F1.
    if not valid:
        for key in ['separated_f1', 'pos_f1', 'dynamic_f1', 'grammar_f1']:
            report[key] = None
    return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true', help='Evaluate every archived TXT prediction file')
    group.add_argument('--prediction', help='Prediction path, relative to the release directory or absolute')
    parser.add_argument('--reference', default='evaluation/reference.json')
    args = parser.parse_args()
    reference_path = resolve(args.reference)
    gold = json.loads(reference_path.read_text(encoding='utf-8-sig'))
    paths = sorted((ROOT / 'evaluation/predictions').glob('*.txt')) if args.all else [resolve(args.prediction)]
    results = {}
    for path in paths:
        predictions = read_data_from_txt(path)
        result = summarize(evaluate(gold, predictions))
        result['prediction_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        result['reference_sha256'] = hashlib.sha256(reference_path.read_bytes()).hexdigest()
        results[path.stem] = result
    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
