"""Task algorithm from the project; file I/O is supplied by the build runner."""
from generation_paths import SOURCE_FILE, OUTPUT_DIR
import json
import xml.etree.ElementTree as ET
from jubenwei_utils import lianciwei_fun2language
from generate_data_single_core_1 import extract_elements_by_tag, get_all_text_from_xml

def extract_cc_with_fun(xml_string):
    root = ET.fromstring(xml_string)
    result = []
    for cc in root.findall('.//cc'):
        if 'fun' in cc.attrib:
            fun_value = cc.get('fun')
            result.append(fun_value)
    return result
if __name__ == '__main__':
    generated_data = []
    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    for meta_data in loaded_data:
        meta_data_xml = meta_data[1]
        xj_results = extract_elements_by_tag(meta_data_xml, 'xj')
        for xj_xml in xj_results:
            result = extract_cc_with_fun(xj_xml)
            cur_xj = ''.join(get_all_text_from_xml('<ju>' + xj_xml + '</ju>'))
            if len(result) > 0:
                str_result = '、'.join([lianciwei_fun2language[i.upper()] for i in result])
            else:
                str_result = '该句子不包含复杂句式类型。'
            instruction = f'分析句子“{cur_xj}”中的复杂句式类型。'
            input = ''
            output = f'{str_result}'
            generated_data.append({'instruction': instruction, 'input': input, 'output': output})
    with open(OUTPUT_DIR / 'fuzaju_1.json', 'w', encoding='utf-8') as f:
        json.dump(generated_data, f, ensure_ascii=False, indent=4)
