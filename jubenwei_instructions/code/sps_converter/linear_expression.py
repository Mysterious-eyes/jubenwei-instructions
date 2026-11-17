"""XML-to-linear-expression scoring converter; default representation used in the paper."""
import re
from .ExprTags import ExprTags
from .XmlTags import XmlTags
from .XmlExtention import XmlExtention
ExprTags = ExprTags()
XmlTags = XmlTags()
XmlExtention = XmlExtention()

class LinearExpr:
    REX_MOD_SYMBOLS = re.compile('[^a-z\\d]')
    REX_SYMBOL_ALL = re.compile('[' + ExprTags.Syn_All + ExprTags.Default + ']|/[a-z](?:\\d{3}[ABC]?)?')
    XJ_EXPR_SEP = '\n'

    def to_linear_expr(self, elem, with_pos_sen=0, split_dyn_word=None, parent=None):
        if elem is None:
            return ''
        expr = ''
        length = len(elem.tag)
        if length == 1:
            if len(elem) != 0 and split_dyn_word is not None and (split_dyn_word == '' or elem.tag in split_dyn_word):
                mods = None
                if re.match(self.REX_MOD_SYMBOLS, list(elem.attrib.values())[0]):
                    mods = elem.attrib['mod']
                dyn_word_expr = '['
                idx = 0
                for e in elem:
                    dyn_word_expr += self.to_linear_expr(e, with_pos_sen, split_dyn_word, elem)
                    if e.tag != XmlTags.W_BiaoDian and idx < len(mods):
                        dyn_word_expr += mods[idx]
                        idx += 1
                dyn_word_expr += ']'
                if with_pos_sen > 0:
                    dyn_word_expr += elem.tag
                return dyn_word_expr
            if with_pos_sen == 0:
                if elem.text is None or elem.text == '':
                    if split_dyn_word is None and 'mod' in elem.attrib:
                        expt = ''
                        for e in elem:
                            expt += ''.join(e.itertext())
                        return self.REX_SYMBOL_ALL.sub('?', expt)
                    else:
                        return ExprTags.Default
                else:
                    return self.REX_SYMBOL_ALL.sub('?', elem.text)
            if elem.text is None or elem.text == '':
                word = ExprTags.Default
            else:
                self.REX_SYMBOL_ALL.sub('?', elem.text)
            word += '/' + elem.tag
            if with_pos_sen == 2 and XmlTags.A_Sen in elem.attrib:
                word += elem.attrib[XmlTags.A_Sen]
            return word
        if length == 2:
            if elem.tag == XmlTags.C_FullSent:
                temp = []
                for e in elem:
                    temp.append(self.to_linear_expr(e, with_pos_sen, split_dyn_word, elem))
                return self.XJ_EXPR_SEP.join(temp)
            elif elem.tag == XmlTags.C_Sent:
                temp = []
                for e in elem:
                    temp.append(self.to_linear_expr(e, with_pos_sen, split_dyn_word, elem))
                return ''.join(temp)
            if len(elem) != 0:
                temp = []
                for e in elem:
                    temp.append(self.to_linear_expr(e, with_pos_sen, split_dyn_word, elem))
                expr = ''.join(temp)
            if (expr is None or expr == '') and elem.tag != XmlTags.C_CC:
                if with_pos_sen > 0:
                    expr = ExprTags.Default + '/x '
                else:
                    expr = ExprTags.Default
            if elem.tag == XmlTags.C_FF:
                expr = ExprTags.Syn_FF + expr
            elif elem.tag == XmlTags.C_PP:
                expr += ExprTags.Syn_PP
            elif elem.tag == XmlTags.C_CC:
                if len(elem.attrib) > 0:
                    fun = elem.attrib[XmlTags.A_Fun]
                    if fun == XmlTags.V_Fun_PVT:
                        expr = ExprTags.Syn_CC_PVT
                    elif fun == XmlTags.V_Fun_SER:
                        expr = ExprTags.Syn_CC_SER
                    elif fun == XmlTags.V_Fun_SYN:
                        expr = ExprTags.Syn_CC_SYN
                    elif fun == XmlTags.V_Fun_APP:
                        expr = ExprTags.Syn_CC_App_L + expr + ExprTags.Syn_CC_App_R
                    elif fun == XmlTags.V_Fun_COO:
                        expr = ExprTags.Syn_CC_Coo_L + expr + ExprTags.Syn_CC_Coo_R
                    elif fun == XmlTags.V_Fun_COO1:
                        expr = ExprTags.Syn_CC_Coo1_L + expr + ExprTags.Syn_CC_Coo1_R
                    elif fun == XmlTags.V_Fun_UNI1:
                        expr = ExprTags.Syn_CC_Uni1_L + expr + ExprTags.Syn_CC_Uni1_R
                    else:
                        expr = ExprTags.Syn_CC_Uni_L + expr + ExprTags.Syn_CC_Uni_R
                else:
                    expr = ExprTags.Syn_CC_L + expr + ExprTags.Syn_CC_R
            elif elem.tag == XmlTags.C_UU:
                if parent.tag == XmlTags.C_Bu:
                    expr += ExprTags.Syn_UU_R
                else:
                    expr = ExprTags.Syn_UU_L + expr
            elif elem.tag == XmlTags.C_UN:
                nexts = []
                after = 0
                for p in parent:
                    if after == 1:
                        nexts.append(p)
                    if p == elem:
                        after = 1
                if len(nexts) > 0 and (nexts[0].tag == XmlTags.C_Ding or len(nexts[0].tag) == 1 or XmlExtention.is_prd_peered_compt(nexts[0])):
                    expr += ExprTags.Syn_UN_R
                else:
                    expr = ExprTags.Syn_UN_L + expr
            elif elem.tag == XmlTags.C_UV:
                prev = None
                next = None
                is_after = 0
                for p in parent:
                    if is_after == 1:
                        next = p
                        break
                    if p == elem:
                        is_after = 1
                    if is_after == 0:
                        prev = p
                if (prev == None or prev.tag != XmlTags.C_Wei) and next != None and (next.tag == XmlTags.C_Wei or next.tag == XmlTags.C_Zhuang):
                    expr += ExprTags.Syn_UV_R
                else:
                    expr = ExprTags.Syn_UV_L + expr
        else:
            if elem.tag == 'jbw':
                temp = []
                for e in elem:
                    temp.append(self.to_linear_expr(e, with_pos_sen, split_dyn_word, elem))
                expr = self.XJ_EXPR_SEP.join(temp)
            else:
                temp = []
                for e in elem:
                    temp.append(self.to_linear_expr(e, with_pos_sen, split_dyn_word, elem))
                expr = ''.join(temp)
            if elem.tag == XmlTags.C_Zhu:
                expr += ExprTags.Syn_Sbj
            elif elem.tag == XmlTags.C_Bin:
                expr = ExprTags.Syn_Obj + expr
            elif elem.tag == XmlTags.C_Ding:
                expr = ExprTags.Syn_Att_L + expr + ExprTags.Syn_Att_R
            elif elem.tag == XmlTags.C_Zhuang:
                expr = ExprTags.Syn_Adv_L + expr + ExprTags.Syn_Adv_R
            elif elem.tag == XmlTags.C_Bu:
                expr = ExprTags.Syn_Cmp_L + expr + ExprTags.Syn_Cmp_R
            elif elem.tag == XmlTags.C_Ind:
                expr = ExprTags.Syn_Ind_L + expr + ExprTags.Syn_Ind_R
        if XmlExtention.is_compt_in_lifter(elem, parent):
            befs = []
            afts = []
            bun = 0
            for p in parent:
                if p == elem:
                    bun = 1
                    continue
                if p.tag == XmlTags.C_Ind or p.tag == XmlTags.C_UU:
                    continue
                if bun == 0:
                    befs.append(p)
                elif bun == 1:
                    afts.append(p)
            if len(befs) == 0:
                b_last = None
            else:
                b_last = befs[len(befs) - 1]
            if len(befs) == 0 or b_last.tag == XmlTags.C_Ding or b_last.tag == XmlTags.C_PP or (b_last.tag == XmlTags.C_UN) or (b_last.tag == XmlTags.C_CC and len(b_last.attrib) > 0 and (list(b_last.attrib.values())[0] == XmlTags.V_Fun_COO or list(b_last.attrib.values())[0] == XmlTags.V_Fun_APP)):
                expr = ExprTags.Syn_Lift_L + expr
            if len(afts) == 0 or afts[0].tag == XmlTags.C_FF or afts[0].tag == XmlTags.C_UN or (afts[0].tag == XmlTags.C_PP) or (afts[0].tag == XmlTags.C_CC and len(afts[0].attrib) > 0 and (list(afts[0].attrib.values())[0] == XmlTags.V_Fun_COO or list(afts[0].attrib.values())[0] == XmlTags.V_Fun_APP)):
                expr += ExprTags.Syn_Lift_R
        if elem.tag == XmlTags.C_Wei or elem.tag == XmlTags.C_Bin or elem.tag == XmlTags.C_Bu or (elem.tag == XmlTags.C_UV):
            is_Uv_start = False
            before = None
            for p in parent:
                if p == elem:
                    break
                before = p
            if elem.tag == XmlTags.C_UV and (before == None or before.tag == XmlTags.C_Zhu or before.tag == XmlTags.C_Zhuang or (before.tag == XmlTags.C_CC) or (before.tag == XmlTags.C_UV)):
                is_Uv_start = True
            if is_Uv_start == False:
                after = None
                temp = []
                i = 0
                bun = 0
                for i in range(len(parent)):
                    if bun == 1:
                        if i < len(parent) - 1:
                            if parent[i].tag != XmlTags.C_Zhuang and (not (parent[i].tag == XmlTags.C_CC and len(parent[i].attrib) == 0)):
                                after = parent[i]
                                break
                    if parent[i] == elem:
                        bun = 1
                if after is not None and after.tag == XmlTags.C_Ind:
                    if i < len(parent) - 1:
                        after = parent[i + 1]
                        i += 1
                    else:
                        after = None
                if after is not None:
                    if after.tag == XmlTags.C_Zhu or after.tag == XmlTags.C_Wei:
                        expr += ExprTags.Syn_Lift_M
        return expr
