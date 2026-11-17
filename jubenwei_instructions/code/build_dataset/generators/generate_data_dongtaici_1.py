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
            result.append((key, tag_name, mod_value))
    return result
if __name__ == '__main__':
    generated_data = []
    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    for meta_data in loaded_data:
        meta_data_xml = meta_data[1]
        xj_results = extract_elements_by_tag(meta_data_xml, 'xj')
        for xj_xml in xj_results:
            cur_xj = ''.join(get_all_text_from_xml('<ju>' + xj_xml + '</ju>'))
            result = get_mod_tag(xj_xml)
            if len(result) > 0:
                str_result = '、'.join(['“' + temp[0] + '（' + temp[1] + ':' + temp[2] + '）' + '”' for temp in result])
                candidate_result = '、'.join(['“' + temp[0] + '”' for temp in result])
                instruction = f'分析句子“{cur_xj}”中的动态词。'
                input = ''
                output = f'<think>在句本位体系中，将未收入基础词库，而又不适宜进行句法结构分析的单位统称为“动态词”。句中符合该定义的单位为{candidate_result}。接着，对待分析的动态词进行词法结构分析。注意，动态词结点的mod属性形式需要符合正则表达式：<动态词结构模式>::=<词素信息>[<结构关系符><词素信息>]+，其中<词素信息>::=<词类><词素的音节数>。</think>{str_result}'
            else:
                instruction = f'分析句子“{cur_xj}”中的动态词。'
                input = ''
                output = f'<think>在句本位体系中，将未收入基础词库，而又不适宜进行句法结构分析的单位统称为“动态词”。</think>经过分析，句中不存在符合该定义的单位。'
            generated_data.append({'instruction': instruction, 'input': input, 'output': output})
    with open(OUTPUT_DIR / 'dongtaici_1.json', 'w', encoding='utf-8') as f:
        json.dump(generated_data, f, ensure_ascii=False, indent=4)
