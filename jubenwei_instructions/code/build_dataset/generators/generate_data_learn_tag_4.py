"""Task algorithm from the project; file I/O is supplied by the build runner."""
from generation_paths import SOURCE_FILE, OUTPUT_DIR
from jubenwei_utils import tag2language, jufa_tags
import xml.etree.ElementTree as ET
import json
from generate_data_single_core_1 import extract_elements_by_tag, get_all_text_from_xml

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
generated_data = []
with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
    loaded_data = json.load(f)
for meta_data in loaded_data:
    meta_data_xml = meta_data[1]
    xj_results = extract_elements_by_tag(meta_data_xml, 'xj')
    for xj_xml in xj_results:
        root = ET.fromstring('<ju>' + xj_xml + '</ju>')
        for target_tag in jufa_tags:
            for found_element in root.findall(f'.//{target_tag}'):
                full_text = get_all_text_recursive(found_element)
                full_text = full_text.replace(' ', '')
                if full_text != '':
                    print('合并后的文本：', full_text)
                    instruction = f"指出“{full_text}”在句本位标注结果“{'<ju>' + xj_xml + '</ju>'}”中的句法成分。"
                    input = ''
                    output = f'<think>首先，正确提取“{full_text}”对应的句法标签，通过递归查找，确定“{full_text}”的句法标签是“{target_tag}”。其次，“{target_tag}”表示{tag2language[target_tag]}。所以，“{full_text}”的句法成分为{tag2language[target_tag]}。</think>{tag2language[target_tag]}。'
                    generated_data.append({'instruction': instruction, 'input': input, 'output': output})
with open(OUTPUT_DIR / 'learn_tag_4.json', 'w', encoding='utf-8') as f:
    json.dump(generated_data, f, ensure_ascii=False, indent=4)
