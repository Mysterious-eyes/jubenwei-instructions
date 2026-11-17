"""Task algorithm from the project; file I/O is supplied by the build runner."""
from generation_paths import SOURCE_FILE, OUTPUT_DIR
import json
from jubenwei_utils import tag2language, dongtaici2language, lianciwei_fun2language, weiyu_tag2language
tags_dict = [tag2language, dongtaici2language, lianciwei_fun2language, weiyu_tag2language]
tag2language_for_dataset = {}
for d in tags_dict:
    tag2language_for_dataset.update(d)
generated_data = []
for key in tag2language_for_dataset:
    instruction = f'指出标签“{key}”在句本位标注体系中的含义。'
    input = ''
    output = f'标签“{key}”表示“{tag2language_for_dataset[key]}”。'
    generated_data.append({'instruction': instruction, 'input': input, 'output': output})
with open(OUTPUT_DIR / 'learn_tag_1.json', 'w', encoding='utf-8') as f:
    json.dump(generated_data, f, ensure_ascii=False, indent=4)
