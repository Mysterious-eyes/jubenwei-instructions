"""Task algorithm from the project; file I/O is supplied by the build runner."""
from generation_paths import SOURCE_FILE, OUTPUT_DIR
import json
from jubenwei_utils import tag2language, dongtaici2language, lianciwei_fun2language, weiyu_tag2language
tags_dict = [('XML元素标签', tag2language), ('动态词词法结构关系符', dongtaici2language), ('连词位fun属性值', lianciwei_fun2language), ('谓核scp属性值', weiyu_tag2language)]
meaning_to_tags = {}
for category, mapping in tags_dict:
    for key, meaning in mapping.items():
        meaning_to_tags.setdefault(meaning, []).append((key, category))
generated_data = []
for meaning, tags in meaning_to_tags.items():
    instruction = f'指出在句本位标注体系中表示“{meaning}”含义的标签。'
    if len(tags) == 1:
        output = f'表示“{meaning}”含义的标签是“{tags[0][0]}”。'
    else:
        descriptions = '；'.join((f'“{key}”（{category}）' for key, category in tags))
        output = f'表示“{meaning}”含义的标签有：{descriptions}。'
    generated_data.append({'instruction': instruction, 'input': '', 'output': output})
with open(OUTPUT_DIR / 'learn_tag_2.json', 'w', encoding='utf-8') as f:
    json.dump(generated_data, f, ensure_ascii=False, indent=4)
