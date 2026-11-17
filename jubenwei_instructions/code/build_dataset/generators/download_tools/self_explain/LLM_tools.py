import xml.etree.ElementTree
from .self_explanatory import SelfExplanatory

def get_single_core(xml_string):
    '''
    将所有句子拆分成单核
    '''
    single_core = [] # {'sentence':xxx,'depth':0}
    sentence_dict={} 
    explain = SelfExplanatory()
    root = xml.etree.ElementTree.fromstring(xml_string)
    # 语料中同时存在 uni / UNI；拆分算法使用大写 fun 值。
    # 这里只修改局部解析树，不修改作为最终答案的原始 XML。
    for cc in root.iter('cc'):
        if cc.get('fun'):
            cc.set('fun', cc.get('fun').upper())
    for xj in root:
            temp = []
            explain.to_single_core(xj,0,temp)
            temp.sort(key = explain.get_depth)
            for t in temp:
                if t['sentence'] not in sentence_dict.keys():
                    sentence_dict[t['sentence']] = '0'
                    single_core.append(t)
    
    return single_core
