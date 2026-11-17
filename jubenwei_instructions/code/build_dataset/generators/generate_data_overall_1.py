"""Task algorithm from the project; file I/O is supplied by the build runner."""
from generation_paths import SOURCE_FILE, OUTPUT_DIR
import json
import xml.etree.ElementTree as ET
import re
from jubenwei_utils import jufa_tags
from generate_data_dongtaici_1 import get_mod_tag
from download_tools.self_explain.LLM_tools import get_single_core
from generate_data_single_core_1 import get_all_text_from_xml
from generate_data_fuzaju_1 import extract_cc_with_fun
from jubenwei_utils import lianciwei_fun2language, tag2language, weiyu_tag2language

def get_all_text_from_element(element):
    """
    递归获取元素及其所有子孙节点的文本内容。
    """
    texts = []
    if element.text and element.text.strip():
        texts.append(element.text.strip())
    for child in element:
        texts.append(get_all_text_from_element(child))
        if child.tail and child.tail.strip():
            texts.append(child.tail.strip())
    return ' '.join(texts)

def get_all_texts_by_tag(xml_string, target_tag):
    """
    解析 XML 字符串，找到所有匹配 target_tag 的标签，
    返回它们各自内部的完整文本内容。
    """
    root = ET.fromstring(xml_string)
    results = []
    for elem in root.findall(f'.//{target_tag}'):
        full_text = get_all_text_from_element(elem)
        results.append(full_text)
    return results

def traverse_tree(element):
    """
    递归地遍历XML元素树，并打印每个元素的标签名和文本内容。
    
    :param element: 当前处理的XML元素
    """
    result = []
    if element.text and element.text.strip():
        result.append({element.text.strip(): element.tag})
    else:
        print(f"标签: {element.tag}, 内容: ''")
    for child in element:
        result.extend(traverse_tree(child))
    return result

def get_all_text_recursive(element):
    """
    递归获取元素及其所有子孙节点的文本内容。
    """
    text = element.text.strip() if element.text else ''
    for child in element:
        text += ' ' + get_all_text_recursive(child)
        if child.tail:
            text += ' ' + child.tail.strip()
    return text.strip()

def extract_xml_tag_content(root, target_tag):
    result = []
    for elem in root.iter():
        if elem.tag == target_tag:
            result.append(ET.tostring(elem, encoding='unicode'))
    if not result:
        return f"未找到标签为 '{target_tag}' 的元素。"
    return result

def extract_attribute_values(root, tag_name, attr_name):
    values = []
    tag_texts = []
    for elem in root.iter():
        if elem.tag == tag_name and elem.get(attr_name) is not None:
            values.append(elem.get(attr_name))
            tag_texts.append(get_all_text_from_element(elem))
    if not values:
        return (None, None)
    return (values, tag_texts)
generated_data = []
with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
    loaded_data = json.load(f)
for meta_data in loaded_data:
    meta_data_xml = meta_data[1]
    root = ET.fromstring(meta_data_xml)
    texts = get_all_texts_by_tag(meta_data_xml, 'xj')
    texts_content = '、'.join(['“' + i.replace(' ', '') + '”' for i in texts])
    xj_xmls = extract_xml_tag_content(root, 'xj')
    xj_prompts = []
    for xj_xml, xj_text in zip(xj_xmls, texts):
        xj_text = xj_text.replace(' ', '')
        xj_root = ET.fromstring(xj_xml)
        xj_prompt = f'小句“{xj_text}”的分析过程如下：1. 分词，'
        pos_results = traverse_tree(xj_root)
        xj_prompt += f'得到带有词性的结果{pos_results}。'
        xj_prompt += '2. 分析句中的动态词及其词法结构。'
        dongtai_mods = get_mod_tag(xj_xml)
        dongtai_mods_str = '、'.join(['“' + temp[0] + '（' + temp[1] + ':' + temp[2] + '）' + '”' for temp in dongtai_mods])
        dongtai_mods_candidates = '、'.join(['“' + temp[0] + '”' for temp in dongtai_mods])
        if len(dongtai_mods_candidates) > 0:
            xj_prompt += f'符合动态词定义的单位为{dongtai_mods_str}。'
        else:
            xj_prompt += '但经过分析，句中不包含动态词。'
        xj_prompt += f'3. 检查小句“{xj_text}”是否可拆分为单核结构。'
        single_cores = get_single_core('<ju>' + xj_xml + '</ju>')
        single_cores_text = []
        for single_score in single_cores:
            single_cores_text.append('“' + ''.join(get_all_text_from_xml(single_score['sentence'])) + '”')
        if len(single_cores_text) > 1:
            single_cores_output_text = '、'.join(single_cores_text)
            xj_prompt += f'拆分结果为{single_cores_output_text}。'
        elif len(single_cores_text) == 1:
            xj_prompt += f'当前规则提取到一个单核结构：{single_cores_text[0]}。'
        else:
            xj_prompt += '当前拆分规则未提取到单核结构，不能据此判定该小句本身为单核。'
        xj_prompt += '4. 依次分析小句中单核结构的句法成分。'
        if not single_cores:
            xj_prompt += '当前没有可供逐核分析的提取结果。'
        for single_core_index, single_score in enumerate(single_cores):
            single_core_text = '“' + ''.join(get_all_text_from_xml(single_score['sentence'])) + '”'
            single_core_root = ET.fromstring(single_score['sentence'])
            grammar_results = []
            xj_prompt += f'在单核结构{single_core_text}中，'
            for target_tag in jufa_tags:
                found_element_all = single_core_root.findall(f'.//{target_tag}')
                for found_element in found_element_all:
                    full_text = get_all_text_recursive(found_element)
                    full_text = full_text.replace(' ', '')
                    if full_text != '':
                        grammar_results.append({full_text: target_tag})
            grammar_text_list = []
            for grammar_result in grammar_results:
                for grammar_result_k in grammar_result:
                    grammar_result_v = grammar_result[grammar_result_k]
                    grammar_text_list.append(f'“{grammar_result_k}”是{tag2language[grammar_result_v]}{grammar_result_v}')
            xj_prompt += '；'.join(grammar_text_list)
            if single_core_index == len(single_cores) - 1:
                xj_prompt += '。'
            else:
                xj_prompt += '；'
        xj_prompt += '5. 依次分析小句中单核结构的谓核辖域。'
        if not single_cores:
            xj_prompt += '当前没有可供逐核分析的提取结果。'
        for single_core_index, single_score in enumerate(single_cores):
            single_core_text = '“' + ''.join(get_all_text_from_xml(single_score['sentence'])) + '”'
            single_core_root = ET.fromstring(single_score['sentence'])
            prd_values, prd_texts = extract_attribute_values(single_core_root, 'prd', 'scp')
            if prd_values:
                xj_prompt += f'在单核结构{single_core_text}中，'
                for prd_index, prd_value, prd_text in zip(range(len(prd_values)), prd_values, prd_texts):
                    prd_text = prd_text.replace(' ', '')
                    scp_description = weiyu_tag2language.get(prd_value.upper(), '当前映射表未定义其含义：')
                    xj_prompt += f'“{prd_text}”是谓核，辖域为“{scp_description}{prd_value}”，'
                if single_core_index == len(single_cores) - 1:
                    xj_prompt = xj_prompt[:-1]
                    xj_prompt += '。'
                else:
                    xj_prompt = xj_prompt[:-1]
                    xj_prompt += '；'
            else:
                xj_prompt += f'在单核结构{single_core_text}中没有谓核辖域。'
        xj_prompt += f'6. 判断小句是否属于复杂句式。经过分析，'
        fuza_result = extract_cc_with_fun(xj_xml)
        if len(fuza_result) > 0:
            xj_prompt += '该句包含' + '、'.join([lianciwei_fun2language[i.upper()] for i in fuza_result]) + '句式类型，需要引入' + '、'.join(['“' + i.upper() + '”' for i in fuza_result]) + '的连词位标签。'
        else:
            xj_prompt += '该句不包含复杂句式类型。'
        xj_prompts.append(xj_prompt)
    xj_prompts_overall = ''.join(xj_prompts)
    instruction = f'给出句子“{meta_data[0]}”的句本位标注结果。'
    input = ''
    output = f'<think>首先，对整句进行切分，得到小句：{texts_content}。然后，对每个小句依次进行分析。{xj_prompts_overall}最后，基于上述分析得到每个小句的标注结果，并使用整句标签<ju>连接，得到最终的标注结果。注意，要确保XML中的文本内容和原句完全匹配、XML标签完全配对以及标签的嵌套符合规则。</think>{meta_data[1]}'
    generated_data.append({'instruction': instruction, 'input': input, 'output': output})
with open(OUTPUT_DIR / 'overall_1.json', 'w', encoding='utf-8') as f:
    json.dump(generated_data, f, ensure_ascii=False, indent=4)
