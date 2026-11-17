"""Task algorithm from the project; file I/O is supplied by the build runner."""
from generation_paths import SOURCE_FILE, OUTPUT_DIR
import json
import xml.etree.ElementTree as ET
from jubenwei_utils import tag2language
generated_data = []

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
with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
    loaded_data = json.load(f)
for meta_data in loaded_data:
    meta_data_xml = meta_data[1]
    root = ET.fromstring(meta_data_xml)
    separated_words = traverse_xml_in_order(root)
    separated_words_connected = '/'.join(separated_words)
    instruction = f'在进行句本位标注前，对句子“{meta_data[0]}”进行分词，词语之间使用“/”分隔。'
    input = ''
    output = f'{separated_words_connected}'
    generated_data.append({'instruction': instruction, 'input': input, 'output': output})
    a = 1
with open(OUTPUT_DIR / 'learn_separate_1.json', 'w', encoding='utf-8') as f:
    json.dump(generated_data, f, ensure_ascii=False, indent=4)
