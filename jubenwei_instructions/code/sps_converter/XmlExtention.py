from .XmlTags import XmlTags

class XmlExtention:
    def is_main_compt(self, elem, include_CcUv = False):
        return elem.tag == XmlTags.C_Zhu or elem.tag == XmlTags.C_Wei or elem.tag == XmlTags.C_Bin \
            or include_CcUv and (elem.tag == XmlTags.C_CC and not(len(elem.attrib)>0 and(\
            list(elem.attrib.values())[0] == XmlTags.V_Fun_COO or \
            list(elem.attrib.values())[0] == XmlTags.V_Fun_APP or \
            list(elem.attrib.values())[0] == XmlTags.V_Fun_COO1)) or elem.tag == XmlTags.C_UV)

    def is_prd_peered_compt(self,elem, include_Ind = False):
        return self.is_main_compt(elem, True) or elem.tag == XmlTags.C_Zhuang or \
            elem.tag == XmlTags.C_Bu or include_Ind and elem.tag == XmlTags.C_Ind

    def is_compt_in_lifter(self,elem,parent):
        return self.is_prd_peered_compt(elem) and (parent.tag == XmlTags.C_Wei or self.is_np_core(parent))

    def is_np_core(self, elem):
        return elem.tag == XmlTags.C_Zhu or elem.tag == XmlTags.C_Bin or \
            any(e.tag == XmlTags.C_Ding or e.tag == XmlTags.C_PP or e.tag == XmlTags.C_FF or \
            e.tag == XmlTags.C_UN or e.tag == XmlTags.C_CC and len(e.attrib)>0 and (\
            list(e.attrib.values())[0] == XmlTags.V_Fun_COO or \
            list(e.attrib.values())[0] == XmlTags.V_Fun_APP) for e in elem)
