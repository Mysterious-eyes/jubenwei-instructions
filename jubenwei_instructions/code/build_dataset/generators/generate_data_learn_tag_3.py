"""Task algorithm from the project; file I/O is supplied by the build runner."""
from generation_paths import SOURCE_FILE, OUTPUT_DIR
import json
import xml.etree.ElementTree as ET
from jubenwei_utils import tag2language
from generate_data_single_core_1 import extract_elements_by_tag, get_all_text_from_xml
generated_data = []

def traverse_tree(element, meta_data_xml):
    """
    递归地遍历XML元素树，并打印每个元素的标签名和文本内容。
    
    :param element: 当前处理的XML元素
    """
    if element.text and element.text.strip():
        instruction = f'指出“{element.text.strip()}”在句本位标注结果“{meta_data_xml}”中的词性。'
        input = ''
        output = f'<think>首先，正确提取“{element.text.strip()}”对应的词性标签，通过查找，确定“{element.text.strip()}”的词性标签是“{element.tag}”。其次，“{element.tag}”表示{tag2language[element.tag]}。所以，“{element.text.strip()}”的词性为{tag2language[element.tag]}。</think>{tag2language[element.tag]}。'
        generated_data.append({'instruction': instruction, 'input': input, 'output': output})
    else:
        print(f"标签: {element.tag}, 内容: ''")
    for child in element:
        traverse_tree(child, meta_data_xml)
with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
    loaded_data = json.load(f)
for meta_data in loaded_data:
    meta_data_xml = meta_data[1]
    xj_results = extract_elements_by_tag(meta_data_xml, 'xj')
    for xj_xml in xj_results:
        root = ET.fromstring('<ju>' + xj_xml + '</ju>')
        traverse_tree(root, '<ju>' + xj_xml + '</ju>')
with open(OUTPUT_DIR / 'learn_tag_3.json', 'w', encoding='utf-8') as f:
    json.dump(generated_data, f, ensure_ascii=False, indent=4)
