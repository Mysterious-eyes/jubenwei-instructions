"""Task algorithm from the project; file I/O is supplied by the build runner."""
from generation_paths import SOURCE_FILE, OUTPUT_DIR
import json
import xml.etree.ElementTree as ET
from jubenwei_utils import dongtaici2language
from generate_data_single_core_1 import extract_elements_by_tag, get_all_text_from_xml

def get_mod_tag(xml_string):
    root = ET.fromstring(xml_string)
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
            result.append((key, current_values, tag_name, mod_value))
    return result
generated_data = []
with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
    loaded_data = json.load(f)
for meta_data in loaded_data:
    meta_data_xml = meta_data[1]
    xj_results = extract_elements_by_tag(meta_data_xml, 'xj')
    for xj_xml in xj_results:
        result = get_mod_tag(xj_xml)
        cur_xj = ''.join(get_all_text_from_xml('<ju>' + xj_xml + '</ju>'))
        for temp in result:
            temp_str_result = temp[0] + '（' + temp[2] + ':' + temp[3] + '）'
            temp_cixing_result = '“' + ''.join(('”、“' if c in ['…', '↗', '→', '←', '｜', '‖', '·', '-'] else c for c in temp[3])) + '”'
            temp_extract_structures_tags = '、'.join(['“' + c + '”' for c in temp[3] if c in ['…', '↗', '→', '←', '｜', '‖', '·', '-']])
            temp_extract_structures_language = '、'.join(['“' + dongtaici2language[c] + '”' for c in temp[3] if c in ['…', '↗', '→', '←', '｜', '‖', '·', '-']])
            instruction = f'分析句子“{cur_xj}”中动态词“{temp[0]}”的词法结构。'
            input = ''
            output = f'<think>首先，将“{temp[0]}”拆分为若干词素，不要求拆分到最小的单位，以基础词库收录的词项为界，拆分结果为{temp[1]}。其次，对拆分出的每个词素标记词类和音节数，标记结果为{temp_cixing_result}。最后，标记词素和词素之间的词法结构关系以及动态词的整体词类。“{temp[0]}”涉及的词法结构关系为{temp_extract_structures_language}，对应的标签为{temp_extract_structures_tags}，“{temp[0]}”的整体词性为“{temp[2]}”。</think>{temp_str_result}'
            generated_data.append({'instruction': instruction, 'input': input, 'output': output})
with open(OUTPUT_DIR / 'dongtaici_2.json', 'w', encoding='utf-8') as f:
    json.dump(generated_data, f, ensure_ascii=False, indent=4)
