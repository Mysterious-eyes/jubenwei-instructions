from .comp_type import CompType
from .ExprTags import ExprTags

class XmlTags:
    """句子成分标记"""
    A_Sen = "sen"
    A_Mod = "mod"
    A_Dict = "dct"
    A_Id = "id" # 小句id
    A_Expand = "expand" # 段落中句子标记
    A_Auto = "auto" # 需要自动分析标记
    A_Ignore = "ignore" # 非句标记

    A_Ptt = "ptt"
    V_PTT_SVO = "SVO"
    V_PTT_VO = "VO"
    V_PTT_H = "H"
    V_PTT_VOS = "VOS"
    V_PTT_SOV = "SOV"

    #prd
    A_Scp = "scp"
    V_SCP_V = "V"
    V_SCP_VO = "VO"
    V_SCP_VC = "VC"
    V_SCP_VOO = "VOO"
    V_SCP_VOC = "VOC"
    V_SCP_VCO = "VCO"
    V_SCP_VOOC = "VOOC"
    V_SCP_VOCC = "VOCC"

    A_Inv = "inv" # 倒装标记

    # 句间关系
    A_Indent = "upt"
    V_Indent_S = "s"
    V_Indent_E = "e"

    A_Coh = "coh" #衔接关系cohesion
    V_Coh_ALL = "↡"
    V_Coh_END = "⫰" #独立句（带主语的可充当独立语的句子）
    V_Coh_END_Up = "⫯"
    V_Coh_PRE = "⋮" #划线位置前面所有成分
    V_Coh_ONE = "⇣"  #单个成分
    V_Coh_ONE_Up = "⇡"

    A_Rel = "rel" # 句间关系
    A_Sub = "sub" # 句间主从指向关系

    A_Fun = "fun"
    V_Fun_APP = "APP"
    V_Fun_COO = "COO"
    V_Fun_COO1 = "coo" #定语间连词
    V_Fun_UNI1 = "uni" #状语间连词
    V_Fun_UNI = "UNI" #联合
    V_Fun_SER = "SER" #连动
    V_Fun_PVT = "PVT" #兼语
    V_Fun_SYN = "SYN" #助动
    V_NP_Funs = [V_Fun_APP, V_Fun_COO]

    #--成分--
    C_Para = "para"  # 段落标记
    C_FullSent = "ju"
    C_Sent = "xj"

    C_Zhu = "sbj"
    C_Wei = "prd"
    C_Bin = "obj"
    C_Ding = "att"
    C_Zhuang = "adv"
    C_Bu = "cmp"
    C_Ind = "ind"

    C_PP = "pp"
    C_CC = "cc"
    C_UN = "un"
    C_UV = "uv"
    C_UU = "uu"
    C_FF = "ff"

    O_Temp = "temp"
    O_Copy = "xcopy"
    O_Full = "full"
    O_Pre = "pre"
    O_Next = "next"
    O_Sptsbj = "sptsbj"
    O_Sptobj = "sptobj"

    #--词类--
    W_Ming = "n"
    W_Ming_ShiJian = "t"
    W_Ming_Fangwei = "f"
    W_Shu = "m"
    W_Liang = "q"
    W_Dai = "r"

    W_Dong = "v"
    W_XingRong = "a"
    W_Fu = "d"

    W_Jie = "p"
    W_Lian = "c"
    W_Zhu = "u"

    W_Tan = "e"
    W_NiSheng = "o"
    W_BiaoDian = "w"
    W_QueSheng = "x"

    W_All = [ W_Ming, W_Ming_ShiJian, W_Ming_Fangwei, W_Shu, W_Liang, W_Dai,
    W_Dong, W_XingRong, W_Fu,W_Jie, W_Lian, W_Zhu, W_Tan, W_NiSheng, W_BiaoDian, W_QueSheng]


    def Type2Tag(self,type):
        if type==CompType.SENT: 
            return self.C_Sent
        elif type==CompType.SBJ: 
            return self.C_Zhu
        elif type==CompType.PRD: 
            return self.C_Wei
        elif type==CompType.OBJ: 
            return self.C_Bin
        elif type==CompType.ATT: 
            return self.C_Ding
        elif type==CompType.ADV: 
            return self.C_Zhuang
        elif type==CompType.CMP: 
            return self.C_Bu
        elif type==CompType.IND: 
            return self.C_Ind
        elif type==CompType._GENERIC: 
            return self.O_Temp

        elif type==CompType.V_PP: 
            return self.C_PP
        elif type==CompType.V_FF: 
            return self.C_FF

        elif type==CompType.V_CC: 
            return self.C_CC
        elif type==CompType.V_CC_COO: 
            return self.C_CC
        elif type==CompType.V_CC_APP: 
            return self.C_CC
        elif type==CompType.V_CC_UNI: 
            return self.C_CC

        elif type==CompType.V_UN: 
            return self.C_UN
        elif type==CompType.V_UV: 
            return self.C_UV
        elif type==CompType.V_UU: 
            return self.C_UU



    def Tag2Type(self,tag,attr):
        tag = tag.lower()
        if tag==self.C_Sent:
            return CompType.SENT
        elif tag==self.C_FullSent:
            return CompType.SENT
        elif tag==self.C_Zhu:
            return CompType.SBJ
        elif tag==self.C_Wei:
            return CompType.PRD
        elif tag==self.C_Bin:
            return CompType.OBJ
        elif tag==self.C_Ding:
            return CompType.ATT
        elif tag==self.C_Zhuang:
            return CompType.ADV
        elif tag==self.C_Bu:
            return CompType.CMP
        elif tag==self.C_Ind:
            return CompType.IND

        elif tag==self.C_PP:
            return CompType.V_PP
        elif tag==self.C_FF:
            return CompType.V_FF

        elif tag==self.C_CC and self.V_Fun_COO.lower()==attr.lower():
            return CompType.V_CC_COO
        elif tag==self.C_CC and self.V_Fun_APP.lower()==attr.lower():
            return CompType.V_CC_APP
        elif tag==self.C_CC and self.V_Fun_UNI.lower()==attr.lower():
            return CompType.V_CC_UNI
        elif tag==self.C_CC:
            return CompType.V_CC

        elif tag==self.C_UN:
            return CompType.V_UN
        elif tag==self.C_UV:
            return CompType.V_UV
        elif tag==self.C_UU:
            return CompType.V_UU

        return CompType._NULL
    
    def ExprTag2Tag(self,tag):
        if tag == ExprTags.Syn_CC_Coo_L: 
            return self.V_Fun_COO
        elif tag == ExprTags.Syn_CC_Coo_R: 
            return self.V_Fun_COO
        elif tag == ExprTags.Syn_CC_App_L: 
            return self.V_Fun_APP
        elif tag == ExprTags.Syn_CC_App_R: 
            return self.V_Fun_APP
        elif tag == ExprTags.Syn_CC_Uni_R: 
            return self.V_Fun_UNI
        elif tag == ExprTags.Syn_CC_SYN: 
            return self.V_Fun_SYN
        elif tag == ExprTags.Syn_CC_SER: 
            return self.V_Fun_SER
        elif tag == ExprTags.Syn_CC_PVT: 
            return self.V_Fun_PVT

        elif tag == ExprTags.Syn_UV_R: 
            return self.W_Zhu
        elif tag == ExprTags.Syn_UN_R: 
            return self.W_Zhu
        else:
            return ""

    def ExprTag2CTag(self,tag):
        if tag==ExprTags.Syn_UU_R: 
            return self.C_UU
        elif tag==ExprTags.Syn_UN_R: 
            return self.C_UN
        elif tag==ExprTags.Syn_PP: 
            return self.C_PP
        else:
            return ""

    

