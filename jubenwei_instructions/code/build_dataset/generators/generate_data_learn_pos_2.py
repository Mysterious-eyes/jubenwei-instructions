"""Task algorithm from the project; file I/O is supplied by the build runner."""
from generation_paths import SOURCE_FILE, OUTPUT_DIR
import json
import xml.etree.ElementTree as ET
from jubenwei_utils import tag2language
from generate_data_single_core_1 import extract_elements_by_tag, get_all_text_from_xml
generated_data = []

def traverse_tree(element, meta_data_xml, sentence):
    """
    递归地遍历XML元素树，并打印每个元素的标签名和文本内容。
    
    :param element: 当前处理的XML元素
    """
    if element.text and element.text.strip():
        instruction = f'判断“{element.text.strip()}”在句子“{sentence}”中的词性以及对应的句本位标签。'
        input = ''
        output = f'“{element.text.strip()}”是{tag2language[element.tag]}，对应的句本位标签是“{element.tag}”。'
        generated_data.append({'instruction': instruction, 'input': input, 'output': output})
    else:
        print(f"标签: {element.tag}, 内容: ''")
    for child in element:
        traverse_tree(child, meta_data_xml, sentence)
with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
    loaded_data = json.load(f)
for meta_data in loaded_data:
    meta_data_xml = meta_data[1]
    xj_results = extract_elements_by_tag(meta_data_xml, 'xj')
    for xj_xml in xj_results:
        cur_xj = ''.join(get_all_text_from_xml('<ju>' + xj_xml + '</ju>'))
        root = ET.fromstring('<ju>' + xj_xml + '</ju>')
        traverse_tree(root, '<ju>' + xj_xml + '</ju>', cur_xj)
with open(OUTPUT_DIR / 'learn_pos_2.json', 'w', encoding='utf-8') as f:
    json.dump(generated_data, f, ensure_ascii=False, indent=4)
