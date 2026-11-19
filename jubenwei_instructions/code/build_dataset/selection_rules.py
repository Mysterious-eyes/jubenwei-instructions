"""Whole-sentence test-text exclusion, with an explicit legacy record-subtraction policy."""
import json
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict, deque

CURRENT_POLICY = 'exclude_all_matching_test_sentences'
LEGACY_POLICY = 'subtract_test_records_by_multiplicity'
SELECTION_POLICIES = (CURRENT_POLICY, LEGACY_POLICY)

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
    """Historical record key; not used to match the current text-exclusion policy."""
    return (normalized(row[0]), ET.canonicalize(row[1], strip_text=True))

def clause_texts(xml):
    return {normalized(''.join(node.itertext()))
            for node in ET.fromstring(xml).iter('xj')} - {''}


def select_source(source, test):
    """按完整句子文本排除所有测试重复记录，不比较 XML，不按小句排除。"""
    test_sentences = {normalized(row[0]) for row in test}
    source_sentences = {normalized(row[0]) for row in source}
    missing = test_sentences - source_sentences
    if missing:
        raise ValueError(f'有 {len(missing)} 个测试原句不在源数据中，请核对输入，例如：{sorted(missing)[0]}')
    selected, selected_indices, excluded = [], [], []
    for index, row in enumerate(source, 1):
        if normalized(row[0]) in test_sentences:
            excluded.append({'source_row_1based': index, 'reason': 'test_sentence'})
        else:
            selected.append(row)
            selected_indices.append(index)
    if not selected:
        raise ValueError('排除与测试集相同的整句后没有可用训练记录')
    assert len(selected) + len(excluded) == len(source)
    assert not ({normalized(row[0]) for row in selected} & test_sentences)
    return selected, selected_indices, excluded


def select_source_by_record(source, test):
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


def select_source_for_policy(source, test, policy=CURRENT_POLICY):
    if policy == CURRENT_POLICY:
        return select_source(source, test)
    if policy == LEGACY_POLICY:
        return select_source_by_record(source, test)
    raise ValueError(f'Unknown selection policy: {policy!r}')


def policy_from_report(report):
    """Require an explicit known policy; never infer a version from its row count."""
    policy = report.get('selection_policy')
    if policy not in SELECTION_POLICIES:
        raise ValueError(f'Split report must declare a supported selection_policy: {policy!r}')
    return policy


def selection_summary(source, test, selected, excluded, policy):
    """Report the chosen rule and its invariants without excluding shared clauses."""
    if policy not in SELECTION_POLICIES:
        raise ValueError(f'Unknown selection policy: {policy!r}')
    excluded_indices = [row['source_row_1based'] for row in excluded]
    if len(excluded_indices) != len(set(excluded_indices)) or any(i < 1 or i > len(source) for i in excluded_indices):
        raise ValueError('Excluded source indices must be unique and in range')
    removed = [source[i - 1] for i in excluded_indices]
    assert len(selected) + len(removed) == len(source)
    assert Counter(map(tuple, selected)) + Counter(map(tuple, removed)) == Counter(map(tuple, source))
    test_sentences = {normalized(row[0]) for row in test}
    retained_sentences = {normalized(row[0]) for row in selected}
    overlap = retained_sentences & test_sentences
    test_clauses = set().union(*(clause_texts(row[1]) for row in test))
    retained_clauses = set().union(*(clause_texts(row[1]) for row in selected))
    result = {
        'selection_policy': policy,
        'normalization': 'remove whitespace only; preserve punctuation and case',
        'record_matching': ('normalized whole sentence only; exclude every source match regardless of XML annotation'
                            if policy == CURRENT_POLICY else
                            'normalized sentence + XML C14N with strip_text=True; identical records consumed in source order'),
        'exclude_shared_clauses': False,
        'remove_all_test_text_matches': policy == CURRENT_POLICY,
        'remove_all_text_duplicates': False,
        'source_partition_conserved': True,
        'source_records': len(source), 'reference_records': len(test), 'test_records': len(test),
        'unique_test_sentences': len(test_sentences), 'selected_source_records': len(selected),
        'excluded_source_records': len(removed), 'excluded_shared_clause_records': 0,
        'remaining_whole_sentence_overlap': len(overlap),
        'remaining_whole_sentence_overlap_records': sum(normalized(row[0]) in test_sentences for row in selected),
        'remaining_shared_clause_overlap': len(retained_clauses & (test_sentences | test_clauses)),
        'unique_training_sentences': len(retained_sentences),
        'retained_duplicate_sentence_records': len(selected) - len(retained_sentences),
    }
    if policy == CURRENT_POLICY:
        assert not overlap
        result['excluded_test_sentence_records'] = len(removed)
    else:
        assert len(removed) == len(test)
        assert Counter(map(record_key, selected)) + Counter(map(record_key, test)) == Counter(map(record_key, source))
        result['excluded_test_record_count'] = len(removed)
        result['record_multiset_conserved'] = True
    return result
