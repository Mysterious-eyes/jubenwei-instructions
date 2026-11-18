"""Read saved prediction fields and calculate the manuscript metrics without file writes."""
from pathlib import Path
import xml.etree.ElementTree as ET
from sps_converter import LinearExpr
from metrics import compute_separated_word_F1, compute_pos_F1, compute_dynamic_word_F1, compute_grammar_F1, compute_sentence_structure_info, count_unparsed_num
FIELDS = ('Instruction', 'Reasoning', 'Output', 'Expression')

def read_data_from_txt(filename, n=4, m=2):
    """按字段读取记录，支持多行值；n/m 仅保留调用兼容性，不再按行数切分。"""
    data = []
    entry = None
    field = None
    for line_number, line in enumerate(Path(filename).read_text(encoding='utf-8-sig').splitlines(), 1):
        key = next((name for name in FIELDS if line.startswith(name + ':')), None)
        if key is not None:
            if key == 'Instruction':
                entry = {}
                data.append(entry)
            if entry is None or key in entry:
                raise ValueError(f'{filename}:{line_number}: 字段顺序错误或重复字段 {key}')
            entry[key] = line.split(':', 1)[1]
            field = key
        elif entry is not None and field is not None:
            entry[field] += '\n' + line
        elif line.strip():
            raise ValueError(f'{filename}:{line_number}: 记录必须以 Instruction: 开始')
    for i, entry in enumerate(data, 1):
        missing = set(FIELDS) - set(entry)
        if missing:
            raise ValueError(f'第 {i} 条记录缺少字段：{sorted(missing)}')
        for key in entry:
            entry[key] = entry[key].strip()
        if not entry['Instruction']:
            raise ValueError(f'第 {i} 条指令为空')
    return data

def compute_metric(token_list, gold_xml_list, pred_xml_list, gold_struct_list, pred_struct_list):
    separated_f1 = compute_separated_word_F1(token_list, gold_xml_list, pred_xml_list)
    pos_f1 = compute_pos_F1(token_list, gold_xml_list, pred_xml_list)
    dynamic_f1 = compute_dynamic_word_F1(token_list, gold_xml_list, pred_xml_list)
    grammar_f1 = compute_grammar_F1(gold_xml_list, pred_xml_list, 'text')
    right_num = compute_sentence_structure_info(gold_struct_list, pred_struct_list)
    unparsed_num, unparsed_sent = count_unparsed_num(token_list, pred_xml_list)
    return (separated_f1, pos_f1, dynamic_f1, grammar_f1, right_num, unparsed_num, unparsed_sent)

def evaluate(loaded_data, predictions):
    """校验对应关系，统一生成表达式；只返回结果，不写文件。"""
    if not loaded_data or len(loaded_data) != len(predictions):
        raise ValueError(f'参考/预测数量必须相同且非空：{len(loaded_data)} / {len(predictions)}')
    for i, (gold, prediction) in enumerate(zip(loaded_data, predictions), 1):
        if not isinstance(gold, list) or len(gold) != 2 or not all(isinstance(v, str) for v in gold):
            raise ValueError(f'第 {i} 条参考数据必须为 [原句, XML]')
        if not isinstance(prediction, dict) or not all(isinstance(prediction.get(k), str) for k in FIELDS):
            raise ValueError(f'第 {i} 条预测必须包含四个字符串字段')
        if prediction['Instruction'] != f'给出句子“{gold[0]}”的句本位标注结果。':
            raise ValueError(f'第 {i} 条预测指令与参考原句不对应')
    return evaluate_outputs(loaded_data, [p['Output'] for p in predictions],
                            stored_expressions=[p['Expression'] for p in predictions])


def evaluate_outputs(loaded_data, outputs, *, stored_expressions=None):
    """Score final answer strings in the order of the reference records."""
    if not loaded_data or len(loaded_data) != len(outputs):
        raise ValueError('Reference records and final answers must have the same nonzero length.')
    if stored_expressions is not None and len(stored_expressions) != len(outputs):
        raise ValueError('Expected one stored expression per answer.')
    tokens, gold_xmls, pred_xmls = ([], [], [])
    gold_structs, pred_structs = ([], [])
    text_mismatches, conversion_errors = ([], [])
    converter = LinearExpr()
    stored_expression_mismatches = 0 if stored_expressions is not None else None

    def convert(root, side, row_number):
        try:
            expression = converter.to_linear_expr(root).strip()
            if not expression:
                raise ValueError('结构表达式为空')
            return expression
        except Exception as exc:
            conversion_errors.append((row_number, side, type(exc).__name__, str(exc)))
            return None
    for i, (gold, output) in enumerate(zip(loaded_data, outputs), 1):
        if not isinstance(gold, list) or len(gold) != 2 or (not all((isinstance(v, str) for v in gold))):
            raise ValueError(f'第 {i} 条参考数据必须为 [原句, XML]')
        if not isinstance(output, str):
            raise ValueError(f'Expected a final answer string at record {i}.')
        sentence, gold_xml = gold
        try:
            gold_root = ET.fromstring(gold_xml)
        except ET.ParseError as exc:
            raise ValueError(f'第 {i} 条参考 XML 无法解析：{exc}') from exc
        if ''.join((t.strip() for t in gold_root.itertext())) != sentence:
            raise ValueError(f'第 {i} 条参考 XML 文本与原句不一致')
        tokens.append(sentence)
        gold_xmls.append(gold_xml)
        pred_xmls.append(output)
        gold_structs.append(convert(gold_root, '参考', i))
        try:
            pred_root = ET.fromstring(output)
        except ET.ParseError:
            pred_structs.append(None)
            continue
        pred_text = ''.join((t.strip() for t in pred_root.itertext()))
        if pred_text != sentence:
            text_mismatches.append((i, sentence, pred_text))
        expression = convert(pred_root, '预测', i)
        pred_structs.append(expression)
        if stored_expressions is not None and expression is not None and expression != stored_expressions[i-1].strip():
            stored_expression_mismatches += 1
    scores = compute_metric(tokens, gold_xmls, pred_xmls, gold_structs, pred_structs)
    separated, pos, dynamic, grammar, right, invalid, invalid_sentences = scores
    return {'total': len(tokens), 'invalid': invalid, 'valid': len(tokens) - invalid, 'separated_f1': separated, 'pos_f1': pos, 'dynamic_f1': dynamic, 'grammar_f1': grammar, 'structure_correct': right, 'structure_evaluated': sum((g is not None and p is not None for g, p in zip(gold_structs, pred_structs))), 'gold_conversion_failures': sum((g is None for g in gold_structs)), 'pred_conversion_failures': sum((side == '预测' for _, side, _, _ in conversion_errors)), 'stored_expression_mismatches': stored_expression_mismatches, 'invalid_sentences': invalid_sentences, 'text_mismatches': text_mismatches, 'conversion_errors': conversion_errors}

def percentage(numerator, denominator):
    return f'{numerator / denominator * 100:.2f}%' if denominator else 'N/A（无可评测样本）'
