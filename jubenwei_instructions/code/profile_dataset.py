"""Profile the public 15-task instruction ZIP or extracted task directory; print JSON only."""
import argparse
from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from reference_from_tasks import load_pairs


TASKS = {
    'overall_1': 'M0', 'learn_tag_1': 'A1', 'learn_tag_2': 'A2',
    'learn_tag_3': 'A3', 'learn_tag_4': 'A4', 'learn_separate_1': 'A5',
    'learn_pos_2': 'A6', 'dongtaici_1': 'A7', 'dongtaici_2': 'A8',
    'xiaoju_1': 'A9', 'single_core_1': 'A10', 'learn_grammar_2': 'A11',
    'weiciyu_1': 'A12', 'fuzaju_1': 'A13', 'XML_rule_1': 'A14',
}


def summarize(values):
    values = sorted(values)
    n = len(values)
    if not n:
        raise ValueError('Cannot profile an empty task')
    result = {'n': n, 'min': values[0], 'max': values[-1],
              'sum': sum(values), 'mean': sum(values) / n}
    for p in (10, 25, 50, 75, 90):
        rank = (n - 1) * p / 100
        lo, hi = math.floor(rank), math.ceil(rank)
        result[f'p{p}'] = values[lo] + (values[hi] - values[lo]) * (rank - lo)
    result['median'] = result['p50']
    return result


def frequencies(counter):
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def profile(dataset):
    dataset = Path(dataset)
    is_zip = dataset.is_file() and dataset.suffix.lower() == '.zip'
    folder = dataset / 'sft_tasks' if (dataset / 'sft_tasks').is_dir() else dataset
    archive = ZipFile(dataset) if is_zip else None
    per_task, all_instruction, all_output = [], [], []
    try:
        for stem, task_id in TASKS.items():
            name = f'sft_tasks/{stem}.json'
            blob = archive.read(name) if archive else (folder / f'{stem}.json').read_bytes()
            rows = json.loads(blob)
            if not isinstance(rows, list):
                raise ValueError(f'{name}: expected a JSON array')
            ins, outs, explained, unbalanced, nonempty_inputs = [], [], 0, 0, 0
            for index, row in enumerate(rows, 1):
                if not isinstance(row, dict) or set(row) != {'instruction', 'input', 'output'} or not all(isinstance(v, str) for v in row.values()):
                    raise ValueError(f'{name}, row {index}: expected three string fields')
                ins.append(len(row['instruction']))
                outs.append(len(row['output']))
                explained += '<think>' in row['output'] and '</think>' in row['output']
                unbalanced += row['output'].count('<think>') != row['output'].count('</think>')
                nonempty_inputs += bool(row['input'])
            per_task.append({
                'task_id': task_id, 'task': stem, 'file': name, 'sha256': sha256(blob).hexdigest(),
                'records': len(rows), 'instruction_chars': summarize(ins), 'output_chars': summarize(outs),
                'with_explanation_markup': explained, 'direct_answer_records': len(rows) - explained,
                'unbalanced_think_records': unbalanced, 'nonempty_input_records': nonempty_inputs,
            })
            all_instruction.extend(ins)
            all_output.extend(outs)
    finally:
        if archive:
            archive.close()

    # Reuse the same final-XML extraction and input/XML consistency checks as reference recovery.
    pairs = load_pairs(dataset if is_zip else folder / 'overall_1.json')
    attrs = {key: Counter() for key in ('scp', 'fun', 'mod')}
    clauses = 0
    for _, xml in pairs:
        tree = ET.fromstring(xml)
        clauses += sum(1 for _ in tree.iter('xj'))
        for node in tree.iter():
            for key in attrs:
                if key in node.attrib:
                    attrs[key][node.attrib[key]] += 1
    counts = {item['task']: item['records'] for item in per_task}
    total = sum(counts.values())
    explained = sum(item['with_explanation_markup'] for item in per_task)
    symbols = counts['learn_tag_1'] + counts['learn_tag_2']
    paired = sum(counts[k] for k in ('learn_tag_3', 'learn_pos_2', 'learn_tag_4', 'learn_grammar_2'))
    mod_top10 = list(frequencies(attrs['mod']).items())[:10]
    return {
        'format_version': '1.0',
        'unit': 'Unicode code points (Python len), including all stored explanation, XML and formatting text',
        'quantile_method': 'Linear interpolation at (n-1)*p/100; every record retained',
        'explanation_definition': 'Output contains both literal <think> and </think> markers',
        'counts': {'full_examples': total, 'task_files': len(per_task), 'main_examples': counts['overall_1'],
                   'auxiliary_examples': total - counts['overall_1'], 'symbol_examples': symbols,
                   'corpus_examples': total - symbols},
        'instruction_chars': summarize(all_instruction), 'output_chars': summarize(all_output),
        'with_explanation_markup': explained, 'with_explanation_percent': 100 * explained / total,
        'direct_answer_records': total - explained, 'direct_answer_percent': 100 * (total - explained) / total,
        'unbalanced_think_records': sum(item['unbalanced_think_records'] for item in per_task),
        'nonempty_input_records': sum(item['nonempty_input_records'] for item in per_task),
        'per_task': per_task,
        'main_xml': {
            'records': len(pairs), 'clauses': clauses,
            'final_xml_chars': summarize([len(xml) for _, xml in pairs]),
            'attribute_totals': {key: sum(counter.values()) for key, counter in attrs.items()},
            **{key: frequencies(counter) for key, counter in attrs.items()},
            'mod_distinct_patterns': len(attrs['mod']),
            'mod_top10': [{'code': key, 'count': value} for key, value in mod_top10],
            'top10_mod_total': sum(value for _, value in mod_top10),
        },
        'paired_node_tasks': {
            'task_ids': ['A3', 'A6', 'A4', 'A11'],
            'word_class_targets': counts['learn_tag_3'], 'constituent_targets': counts['learn_tag_4'],
            'paired_task_counts_equal': counts['learn_tag_3'] == counts['learn_pos_2'] and counts['learn_tag_4'] == counts['learn_grammar_2'],
            'examples': paired, 'denominator': total, 'percent': 100 * paired / total,
            'percent_one_decimal': round(100 * paired / total, 1),
        },
    }


def check_figure_data(result, path):
    """Check only quantities derivable from the full task ZIP, not training/model results."""
    data = json.loads(Path(path).read_bytes())
    tasks = {row['task']: row for row in result['per_task']}
    checks = 0

    def equal(actual, expected, label):
        nonlocal checks
        if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-9):
            raise ValueError(f'Figure data mismatch: {label}: computed {actual}, figure {expected}')
        checks += 1

    for key in ('full_examples', 'corpus_examples', 'symbol_examples'):
        equal(result['counts'][key], data['counts'][key], key)
    equal(result['main_xml']['records'], data['counts']['source_records'], 'main XML records')
    for task in data['tasks']:
        equal(tasks[task['stem']]['records'], task['full_n'], task['stem'])
    figures = {item['number']: item for item in data['figures']}
    five = {panel['id']: panel for panel in figures[5]['panels']}
    for row in five['a']['rows']:
        equal(tasks[row['stem']]['records'], row['n'], row['stem'] + '.n')
        for key in ('p10', 'p25', 'median', 'p75', 'p90'):
            equal(tasks[row['stem']]['output_chars'][key], row[key], row['stem'] + '.' + key)
    equal(result['with_explanation_markup'], five['b']['rows'][0]['count'], 'explanations')
    equal(result['direct_answer_records'], five['b']['rows'][1]['count'], 'direct answers')
    equal(result['counts']['full_examples'], five['b']['denominator'], 'supervision denominator')
    six, xml = figures[6], result['main_xml']
    equal(xml['records'], six['population'], 'XML population')
    for key, count in six['attribute_totals'].items():
        equal(xml['attribute_totals'][key], count, key + ' total')
    for key in ('mod_distinct_patterns', 'top10_mod_total'):
        equal(xml[key], six[key], key)
    for panel in six['panels']:
        for row in panel['rows']:
            equal(xml[panel['attribute']].get(row['code'], 0), row['count'], panel['attribute'] + ':' + row['code'])
    return {'status': 'passed', 'numeric_checks': checks,
            'scope': 'Full-task counts, length quantiles, explanation counts and final-XML attributes'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', required=True, type=Path,
                        help='Public instruction ZIP, extracted sft_tasks/, or its parent directory')
    parser.add_argument('--check-figure-data', type=Path,
                        help='Optional figures/data/figure_data.json to check against the computed profile')
    args = parser.parse_args()
    result = profile(args.dataset)
    if args.check_figure_data:
        result['figure_check'] = check_figure_data(result, args.check_figure_data)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
