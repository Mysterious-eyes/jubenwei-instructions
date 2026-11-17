"""Task algorithm from the project; file I/O is supplied by the build runner."""
from generation_paths import SOURCE_FILE, OUTPUT_DIR
import xml.etree.ElementTree as ET
import json
from download_tools.self_explain.LLM_tools import get_single_core
from generate_data_xiaoju_1 import get_all_xj_children_values

def get_all_text_from_xml(xml_string):
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as e:
        return f'XML 解析错误: {e}'
    texts = []

    def extract_text(element):
        if element.text and element.text.strip():
            texts.append(element.text.strip())
        for child in element:
            extract_text(child)
        if element.tail and element.tail.strip():
            texts.append(element.tail.strip())
    extract_text(root)
    return texts

def extract_elements_by_tag(xml_string, target_tag):
    """
    从 XML 字符串中提取所有指定标签的元素。

    Args:
        xml_string (str): 输入的 XML 字符串。
        target_tag (str): 要提取的标签名称。

    Returns:
        str: 包含所有匹配元素的 XML 字符串。如果没有找到匹配的元素，则返回空字符串。
    """
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as e:
        raise ValueError(f'无效的 XML 字符串: {e}')
    found_elements = root.iter(target_tag)
    results = []
    found_elements = list(root.iter(target_tag))
    if len(found_elements) == 0:
        return results
    for elem in found_elements:
        copied_elem = ET.tostring(elem, encoding='unicode')
        results.append(copied_elem)
    return results
if __name__ == '__main__':
    generated_data = []
    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    for meta_data in loaded_data:
        meta_data_xml = meta_data[1]
        xj_results = extract_elements_by_tag(meta_data_xml, 'xj')
        for xj_xml in xj_results:
            cur_xj = ''.join(get_all_text_from_xml('<ju>' + xj_xml + '</ju>'))
            single_cores = get_single_core('<ju>' + xj_xml + '</ju>')
            single_cores_text = []
            for single_score in single_cores:
                single_cores_text.append('“' + ''.join(get_all_text_from_xml(single_score['sentence'])) + '”')
            if len(single_cores_text) > 1:
                output_text = '拆分结果为' + '、'.join(single_cores_text) + '。'
            elif len(single_cores_text) == 1:
                output_text = '当前规则提取到一个单核结构：' + single_cores_text[0] + '。'
            else:
                output_text = '当前拆分规则未提取到单核结构，不能据此判定该句子本身为单核。'
            instruction = f'检查句子“{cur_xj}”是否可拆分为单核结构。'
            input = ''
            output = f'{output_text}'
            generated_data.append({'instruction': instruction, 'input': input, 'output': output})
    with open(OUTPUT_DIR / 'single_core_1.json', 'w', encoding='utf-8') as f:
        json.dump(generated_data, f, ensure_ascii=False, indent=4)
