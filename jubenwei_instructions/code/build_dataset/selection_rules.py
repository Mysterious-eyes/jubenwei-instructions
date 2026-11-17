"""Official multiplicity-based record subtraction; no additional text or clause exclusion."""
import json
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict, deque

def normalized(text):
    """仅忽略空白差异，保留标点、大小写及其他字符。"""
    return ''.join(text.split())

def load_pairs(path):
    rows = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(rows, list) or not rows:
        raise ValueError(f'数据必须是非空列表：{path}')
    for index, row in enumerate(rows, 1):
        if not isinstance(row, list) or len(row) != 2 or (not all((isinstance(v, str) for v in row))):
            raise ValueError(f'{path} 第 {index} 条必须是 [原句, XML]')
        root = ET.fromstring(row[1])
        if root.tag != 'ju' or not normalized(row[0]):
            raise ValueError(f'{path} 第 {index} 条必须有原句和 ju 根节点')
        if normalized(''.join(root.itertext())) != normalized(row[0]):
            raise ValueError(f'{path} 第 {index} 条原句与 XML 文本不一致')
    return rows

def record_key(row):
    """按原句和规范化 XML 匹配，不把不同标注的同文本记录混为一条。"""
    return (normalized(row[0]), ET.canonicalize(row[1], strip_text=True))

def select_source(source, test):
    """每条测试记录只扣除一条源记录，保留其余重复文本及共享小句。"""
    source_counts = Counter((record_key(row) for row in source))
    test_counts = Counter((record_key(row) for row in test))
    missing = test_counts - source_counts
    if missing:
        example = next(iter(missing))[0]
        raise ValueError(f'有 {sum(missing.values())} 条测试记录无法按原句和 XML 匹配源数据，例如：{example}')
    test_indices = defaultdict(deque)
    for index, row in enumerate(test, 1):
        test_indices[record_key(row)].append(index)
    selected, selected_indices, excluded = ([], [], [])
    for index, row in enumerate(source, 1):
        matches = test_indices.get(record_key(row))
        if matches:
            excluded.append({'source_row_1based': index, 'test_row_1based': matches.popleft(), 'reason': 'selected_test_record'})
        else:
            selected.append(row)
            selected_indices.append(index)
    if not selected:
        raise ValueError('扣除测试记录后没有可用训练记录')
    assert len(excluded) == len(test)
    assert len(selected) + len(test) == len(source)
    return (selected, selected_indices, excluded)
