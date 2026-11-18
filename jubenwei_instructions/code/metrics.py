"""Paper metric extraction and alignment, with standard BIO entity micro-F1.

The four component metrics return their original F1 score by default.
With return_counts=True they return pooled (TP, FP, FN) from the same extraction
and alignment, for case-level diagnostics or independent metric aggregation.
"""
from collections import Counter
from typing import List
import xml.etree.ElementTree as ET
from bio_f1 import entity_counts, f1_score
def tqdm(iterable, **kwargs):
    return iterable

def label_sequence(labeled_tokens, labeled_reference, task, scheme='BIO'):
    if task not in ['separated_word', 'pos', 'dynamic_word', 'grammar']:
        raise Exception('Unsupported task for computing F1 score!')
    if scheme == 'BIO':
        labeled_results = ['O'] * len(labeled_tokens)
        if task == 'separated_word':
            index = 0
            for meta_refer in labeled_reference:
                if not meta_refer:
                    continue
                preindex = index
                while ''.join(labeled_tokens[index:index + len(meta_refer)]) != meta_refer:
                    index += 1
                    if index >= len(labeled_tokens):
                        break
                if index >= len(labeled_tokens):
                    index = preindex
                    continue
                labeled_results[index] = 'B-word'
                if len(meta_refer) > 1:
                    for i in range(len(meta_refer) - 1):
                        labeled_results[index + i + 1] = 'I-word'
                index += len(meta_refer)
        elif task == 'pos':
            index = 0
            for meta_refer in labeled_reference:
                if not meta_refer[0]:
                    continue
                preindex = index
                while ''.join(labeled_tokens[index:index + len(meta_refer[0])]) != meta_refer[0]:
                    index += 1
                    if index >= len(labeled_tokens):
                        break
                if index >= len(labeled_tokens):
                    index = preindex
                    continue
                labeled_results[index] = 'B-' + meta_refer[1]
                if len(meta_refer[0]) > 1:
                    for i in range(len(meta_refer[0]) - 1):
                        labeled_results[index + i + 1] = 'I-' + meta_refer[1]
                index += len(meta_refer[0])
        elif task == 'dynamic_word':
            index = 0
            for meta_refer in labeled_reference:
                if not meta_refer[0]:
                    continue
                preindex = index
                while ''.join(labeled_tokens[index:index + len(meta_refer[0])]) != meta_refer[0]:
                    index += 1
                    if index >= len(labeled_tokens):
                        break
                if index >= len(labeled_tokens):
                    index = preindex
                    continue
                labeled_results[index] = 'B-' + meta_refer[1] + ':' + meta_refer[2]
                if len(meta_refer[0]) > 1:
                    for i in range(len(meta_refer[0]) - 1):
                        labeled_results[index + i + 1] = 'I-' + meta_refer[1] + ':' + meta_refer[2]
                index += len(meta_refer[0])
        return labeled_results

def compute_separated_word_F1(token_list: List[str], gold_xml_list: List[str], pred_xml_list: List[str],
                              *, return_counts: bool = False) -> float | tuple[int, int, int]:
    """
        计算分词的F1分数。

        Args:
           token_list：词元列表
           gold_xml_list：真实xml的列表
           pred_xml_list：预测xml的列表

        Returns:
            F1分数（0-1）；return_counts=True时返回(TP, FP, FN)。
    """

    def traverse_xml_in_order(element):
        """
        按照先序遍历（深度优先）方式递归访问元素及其子元素。
        返回值：列表，每项是一个字典，包含 tag 和 text（合并后的文本内容）
        """
        result = []
        current_text = (element.text or '').strip()
        if current_text != '':
            result.append(current_text)
        for child in element:
            result.extend(traverse_xml_in_order(child))
        return result
    if len(token_list) != len(gold_xml_list) or len(gold_xml_list) != len(pred_xml_list) or len(token_list) == 0:
        return (0, 0, 0) if return_counts else 0
    gold_sequences, pred_sequences = ([], [])
    for meta_token, meta_gold_xml, meta_pred_xml in tqdm(zip(token_list, gold_xml_list, pred_xml_list), desc='Processing separated word', total=len(token_list)):
        gold_root = ET.fromstring(meta_gold_xml)
        try:
            pred_root = ET.fromstring(meta_pred_xml)
        except ET.ParseError:
            continue
        meta_separated_gold_list = traverse_xml_in_order(gold_root)
        meta_separated_pred_list = traverse_xml_in_order(pred_root)
        meta_token_list = [i for i in meta_token]
        meta_gold_sequence = label_sequence(meta_token_list, meta_separated_gold_list, 'separated_word')
        meta_pred_sequence = label_sequence(meta_token_list, meta_separated_pred_list, 'separated_word')
        gold_sequences.append(meta_gold_sequence)
        pred_sequences.append(meta_pred_sequence)
    if return_counts:
        return entity_counts(gold_sequences, pred_sequences)
    f1 = f1_score(gold_sequences, pred_sequences, zero_division=0) if gold_sequences else 0.0
    return f1

def compute_pos_F1(token_list: List[str], gold_xml_list: List[str], pred_xml_list: List[str],
                   *, return_counts: bool = False) -> float | tuple[int, int, int]:
    """
        计算词性的F1分数。

        Args:
           token_list：词元列表
           gold_xml_list：真实xml的列表
           pred_xml_list：预测xml的列表

        Returns:
            F1分数（0-1）；return_counts=True时返回(TP, FP, FN)。
    """

    def traverse_tree(element):
        """
        递归地遍历XML元素树，并打印每个元素的标签名和文本内容。
        
        :param element: 当前处理的XML元素
        """
        pos_results = []
        if element.text and element.text.strip():
            pos_results.append((element.text.strip(), element.tag))
        for child in element:
            pos_results.extend(traverse_tree(child))
        return pos_results
    if len(token_list) != len(gold_xml_list) or len(gold_xml_list) != len(pred_xml_list) or len(token_list) == 0:
        return (0, 0, 0) if return_counts else 0
    gold_sequences, pred_sequences = ([], [])
    for meta_token, meta_gold_xml, meta_pred_xml in tqdm(zip(token_list, gold_xml_list, pred_xml_list), desc='Processing POS', total=len(token_list)):
        gold_root = ET.fromstring(meta_gold_xml)
        try:
            pred_root = ET.fromstring(meta_pred_xml)
        except ET.ParseError:
            continue
        meta_pos_gold_list = traverse_tree(gold_root)
        meta_pos_pred_list = traverse_tree(pred_root)
        meta_token_list = [i for i in meta_token]
        meta_gold_sequence = label_sequence(meta_token_list, meta_pos_gold_list, 'pos')
        meta_pred_sequence = label_sequence(meta_token_list, meta_pos_pred_list, 'pos')
        gold_sequences.append(meta_gold_sequence)
        pred_sequences.append(meta_pred_sequence)
    if return_counts:
        return entity_counts(gold_sequences, pred_sequences)
    f1 = f1_score(gold_sequences, pred_sequences, zero_division=0) if gold_sequences else 0.0
    return f1

def compute_dynamic_word_F1(token_list: List[str], gold_xml_list: List[str], pred_xml_list: List[str],
                            *, return_counts: bool = False) -> float | tuple[int, int, int]:
    """
        计算动态词的F1分数。

        Args:
           token_list：词元列表
           gold_xml_list：真实xml的列表
           pred_xml_list：预测xml的列表

        Returns:
            F1分数（0-1）；return_counts=True时返回(TP, FP, FN)。
    """

    def get_mod_tag(root):
        result = []
        for elem in root.iter():
            if 'mod' in elem.attrib:
                current_values = []
                for child in elem.iter():
                    if child is elem:
                        continue
                    if child.tag == 'w':
                        continue
                    if child.text and child.text.strip():
                        current_values.append(child.text.strip())
                key = ''.join(current_values)
                tag_name = elem.tag
                mod_value = elem.attrib['mod']
                result.append((key, tag_name, mod_value))
        return result
    if len(token_list) != len(gold_xml_list) or len(gold_xml_list) != len(pred_xml_list) or len(token_list) == 0:
        return (0, 0, 0) if return_counts else 0
    gold_sequences, pred_sequences = ([], [])
    for meta_token, meta_gold_xml, meta_pred_xml in tqdm(zip(token_list, gold_xml_list, pred_xml_list), desc='Processing dynamic word', total=len(token_list)):
        gold_root = ET.fromstring(meta_gold_xml)
        try:
            pred_root = ET.fromstring(meta_pred_xml)
        except ET.ParseError:
            continue
        meta_dynamic_gold_list = get_mod_tag(gold_root)
        meta_dynamic_pred_list = get_mod_tag(pred_root)
        meta_token_list = [i for i in meta_token]
        meta_gold_sequence = label_sequence(meta_token_list, meta_dynamic_gold_list, 'dynamic_word')
        meta_pred_sequence = label_sequence(meta_token_list, meta_dynamic_pred_list, 'dynamic_word')
        gold_sequences.append(meta_gold_sequence)
        pred_sequences.append(meta_pred_sequence)
    if return_counts:
        return entity_counts(gold_sequences, pred_sequences)
    f1 = f1_score(gold_sequences, pred_sequences, zero_division=0) if gold_sequences else 0.0
    return f1

def compute_grammar_F1(gold_xml_list: List[str], pred_xml_list: List[str], data_type: str,
                       *, return_counts: bool = False) -> float | tuple[int, int, int]:
    """
        计算句法成分的F1分数，保留重复成分的计数。

        Args:
           gold_xml_list：真实xml的列表
           pred_xml_list：预测xml的列表
           data_type：句法信息表示类型，两种，span和text，前者是(开始位置, 结束位置, 成分类型)，后者是(文本片段, 成分类型)

        Returns:
            F1分数（0-1）；return_counts=True时返回(TP, FP, FN)。
    """

    def extract_text_with_positions(root, target_tags, data_type):
        spans = []
        position = 0

        def traverse(elem):
            nonlocal position
            start = position
            parts = [(elem.text or '').strip()]
            position += len(parts[0])
            for child in elem:
                parts.append(traverse(child))
                tail = (child.tail or '').strip()
                parts.append(tail)
                position += len(tail)
            text = ''.join(parts)
            if elem.tag in target_tags and text:
                if data_type == 'span':
                    spans.append((start, position, elem.tag))
                else:
                    spans.append((text, elem.tag))
            return text
        traverse(root)
        return spans
    if data_type not in {'text', 'span'}:
        raise ValueError(f'Unsupported grammar data_type: {data_type}')
    if len(gold_xml_list) != len(pred_xml_list) or len(gold_xml_list) == 0:
        return (0, 0, 0) if return_counts else 0
    jufa_tags = ['sbj', 'prd', 'obj', 'att', 'adv', 'cmp', 'ind', 'pp', 'cc', 'uu', 'un', 'uv', 'ff']
    tp = 0
    fp = 0
    fn = 0
    for meta_gold_xml, meta_pred_xml in tqdm(zip(gold_xml_list, pred_xml_list), desc='Processing grammar', total=len(gold_xml_list)):
        gold_root = ET.fromstring(meta_gold_xml)
        try:
            pred_root = ET.fromstring(meta_pred_xml)
        except ET.ParseError:
            continue
        meta_gold_spans = extract_text_with_positions(gold_root, jufa_tags, data_type)
        meta_pred_spans = extract_text_with_positions(pred_root, jufa_tags, data_type)
        gold_set = Counter(meta_gold_spans)
        pred_set = Counter(meta_pred_spans)
        tp += sum((gold_set & pred_set).values())
        fp += sum((pred_set - gold_set).values())
        fn += sum((gold_set - pred_set).values())
    if return_counts:
        return tp, fp, fn
    precision = tp / (tp + fp) if tp + fp > 0 else 0
    recall = tp / (tp + fn) if tp + fn > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0
    return f1

def compute_sentence_structure_info(gold_list: List[str], pred_list: List[str]) -> int:
    """
        计算句式结构分析结果的准确率和无法解析的比例。

        Args:
           gold_list：真实句式结构的列表
           pred_list：预测句式结构的列表

        Returns:
            预测完全正确的数量
    """
    if len(gold_list) != len(pred_list):
        raise ValueError('Gold/predicted structure counts differ')
    right = 0
    for meta_gold, meta_pred in tqdm(zip(gold_list, pred_list), desc='Processing sentence structure', total=len(gold_list)):
        if meta_gold is not None and meta_pred is not None and (meta_gold == meta_pred):
            right += 1
    return right

def count_unparsed_num(token_list, pred_xml_list: List[str]) -> int:
    """
        统计无法解析的数量。

        Args:
           pred_xml_list：预测xml的列表

        Returns:
            数量（整数）
    """
    unparsed_num = 0
    unparsed_sent = []
    for meta_token_list, meta_pred_xml in zip(token_list, pred_xml_list):
        try:
            pred_root = ET.fromstring(meta_pred_xml)
        except ET.ParseError:
            unparsed_num += 1
            unparsed_sent.append(''.join(meta_token_list))
    return (unparsed_num, unparsed_sent)
