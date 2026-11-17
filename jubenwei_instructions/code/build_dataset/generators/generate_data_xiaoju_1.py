"""Task algorithm from the project; file I/O is supplied by the build runner."""
from generation_paths import SOURCE_FILE, OUTPUT_DIR
import json
import xml.etree.ElementTree as ET

def get_all_xj_children_values(xml_string):
    root = ET.fromstring(xml_string)
    result = []
    for xj in root.findall('.//xj'):
        current_values = []
        for elem in xj.iter():
            if elem is xj:
                continue
            if elem.text and elem.text.strip():
                current_values.append(elem.text.strip())
        result.append(current_values)
    return result
if __name__ == '__main__':
    generated_data = []
    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    for meta_data in loaded_data:
        meta_data_xml = meta_data[1]
        result = get_all_xj_children_values(meta_data_xml)
        str_result = '、'.join(['“' + ''.join(temp) + '”' for temp in result])
        instruction = f'分析句子“{meta_data[0]}”的小句切分结果。'
        input = ''
        output = f'<think>小句是最小的具有表述性和独立性的语法单位。在整句内部切分小句，分号是确定性的标点，除此之外就是逗号标记。但需要注意逗号分隔的不全是小句，句首状语、主语部分和并列成分之后都有可能存在逗号，这些成分不应该被切分为小句。</think>{str_result}'
        generated_data.append({'instruction': instruction, 'input': input, 'output': output})
    with open(OUTPUT_DIR / 'xiaoju_1.json', 'w', encoding='utf-8') as f:
        json.dump(generated_data, f, ensure_ascii=False, indent=4)
