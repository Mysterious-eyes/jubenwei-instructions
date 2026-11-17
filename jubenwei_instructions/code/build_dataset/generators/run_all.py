"""生成全部辅助任务和 20250731 修正版主任务，并检查 Alpaca 格式。"""

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET


BASE = Path(__file__).resolve().parent
from generation_paths import SOURCE_FILE, OUTPUT_DIR, REPORT_FILE, REFERENCE_FILE
SOURCE = SOURCE_FILE
TASKS = [
    'learn_tag_1', 'learn_tag_2', 'learn_tag_3', 'learn_tag_4',
    'learn_separate_1', 'learn_pos_2', 'learn_grammar_2',
    'xiaoju_1', 'single_core_1', 'dongtaici_1', 'dongtaici_2',
    'weiciyu_1', 'fuzaju_1', 'XML_rule_1', 'overall_1',
]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_xml_rules(rows):
    counts = Counter()
    for i, row in enumerate(rows):
        sentence, xml = row['instruction'].removeprefix('分析句子“').split('”句本位标注结果“', 1)
        xml = xml.removesuffix('”的文本内容是否和原句完全匹配、XML标签是否配对以及标签的嵌套是否符合规则。')
        answer = row['output'].split('</think>', 1)[1]
        try:
            root = ET.fromstring(xml)
            text = ''.join(root.itertext())
        except ET.ParseError:
            root, text = None, None
        if '出现标签不配对' in answer:
            kind, valid = 'unpaired', root is None
        elif '出现标签嵌套层次不对' in answer:
            kind, valid = 'hierarchy', root is not None and root.tag != 'ju' and text == sentence
        elif '出现文本片段顺序不同' in answer:
            kind, valid = 'swap', root is not None and text != sentence and Counter(text) == Counter(sentence)
        elif '出现文本片段丢失' in answer:
            kind, valid = 'delete', root is not None and len(text) < len(sentence)
        elif '出现文本片段重复' in answer:
            kind, valid = 'copy', root is not None and len(text) > len(sentence)
        else:
            kind, valid = 'original', root is not None and root.tag == 'ju' and text == sentence
        if not valid:
            raise ValueError(f'XML_rule_1[{i}]: incorrect corruption label ({kind})')
        counts[kind] += 1
    return dict(counts)


def validate_outputs():
    source = json.loads(SOURCE.read_text(encoding='utf-8'))
    roots = [ET.fromstring(row[1]) for row in source]
    xjs = [xj for root in roots for xj in root.iter('xj')]
    from jubenwei_utils import jufa_tags, weiyu_tag2language
    from download_tools.self_explain.LLM_tools import get_single_core

    expected = {
        'overall_1': len(source), 'learn_separate_1': len(source),
        'xiaoju_1': len(source), 'single_core_1': len(xjs),
        'dongtaici_1': len(xjs), 'fuzaju_1': len(xjs),
        'dongtaici_2': sum('mod' in e.attrib for xj in xjs for e in xj.iter()),
        'weiciyu_1': sum('scp' in e.attrib for xj in xjs for e in xj.iter('prd')),
        'learn_tag_3': sum(bool(e.text and e.text.strip()) for xj in xjs for e in xj.iter()),
        'learn_pos_2': sum(bool(e.text and e.text.strip()) for xj in xjs for e in xj.iter()),
        'learn_tag_4': sum(e.tag in jufa_tags and bool(''.join(e.itertext()).strip()) for xj in xjs for e in xj.iter()),
        'learn_grammar_2': sum(e.tag in jufa_tags and bool(''.join(e.itertext()).strip()) for xj in xjs for e in xj.iter()),
    }
    report = {
        'source': SOURCE.name, 'source_sha256': sha256(SOURCE),
        'source_records': len(source), 'unique_source_sentences': len({r[0] for r in source}),
        'small_clauses': len(xjs), 'main_version': '20250731-corrected',
        'python': sys.version, 'length_unit': 'Unicode characters, not model tokens',
        'datasets': {},
    }
    for task in TASKS:
        path = OUTPUT_DIR / f'{task}.json'
        rows = json.loads(path.read_text(encoding='utf-8'))
        if not rows or (task in expected and len(rows) != expected[task]):
            raise ValueError(f'{task}: unexpected number of records: {len(rows)}')
        seen = set()
        answers = {}
        lengths = []
        for i, row in enumerate(rows):
            if set(row) != {'instruction', 'input', 'output'} or not all(isinstance(v, str) for v in row.values()):
                raise ValueError(f'{task}[{i}]: invalid Alpaca schema')
            if not row['instruction'] or not row['output'] or row['input'] != '':
                raise ValueError(f'{task}[{i}]: invalid text fields')
            output = row['output']
            if output.count('<think>') != output.count('</think>'):
                raise ValueError(f'{task}[{i}]: unbalanced think tags')
            seen.add((row['instruction'], row['input'], output))
            answers.setdefault((row['instruction'], row['input']), set()).add(output)
            lengths.append(len(output))
            if task == 'overall_1':
                if not output.startswith('<think>') or output.count('</think>') != 1:
                    raise ValueError(f'{task}[{i}]: invalid explanation wrapper')
                xml = output.split('</think>', 1)[1]
                if xml != source[i][1] or ET.fromstring(xml).tag != 'ju':
                    raise ValueError(f'{task}[{i}]: final XML differs from source')
                if row['instruction'] != f'给出句子“{source[i][0]}”的句本位标注结果。':
                    raise ValueError(f'{task}[{i}]: sentence differs from source')
            if task == 'learn_separate_1':
                tokens = [e.text.strip() for e in roots[i].iter() if e.text and e.text.strip()]
                if output != '/'.join(tokens) or ''.join(tokens) != source[i][0]:
                    raise ValueError(f'{task}[{i}]: token order differs from source')
        ordered = sorted(lengths)
        report['datasets'][path.name] = {
            'records': len(rows), 'duplicate_records': len(rows) - len(seen),
            'inputs_with_multiple_outputs': sum(len(v) > 1 for v in answers.values()),
            'output_chars_mean': round(sum(lengths) / len(lengths), 2),
            'output_chars_p90': ordered[(len(ordered) * 9 - 1) // 10],
            'output_chars_max': max(lengths), 'sha256': sha256(path),
        }
        if task == 'XML_rule_1':
            report['xml_rule_operations'] = validate_xml_rules(rows)
    source_groups = defaultdict(list)
    for i, (sentence, xml) in enumerate(source):
        source_groups[sentence].append((i + 1, xml))
    report['source_annotation_conflicts'] = [
        {'sentence': sentence, 'source_rows_1based': [i for i, xml in items],
         'distinct_annotations': len({xml for i, xml in items})}
        for sentence, items in source_groups.items() if len({xml for i, xml in items}) > 1
    ]
    report['unknown_scopes'] = [
        {'source_row_1based': i + 1, 'sentence': row[0], 'scope': e.get('scp')}
        for i, (row, root) in enumerate(zip(source, roots)) for e in root.iter('prd')
        if e.get('scp') is not None and e.get('scp').upper() not in weiyu_tag2language
    ]
    report['clauses_without_extracted_core'] = sum(
        not get_single_core('<ju>' + ET.tostring(xj, encoding='unicode') + '</ju>') for xj in xjs
    )
    report['reference_text_check'] = {}
    if REFERENCE_FILE is not None:
        tests = json.loads(REFERENCE_FILE.read_text(encoding='utf-8-sig'))
        train_texts = {row[0] for row in source}
        report['reference_text_check'] = {
            'records': len(tests),
            'matching_source_text': sum(row[0] in train_texts for row in tests),
        }
    report['source_code_sha256'] = {
        str(p.relative_to(BASE)): sha256(p)
        for p in sorted(BASE.rglob('*.py'))
    }
    REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for task in TASKS:
        print(f'Generating {task} ...', flush=True)
        result = subprocess.run(
            [sys.executable, '-B', '-X', 'utf8', str(BASE / f'generate_data_{task}.py')],
            cwd=BASE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            encoding='utf-8',
        )
        if result.returncode:
            raise RuntimeError(f'{task} failed:\n{result.stderr}')
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    report = validate_outputs()
    for name, stats in report['datasets'].items():
        print(f'{name}: {stats["records"]} records')
    print('Validated all outputs. See generation_report.json for counts and limitations.')


if __name__ == '__main__':
    main()
