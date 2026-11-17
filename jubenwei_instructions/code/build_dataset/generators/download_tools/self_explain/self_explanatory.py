import xml.etree.ElementTree
import itertools

class SelfExplanatory:

    sentence_dict = {} # 句子字典

    def sortKey(self,w):
        return w['id']

    def get_depth(self,e):
        return e['depth']

    def set_senetnce_dict(self, dict):
        self.sentence_dict = dict

    def strip_w(self, sent):
        """去掉句子首尾标点符号"""
        for s in sent:
            if s.tag == 'w':
                sent.remove(s)
            else:
                break
        for i in range(len(sent)-1,-1,-1):
            if sent[i].tag == 'w' or sent[i].tag == 'uu':
                sent.remove(sent[i])
            else:
                break
        return sent

    # 拆分多核
    def separate(self, elem,parent):
        """拆分多核，返回拆出的第一句和加了开头的剩余部分"""
        fun = elem.attrib['fun'] # 复句类型
        sent1 = xml.etree.ElementTree.Element(parent.tag)
        sent2 = xml.etree.ElementTree.Element(parent.tag)
        if fun == "UNI":
            # 若句2有主语，则不变，若无主语，使用句1主语
            is_after = 0
            first_sbj = None
            for p in parent:
                if p == elem:
                    is_after = 1
                else:
                    if is_after == 0:
                        sent1.append(p)
                        if p.tag == 'sbj':
                            first_sbj = p
                    elif is_after == 1:
                        if first_sbj is not None and p.tag!='sbj':
                            sent2.append(first_sbj)
                            sent2.append(p)
                            first_sbj = None
                        else:
                            sent2.append(p)
                            first_sbj = None
        elif fun == "SER":
            # 句1的主语为句2的主语
            is_after = 0
            first_sbj = None
            for p in parent:
                if p == elem:
                    is_after = 1
                else:
                    if is_after == 0:
                        sent1.append(p)
                        if p.tag == 'sbj':
                            first_sbj = p
                    elif is_after == 1:
                        if first_sbj is not None and p.tag!='sbj':
                            sent2.append(first_sbj)
                            sent2.append(p)
                            first_sbj = None
                        else:
                            sent2.append(p)
                            first_sbj = None
        elif fun == "PVT":
            # 句2主语为句1宾语
            is_after = 0
            first_obj = None
            for p in parent:
                if p == elem:
                    is_after = 1
                else:
                    if is_after == 0:
                        sent1.append(p)
                        if p.tag == 'obj':
                            first_obj = p
                    elif is_after == 1:
                        if first_obj is not None:
                            sbj = xml.etree.ElementTree.fromstring(xml.etree.ElementTree.tostring(first_obj, encoding='unicode'))
                            sbj.tag = 'sbj'
                            sent2.append(sbj)
                            sent2.append(p)
                            first_obj = None
                        else:
                            sent2.append(p)
        if not any(s.tag == 'prd' for s in sent1): # 没有prd则不算一句
            sent1 = []
        else:
            sent1 = self.strip_w(sent1)# 去掉首尾标点符号
        res = [sent1,sent2]
        return res

    def to_single_core(self, elem, depth, result):
        """
            分层拆分，有prd成分才算句子
            elem: 节点
            depth: 当前层数
            result: 存放所有结果的数组
        """
        if elem is None:
            return    
        if len(elem.tag) == 1:       
            return
        sentence = xml.etree.ElementTree.Element(elem.tag)
        for e in elem:
            if e.tag == "cc" and (len(e.attrib)!=0 and (e.attrib['fun']=="UNI" or e.attrib['fun']=="SER" or e.attrib['fun']=="PVT")):
                res = self.separate(e,elem)
                if len(res[0])>1:
                    res[0].tag = 'xj'
                    result.append({"sentence":xml.etree.ElementTree.tostring(res[0], encoding='unicode'),"depth":depth})
                self.to_single_core(res[1],depth,result)
                return
            elif e.tag == 'prd' or e.tag == 'obj' or e.tag == 'cmp' or e.tag == 'uv':
                sentence.append(e)
                is_Uv_start = False
                before = None
                for p in elem:
                    if p == e:
                        break
                    before = p
                if e.tag == 'uv' and (before == None or \
                    before.tag == 'sbj' or before.tag == 'adv' or \
                    before.tag == 'cc' or before.tag == 'uv'):
                    is_Uv_start = True
                if is_Uv_start == False:
                    # e同一层级后面的 首个元素（不等于ind && 不等于adv && 不等于cc && 不包含任何属性）
                    after = None
                    i = 0
                    bun = 0
                    for i in range(len(elem)):
                        if bun == 1:
                            if i < len(elem)-1:
                                if elem[i].tag!='adv' and \
                                    not(elem[i].tag=='cc' and len(elem[i].attrib) == 0):
                                    after = elem[i]
                                    break
                        if elem[i] == e:
                            bun = 1   
                    if after is not None and after.tag == 'ind':
                        if i < len(elem)-1:
                            after = elem[i+1]
                            i+=1
                        else:
                            after = None
                    # 符合上述条件的首个元素 不为空且是sbj或prd
                    if after is not None:
                        if after.tag == 'sbj' or after.tag == 'prd':
                            sentence.tag = 'xj'
                            result.append({"sentence":xml.etree.ElementTree.tostring(sentence, encoding='unicode'),"depth":depth})
                            sentence = xml.etree.ElementTree.Element(elem.tag)               
            else:
                sentence.append(e)
            self.to_single_core(e,depth+1,result)   
        if not any(s.tag=='prd' for s in sentence): # 没有prd则不算一句
            sentence = []
        else:
            sentence = self.strip_w(sentence) # 去掉首尾标点符号
        if len(sentence)>1:
            if len(sentence)==2 and sentence[1].tag=='uu':
                return 
            sentence.tag = 'xj'
            result.append({"sentence":xml.etree.ElementTree.tostring(sentence, encoding='unicode'),"depth":depth})   
        return


    # 排列组合修饰词
    def combine(self, ps_list, result): # 组合
        """排列组合方法"""
        l = len(ps_list)
        while l!=0:
            temp = itertools.combinations(ps_list,l)
            for t in temp:
                result.append(list(t))
            l -= 1

    def permutate(self, elem):
        """
            排列句子中的修饰成分
            输入一个xml格式句子，返回一个列表
        """
        # print(elem.tag)
        ps = []
        i = 0
        pos = [] # 记录固定节点
        for e in elem:
            if e.tag == 'att' or e.tag == 'adv':
                temp = {}
                temp['elem'] = e
                temp['id'] = i
                ps.append(temp)
            else:
                temp = {}
                temp['elem'] = e
                temp['id'] = i
                pos.append(temp)
            i+=1
        if len(ps) == 0:
            return [elem]
        else:
            per_result = [] # att adv 排列组合结果
            self.combine(ps,per_result) # 组合
            per_result.append([]) # 添加没有状语定语的情况
            res = []
            for p in per_result: # 遍历排列组合结果
                res_temp = xml.etree.ElementTree.Element(elem.tag)
                temp = p + pos
                temp.sort(key = self.sortKey)
                if len(temp)>1: # 排除只有一个动词的
                    for t in temp:
                        res_temp.append(t['elem'])
                    res.append(res_temp)
            return res

    # 拆分APP和COO
    def check_branches(self,elem):
        """拆分elem中的同位和并列，返回一个数组，包含多个拆分结果"""
        # print("当前节点：",xml.etree.ElementTree.tostring(elem, encoding='unicode'))
        if len(elem.tag)==1:
            return [elem]
        sentences = [xml.etree.ElementTree.Element(elem.tag)]
        idx = 0
        is_cc = 0
        for e in elem:
            res = self.check_branches(e)
            # print(e,"返回：",res)
            # 处理e分支结果
            if len(res)>1:
                sentlen = len(sentences)
                # print(sentences)
                for j in range(sentlen):
                    temp = xml.etree.ElementTree.fromstring(xml.etree.ElementTree.tostring(sentences[j]))
                    # print("temp: ",temp)
                    sentences[j].append(res[0])
                    for i in range(len(res)-1):
                        # print(xml.etree.ElementTree.fromstring(xml.etree.ElementTree.tostring(temp)))
                        insert = xml.etree.ElementTree.fromstring(xml.etree.ElementTree.tostring(temp))
                        insert.append(res[i+1])
                        sentences.append(insert)
                # print("1",sentences)
                continue

            if e.tag == "cc" and (len(e.attrib)!=0 and (e.attrib['fun']=="APP" or e.attrib['fun']=="COO")):
                is_cc = 1
                idx = len(sentences)
                temp = xml.etree.ElementTree.Element(elem.tag)
                sentences.append(temp)
                # print("2",sentences)
            else:
                if is_cc == 1 and e.tag!='uu': # 当前正在进行分支 只向最后一个句子添加元素
                    sentences[idx].append(e)
                else: # 当前没有分支，向所有句子添加元素
                    for s in sentences:
                        if e.tag == 'uu' and s[len(s)-1].tag == 'un':
                            s.remove(s[len(s)-1])
                        s.append(e)
        return sentences

    
    def check_is_sentence(self, elem):
        """检查elem中是否构成句子成分（有prd）"""
        for e in elem:
            if len(e.tag) == 1:
                return False
            if e.tag in ['att','adv','cmp','ind','uv','pp','ff','un']:
                continue
            if e.tag == 'prd':
                return True
            else:
                res = self.check_is_sentence(e)
                if res:
                    return True
        return False

    def check_is_independence(self,elem):
        """检查句子是否是独词句"""
        for e in elem:
            if len(e.tag) == 1:
                return True
        return False

    # 提取主干
    def extract_trunk(self, elem):
        """
            为单核句子提取主干，去掉定状补独
            主干不构成句子的返回None
            输入一个xml格式句子，返回主干的xml
        """
        if len(elem.tag) == 1:
            return elem
        res = xml.etree.ElementTree.Element(elem.tag)
        for e in elem:
            if e.tag not in ['att','adv','cmp','ind','uv','pp','ff','un']:
            # if e.tag in ['sbj','prd','obj']:
                if e.tag == 'cc':
                    if len(e.attrib)!=0 and (e.attrib['fun'] == 'APP' or e.attrib['fun'] == 'COO'): # 留下APP和COO的标签 方便提取主干后拆分
                        res.append(e)
                    elif len(e.attrib)!=0 and e.attrib['fun'] == 'SYN' and res[len(res)-1].tag == 'prd': # 删除SYN前的prd
                        res.remove(res[len(res)-1])
                else:
                    is_sentence = self.check_is_sentence(e)
                    if is_sentence:
                        temp = xml.etree.ElementTree.Element(e.tag)
                        temp_inner = xml.etree.ElementTree.Element('x')
                        temp_inner.text = 'xj'
                        temp.append(temp_inner)
                        res.append(temp)
                    else:
                        res.append(self.extract_trunk(e))
        if len(res)==1 and res[0].tag == 'prd':
            return None
        return res

    # 去标点
    def remove_w(self,elem):
        if len(elem.tag)==1:
            return elem
        res = xml.etree.ElementTree.Element(elem.tag)
        for e in elem:
            if e.tag!='w':
                res.append(self.remove_w(e))
        return res
        

    # 搭配库
    def extract_matches(self,elem,result):
        """
            提取搭配
            主语或宾语里  定中   <att><x>
            状中		<adv><prd>
            述补		<prd><cmp>
            传入一个xml格式句子和保存最终结果的列表，无返回值
            结果格式 {'match':xxx,type:'x'}
        """
        if len(elem.tag)==1:
            return
        temp = xml.etree.ElementTree.Element('match')
        prd = None
        match_type = 0
        for e in elem:
            self.extract_matches(e,result)
            if match_type == 1:
                if len(e.tag)==1:
                    temp.append(e)
                    if e.tag == 'w':
                        continue
                    branch = self.check_branches(temp) # 检查是否有COO和APP需要拆分
                    if len(branch) == 1:
                        result.append({'match':xml.etree.ElementTree.tostring(self.remove_w(temp), encoding='unicode'),'type':'1'})
                    else:
                        for b in branch:
                            result.append({'match':xml.etree.ElementTree.tostring(self.remove_w(b), encoding='unicode'),'type':'1'})
                match_type = 0
                temp = xml.etree.ElementTree.Element('match') # temp清零

            elif match_type == 2:
                if e.tag == 'prd':
                    temp.append(e) # prd去标点
                    # print("adv:",xml.etree.ElementTree.tostring(temp, encoding='unicode'))
                    result.append({'match':xml.etree.ElementTree.tostring(self.remove_w(temp), encoding='unicode'),'type':'2'})
                match_type = 0
                temp = xml.etree.ElementTree.Element('match') # temp清零

            if prd is not None and e.tag != 'prd' and e.tag != 'cmp': # 不符合述补 放弃当前prd
                prd = None

            if e.tag == 'att':
                match_type = 1
                temp.append(e)
            elif e.tag == 'adv':
                match_type = 2
                temp.append(e)
            elif e.tag == 'prd':
                prd = e
            elif e.tag == 'cmp' and prd is not None:
                temp.append(prd)
                temp.append(e)
                # print("prd:",xml.etree.ElementTree.tostring(temp, encoding='unicode'))
                result.append({'match':xml.etree.ElementTree.tostring(self.remove_w(temp), encoding='unicode'),'type':'3'})
                temp = xml.etree.ElementTree.Element('match') # temp清零
        return


    def save_data(self,db,r,sql=None):
        """
            将结果存入数据库
        """
        if sql is not None and r is not None:
            saveSQL = sql
            db.ping(reconnect=True)
            cursor = db.cursor()
            cursor.execute(saveSQL)
            db.commit()
