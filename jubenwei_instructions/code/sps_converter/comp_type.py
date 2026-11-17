class CompType:
    _NULL = -1,

    # 小句
    SENT = 0,
    #独立成分
    IND = 1,
    ASSIST = 2,

    #TextCompt
    #主语
    SBJ = 100,
    #宾语
    OBJ = 101,
    #定语
    ATT = 102,

    #谓语
    PRD = 103,
    # 状语
    ADV = 104,
    #补语
    CMP = 105,
    # 待定成分
    _GENERIC = 106,

    #V_UU = 200,
    # NP助词
    V_UN = 200,
    # VP助词
    V_UV = 201,
    # 定状补角上的助词
    V_UU = 202,
    #V_UU_D,
    #V_UU_I,
    #V_UU_E,
    #V_UU_V,

    # 连词（句间）
    V_CC = 203,
    # 连词（并列）
    V_CC_COO = 204,
    # 同位
    V_CC_APP = 205,
    # 连词（联合）
    V_CC_UNI = 206,
    # 方位词
    V_FF = 207,
    # 介词
    V_PP = 208

    OBJ_UN = 237

    OBJ_FF = 239