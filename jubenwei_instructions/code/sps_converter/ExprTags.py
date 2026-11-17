from .comp_type import CompType
class ExprTags:
    """句法符号"""
    Default = "×"
    # --句法--
    Syn_Sbj = "║"   # U+2551
    Syn_Obj = "│"    # U+2502
    Syn_Att_L = "﹙"
    Syn_Att_R = "﹚"
    Syn_Adv_L = "﹝"
    Syn_Adv_R = "﹞"
    Syn_Cmp_L = "﹤"
    Syn_Cmp_R = "﹥"
    Syn_Ind_L = "〖"
    Syn_Ind_R = "〗"

    Syn_FF = "□"
    Syn_PP = "∧"
    Syn_CC_L = "⠉"     # U+2808
    Syn_CC_R = "⠁"    # U+2801#
    Syn_CC_Uni_L = "⠒"     # U+2812
    Syn_CC_Uni_R = "⠂"    # U+2802
    Syn_CC_Uni1_L = "⣀"    # U+28C0
    Syn_CC_Uni1_R = "⠁"    # U+2801
    Syn_CC_Coo_L = "⠤"    # U+2824
    Syn_CC_Coo_R = "⠄"    #U+2804
    Syn_CC_Coo1_L = "⣀"     # U+28C0
    Syn_CC_Coo1_R = "⡀"     # U+2840
    Syn_CC_App_L = "≔"
    Syn_CC_App_R = "≕"
    Syn_CC_PVT = "⫽"
    Syn_CC_SER = "／"
    Syn_CC_SYN = "∶"
    Syn_UU_L = "▷"
    Syn_UU_R = "◁"
    Syn_UN_L = "△"
    Syn_UN_R = "▲"
    Syn_UV_L = "▽"
    Syn_UV_R = "▼"

    Syn_Lift_L = "﹛"
    Syn_Lift_R = "﹜"
    Syn_Lift_M = "§"

    Syn_All = Syn_Sbj + Syn_Obj + Syn_Att_L + Syn_Att_R + Syn_Adv_L + \
        Syn_Adv_R + Syn_Cmp_L + Syn_Cmp_R + Syn_Ind_L + Syn_Ind_R + Syn_FF + Syn_PP + \
        Syn_CC_L + Syn_CC_R + Syn_CC_Uni_L + Syn_CC_Uni_R + Syn_CC_Coo_L + Syn_CC_Coo_R + \
        Syn_CC_App_L + Syn_CC_App_R + Syn_CC_PVT + Syn_CC_SER + Syn_CC_SYN + Syn_UU_L + \
        Syn_UU_R + Syn_UN_L + Syn_UN_R + Syn_UV_L + Syn_UV_R + Syn_Lift_L + Syn_Lift_R + Syn_Lift_M

    Syn_No_UU = Syn_Sbj + Syn_Obj + Syn_Att_L + Syn_Att_R + Syn_Adv_L + Syn_Adv_R + \
        Syn_Cmp_L + Syn_Cmp_R + Syn_Ind_L + Syn_Ind_R + Syn_FF + Syn_PP + Syn_CC_L + \
        Syn_CC_R + Syn_CC_Uni_L + Syn_CC_Uni_R + Syn_CC_Coo_L + Syn_CC_Coo_R + \
        Syn_CC_App_L + Syn_CC_App_R + Syn_CC_PVT + Syn_CC_SER + Syn_CC_SYN + Syn_UN_L + \
        Syn_UN_R + Syn_UV_L + Syn_UV_R + Syn_Lift_L + Syn_Lift_R + Syn_Lift_M

        # <summary>
        # 排除方、介、非角上助词
        # </summary>
    Syn_No_Vir1 = Syn_Sbj + Syn_Obj + Syn_Att_L + Syn_Att_R + Syn_Adv_L + Syn_Adv_R + \
        Syn_Cmp_L + Syn_Cmp_R + Syn_Ind_L + Syn_Ind_R + Syn_CC_L + Syn_CC_R + \
        Syn_CC_Uni_L + Syn_CC_Uni_R + Syn_CC_Coo_L + Syn_CC_Coo_R + Syn_CC_App_L + \
        Syn_CC_App_R + Syn_CC_PVT + Syn_CC_SER + Syn_CC_SYN + Syn_UU_L + Syn_UU_R + \
        Syn_Lift_L + Syn_Lift_R + Syn_Lift_M
#
    Syn_Additives_L = Syn_Att_L + Syn_Adv_L + Syn_Cmp_L + Syn_Ind_L # 附加成分左括号
    Syn_Additives_R = Syn_Att_R + Syn_Adv_R + Syn_Cmp_R + Syn_Ind_R # 附加成分右括号
    Syn_Brakets_L = Syn_Additives_L + Syn_Lift_L # 所有左括号
    Syn_Brakets_R = Syn_Additives_R + Syn_Lift_R # 所有右括号
    # Syn_PrdLayMark = ExprTags.Syn_Sbj + ExprTags.Syn_Obj + ExprTags.Syn_Adv_L +
    # ExprTags.Syn_Adv_R + ExprTags.Syn_Cmp_L + ExprTags.Syn_Cmp_R + ExprTags.Syn_CC_PVT +
    # ExprTags.Syn_CC_SER + ExprTags.Syn_CC_SYN + ExprTags.Syn_CC_Uni_L + ExprTags.Syn_CC_Uni_R;
    Syn_PrdLayMark = Syn_Sbj + Syn_Obj + Syn_Adv_L + Syn_Adv_R + Syn_Cmp_L + Syn_Cmp_R + \
        Syn_CC_PVT + Syn_CC_SER + Syn_CC_SYN + Syn_CC_Uni_L + Syn_CC_Uni_R

        # <summary>
        # 进一步分析符号
        # </summary>
    Syn_SegMore = Syn_Sbj + Syn_Obj + Syn_CC_PVT + Syn_CC_SER + Syn_CC_SYN + Syn_CC_Uni_L + \
        Syn_CC_Uni_R + Syn_CC_Coo_L + Syn_CC_Coo_R + Syn_CC_App_L + Syn_CC_App_R

        # <summary>
        # NP结构中的虚词
        # </summary>
    Syn_NP_Vir = Syn_PP + Syn_FF + Syn_UN_L + Syn_UN_R

        #--词法--
    Lex_BL = "…"
    Lex_DZ = "↗"
    Lex_ZZ = "→"
    Lex_SB = "←"
    Lex_DB = "｜"  # U+FF5C
    Lex_ZW = "‖"   # U+2016
    Lex_QT = "-"
    Lex_CD = "·"
    Lex_FC = "◇"

    #Lex_QT特殊符号，需放首位
    Lex_ALL = Lex_QT + Lex_BL + Lex_DZ + Lex_ZZ + Lex_SB + Lex_DB + Lex_ZW + Lex_CD + Lex_FC

    Tag_Pair = {
        Syn_Att_L : Syn_Att_R,
        Syn_Adv_L : Syn_Adv_R,
        Syn_Cmp_L : Syn_Cmp_R,
        Syn_Ind_L : Syn_Ind_R,
        Syn_Lift_L : Syn_Lift_R,
        Syn_CC_L : Syn_CC_R,
        Syn_CC_Uni_L : Syn_CC_Uni_R,
        Syn_CC_Coo_L : Syn_CC_Coo_R,
        Syn_CC_App_L : Syn_CC_App_R
    }
    # def ExprTags(self):
    #     self.Tag_Pair[self.Syn_Att_L]=self.Syn_Att_R
    #     self.Tag_Pair[self.Syn_Adv_L]=self.Syn_Adv_R
    #     self.Tag_Pair[self.Syn_Cmp_L]=self.Syn_Cmp_R
    #     self.Tag_Pair[self.Syn_Ind_L]=self.Syn_Ind_R
    #     self.Tag_Pair[self.Syn_Lift_L]=self.Syn_Lift_R
    #     self.Tag_Pair[self.Syn_CC_L]=self.Syn_CC_R
    #     self.Tag_Pair[self.Syn_CC_Uni_L]=self.Syn_CC_Uni_R
    #     self.Tag_Pair[self.Syn_CC_Coo_L]=self.Syn_CC_Coo_R
    #     self.Tag_Pair[self.Syn_CC_App_L]=self.Syn_CC_App_R
    def Tag2Type(self,tag):
        if tag == self.Syn_Ind_L: 
            return CompType.IND
        elif tag == self.Syn_Att_L: 
            return CompType.ATT
        elif tag == self.Syn_Adv_L: 
            return CompType.ADV
        elif tag == self.Syn_Cmp_L: 
            return CompType.CMP
        elif tag == self.Syn_Lift_L: 
            return CompType._GENERIC

        elif tag == self.Syn_UN_R: 
            return CompType.V_UN
        elif tag == self.Syn_UV_R: 
            return CompType.V_UV
        elif tag == self.Syn_PP: 
            return CompType.V_PP
        return CompType._NULL;
