"""Task algorithm from the project; file I/O is supplied by the build runner."""
from generation_paths import SOURCE_FILE, OUTPUT_DIR
import json
import xml.etree.ElementTree as ET
from jubenwei_utils import weiyu_tag2language
from generate_data_single_core_1 import extract_elements_by_tag, get_all_text_from_xml

def extract_prd_with_scp(xml_string):
    root = ET.fromstring(xml_string)
    results = []
    for prd in root.findall('.//prd'):
        if 'scp' in prd.attrib:
            scp_value = prd.get('scp')
            children_texts = []
            for child in prd.iter():
                if child != prd and child.text and child.text.strip():
                    children_texts.append(child.text.strip())
            results.append((''.join(tuple(children_texts)), scp_value))
    return results
generated_data = []
with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
    loaded_data = json.load(f)
for meta_data in loaded_data:
    meta_data_xml = meta_data[1]
    xj_results = extract_elements_by_tag(meta_data_xml, 'xj')
    for xj_xml in xj_results:
        result = extract_prd_with_scp(xj_xml)
        cur_xj = ''.join(get_all_text_from_xml('<ju>' + xj_xml + '</ju>'))
        for meta_result in result:
            instruction = f'分析句子“{cur_xj}”中谓核“{meta_result[0]}”在句本位标注结果中应该使用的辖域标签。'
            input = ''
            scp_description = weiyu_tag2language.get(meta_result[1].upper(), '当前映射表未定义其含义，保留原始辖域标签')
            output = f'<think>“{meta_result[0]}”在“{cur_xj}”中的辖域为“{scp_description}”</think>{meta_result[1]}'
            generated_data.append({'instruction': instruction, 'input': input, 'output': output})
with open(OUTPUT_DIR / 'weiciyu_1.json', 'w', encoding='utf-8') as f:
    json.dump(generated_data, f, ensure_ascii=False, indent=4)
