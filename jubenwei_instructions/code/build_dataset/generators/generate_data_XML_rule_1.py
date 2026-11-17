"""Task algorithm from the project; file I/O is supplied by the build runner."""
from generation_paths import SOURCE_FILE, OUTPUT_DIR
import xml.etree.ElementTree as ET
import random
import json
from jubenwei_utils import jufa_tags
import re
random.seed(0)

def swap_random_text_siblings(root):
    """
    随机选择一对具有非空文本内容的兄弟节点并交换它们的位置。
    如果交换成功，返回这两个节点的文本内容。
    如果交换失败（没有找到符合条件的兄弟节点对），返回两个空字符串。

    Args:
        root (ET.Element): XML 根节点。

    Returns:
        tuple: (text1: str, text2: str) 交换的两个节点的文本内容，或 ("", "")。
    """
    all_elements = list(root.iter())[1:]
    if len(all_elements) < 2:
        return ('', '')
    random.shuffle(all_elements)
    for elem in all_elements:
        parent = find_parent(root, elem)
        if parent is not None:
            children = list(parent)
            text_children_with_index = []
            for idx, child in enumerate(children):
                if child.text is not None and child.text.strip():
                    text_children_with_index.append((idx, child))
            if len(text_children_with_index) >= 2:
                idx1, idx2 = random.sample(range(len(text_children_with_index)), 2)
                pos1, node1 = text_children_with_index[idx1]
                pos2, node2 = text_children_with_index[idx2]
                text1 = node1.text
                text2 = node2.text
                if text1 != text2:
                    parent[pos1], parent[pos2] = (node2, node1)
                    print(f"已交换兄弟节点: '{node1.tag}' (文本: '{text1}') 和 '{node2.tag}' (文本: '{text2}') (在父节点 '{parent.tag}' 下)")
                    return (text1, text2)
    return ('', '')

def delete_random_child(root):
    """
    随机删除一个非根节点、非根节点直接子节点、且后代包含文本的句法成分。
    如果删除成功，返回被删除子树的完整文本。
    如果删除失败（没有符合条件的节点），返回空字符串。

    Args:
        root (ET.Element): XML 根节点。

    Returns:
        str: 被删除节点的文本内容，或空字符串。
    """
    deletable_elements_with_text = []
    for elem in root.iter():
        if elem == root:
            continue
        if elem.tag not in jufa_tags:
            continue
        parent = find_parent(root, elem)
        if parent is not None and parent != root and get_all_text_from_element(elem).strip():
            deletable_elements_with_text.append((elem, parent))
    if not deletable_elements_with_text:
        return ''
    node_to_delete, parent_of_deleted = random.choice(deletable_elements_with_text)
    deleted_text = get_all_text_from_element(node_to_delete)
    parent_of_deleted.remove(node_to_delete)
    return deleted_text

def find_parent(root, node):
    """
    找到给定节点的父节点。
    
    Args:
        root (ET.Element): XML 根节点。
        node (ET.Element): 要查找父节点的元素。
    
    Returns:
        ET.Element or None: 父节点，如果未找到则返回 None。
    """
    for parent in root.iter():
        if node in parent:
            return parent
    return None

def random_copy_xml_node(root):
    """
    随机选择XML中的一个节点并复制它
    """
    all_nodes = []

    def collect_nodes(parent):
        if parent.tag in jufa_tags:
            node_text = get_all_text_from_element(parent)
            if node_text != '':
                all_nodes.append((node_text, parent))
        for child in parent:
            collect_nodes(child)
    collect_nodes(root)
    node_text = ''
    if len(all_nodes) > 0:
        node_text, node_to_copy = random.choice(all_nodes)
        copied_node = ET.fromstring(ET.tostring(node_to_copy))
        parent = find_parent(root, node_to_copy)
        index = list(parent).index(node_to_copy) + 1
        parent.insert(index, copied_node)
    return node_text

def get_all_text_from_element(element):
    """
    递归获取元素及其所有子孙节点的文本内容。
    """
    texts = []
    if element.text and element.text.strip():
        texts.append(element.text.strip())
    for child in element:
        texts.append(get_all_text_from_element(child))
        if child.tail and child.tail.strip():
            texts.append(child.tail.strip())
    return ''.join(texts)

def create_mismatched_xml(original_xml_str):
    """只删除非自闭合标签，并验证 XML 确实无法解析。"""
    ET.fromstring(original_xml_str)
    candidates = [match for match in re.finditer('<(/?)(\\w+)[^>]*>', original_xml_str) if not match.group(0).rstrip().endswith('/>')]
    random.shuffle(candidates)
    for match in candidates:
        corrupted = original_xml_str[:match.start()] + original_xml_str[match.end():]
        try:
            ET.fromstring(corrupted)
        except ET.ParseError:
            return (corrupted, match.group(2))
    raise ValueError('没有可破坏的非自闭合标签')

def swap_parent_child_tags(root):
    """
    随机交换一个父节点标签和其子节点标签
    返回: (交换后的XML字符串, (父标签名, 子标签名))
    """
    parent_child_pairs = []

    def find_parent_child_pairs(parent):
        for child in parent:
            if parent is root and parent.tag == 'ju' and (child.tag == 'xj'):
                parent_child_pairs.append((parent, child))
            find_parent_child_pairs(child)
    find_parent_child_pairs(root)
    if not parent_child_pairs:
        raise ValueError('XML中没有父子节点关系可以交换')
    selected_pair = random.choice(parent_child_pairs)
    parent_elem, child_elem = selected_pair
    parent_tag = parent_elem.tag
    child_tag = child_elem.tag
    parent_elem.tag = child_tag
    child_elem.tag = parent_tag
    return (parent_tag, child_tag)
generated_data = []
with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
    loaded_data = json.load(f)
for meta_data in loaded_data:
    meta_data_xml = meta_data[1]
    root = ET.fromstring(meta_data_xml)
    selected_number = random.choice([0, 1, 2, 3, 4, 5])
    success_index = True
    if selected_number == 1:
        swap_text_1, swap_text_2 = swap_random_text_siblings(root)
        if swap_text_1 == '' and swap_text_2 == '':
            success_index = False
    elif selected_number == 2:
        deleted_text = delete_random_child(root)
        if deleted_text == '':
            success_index = False
    elif selected_number == 3:
        copied_text = random_copy_xml_node(root)
        if copied_text == '':
            success_index = False
    elif selected_number == 4:
        try:
            corrupted_xml, destroyed_tag_name = create_mismatched_xml(meta_data_xml)
        except ValueError:
            success_index = False
    elif selected_number == 5:
        try:
            swap_tag_1, swap_tag_2 = swap_parent_child_tags(root)
        except ValueError:
            success_index = False
    if not success_index:
        continue
    meta_data_xml = ET.tostring(root, encoding='unicode')
    meta_data_text = get_all_text_from_element(root)
    meta_data_text = meta_data_text.replace(' ', '')
    if selected_number == 4:
        meta_data_xml = corrupted_xml
    instruction = f'分析句子“{meta_data[0]}”句本位标注结果“{meta_data_xml}”的文本内容是否和原句完全匹配、XML标签是否配对以及标签的嵌套是否符合规则。'
    input = ''
    if selected_number == 0:
        output = f'<think>对标注结果的文本内容进行抽取，得到“{meta_data_text}”。该结果和原始句子一致。此外，XML仍可正常解析，标签保持配对。</think>文本内容和原句完全匹配、XML标签是配对的、标签的嵌套也符合规则。'
    if selected_number == 1:
        output = f'<think>对标注结果的文本内容进行抽取，得到“{meta_data_text}”。片段“{swap_text_1}”和“{swap_text_2}”和原句的顺序不同。此外，XML仍可正常解析，标签保持配对。</think>XML仍可正常解析，标签保持配对。但是出现文本片段顺序不同的情况，应恢复原句的顺序，将标注结果调整为“{meta_data[1]}”。'
    if selected_number == 2:
        output = f'<think>对标注结果的文本内容进行抽取，得到“{meta_data_text}”。原句中的片段“{deleted_text}”丢失了。此外，XML仍可正常解析，标签保持配对。</think>XML仍可正常解析，标签保持配对。但是出现文本片段丢失的情况，应补充相关片段，将标注结果调整为“{meta_data[1]}”。'
    if selected_number == 3:
        output = f'<think>对标注结果的文本内容进行抽取，得到“{meta_data_text}”。原句中的片段“{copied_text}”重复了。此外，XML仍可正常解析，标签保持配对。</think>XML仍可正常解析，标签保持配对。但是出现文本片段重复的情况，应去掉重复部分，将标注结果调整为“{meta_data[1]}”。'
    if selected_number == 4:
        output = f'<think>对标注结果的文本内容进行抽取，得到“{meta_data_text}”。该结果和原始句子一致。此外，对标签的配对情况进行检测，发现标签{destroyed_tag_name}不配对，无法构成完整的 XML 树，不能据此确认嵌套合法。</think>文本内容和原句完全匹配，但出现标签不配对的情况，应补充相关标签，将标注结果调整为“{meta_data[1]}”。'
    if selected_number == 5:
        output = f'<think>对标注结果的文本内容进行抽取，得到“{meta_data_text}”。该结果和原始句子一致。此外，对标签的嵌套情况进行检测，发现标签{swap_tag_1}和{swap_tag_2}嵌套层次不对，但是标签都是配对的。</think>文本内容和原句完全匹配、标签的也都是配对的。但是出现标签嵌套层次不对的情况，应改变相关标签的嵌套关系，将标注结果调整为“{meta_data[1]}”。'
    generated_data.append({'instruction': instruction, 'input': input, 'output': output})
with open(OUTPUT_DIR / 'XML_rule_1.json', 'w', encoding='utf-8') as f:
    json.dump(generated_data, f, ensure_ascii=False, indent=4)
