"""Draw the seven bilingual manuscript figures from fixed aggregate inputs.

Dependencies: Matplotlib, NumPy and Pillow. SVG retains text; PDF embeds fonts.
No source sentences, model answers or remote services are used.
"""
from pathlib import Path
import json
import math
import os
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle, FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
WIDTH = 3779
DPI = 600
LOGICAL_WIDTH = 1600
HEIGHTS = {1: 2881, 2: 2669, 3: 2173, 4: 2692, 5: 2314, 6: 2551, 7: 2834}
P = {"ink": "#1f2328", "muted": "#6b747d", "body": "#4a535c",
     "blue": "#2a66a3", "orange": "#d0782a", "gray": "#9aa2aa",
     "border": "#8c949c", "grid": "#e3e6ea", "light_blue": "#e8f0f8",
     "deep_blue": "#c9daec", "light_gray": "#f1f2f4", "light_orange": "#fbefe2"}
SCALE = 72 * (WIDTH / DPI) / LOGICAL_WIDTH
matplotlib.rcParams.update({"svg.fonttype": "none", "pdf.fonttype": 42,
                            "ps.fonttype": 42, "axes.unicode_minus": False,
                            "savefig.facecolor": "white",
                            "svg.hashsalt": "jubenwei-manuscript-figures"})


def load_data():
    return json.loads((ROOT / "data/figure_data.json").read_text(encoding="utf-8-sig"))


def select_font(lang):
    """Use an explicit font override, then locally installed common fonts."""
    override = os.environ.get(f"FIGURE_FONT_{lang.upper()}")
    if override:
        p = Path(override)
        if not p.is_file():
            raise FileNotFoundError(f"Font does not exist: {p}")
        fm.fontManager.addfont(str(p))
        return fm.FontProperties(fname=str(p)).get_name()
    candidates = (["Arial", "Liberation Sans", "DejaVu Sans"] if lang == "en"
                  else ["Microsoft YaHei", "Noto Sans CJK SC", "Noto Sans SC", "SimHei"])
    system = {f.name for f in fm.fontManager.ttflist}
    # Explicitly register common Windows font faces if a cached font list predates them.
    for name in ["arial.ttf", "arialbd.ttf", "msyh.ttc", "msyhbd.ttc"]:
        path = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / name
        if path.is_file():
            fm.fontManager.addfont(str(path))
            system.add(fm.FontProperties(fname=str(path)).get_name())
    for family in candidates:
        if family in system:
            return family
    raise RuntimeError("Install Noto Sans CJK SC or set FIGURE_FONT_ZH to a CJK font file.")


def choose(lang, en, zh):
    return zh if lang == "zh" else en


class Canvas:
    def __init__(self, number, lang):
        self.number, self.lang = number, lang
        self.height = HEIGHTS[number] / WIDTH * LOGICAL_WIDTH
        self.font = select_font(lang)
        # The raw SPS code U+FF5C needs a CJK fallback even in English labels.
        self.families = list(dict.fromkeys([self.font, select_font("zh"), "DejaVu Sans"]))
        self.fig = plt.figure(figsize=(WIDTH / DPI, HEIGHTS[number] / DPI), dpi=DPI)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set(xlim=(0, LOGICAL_WIDTH), ylim=(self.height, 0))
        self.ax.set_axis_off()
        self.texts = []

    def t(self, x, y, value, size=24, bold=False, color=None, align="left", italic=False):
        text = self.ax.text(x, y, value, ha=align, va="center",
                            fontsize=size * SCALE, fontfamily=self.families,
                            fontweight="bold" if bold else "normal",
                            fontstyle="italic" if italic else "normal",
                            color=color or P["ink"], linespacing=1.22, clip_on=False)
        self.texts.append(text)
        return text

    def rect(self, x, y, w, h, fill="white", stroke=None, lw=2, radius=0, dash=False):
        kw = dict(facecolor=fill, edgecolor=stroke or "none", linewidth=lw * SCALE,
                  linestyle=(0, (3, 2)) if dash else "solid", clip_on=False, zorder=2)
        if radius:
            obj = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={radius}", **kw)
        else:
            obj = Rectangle((x, y), w, h, **kw)
        self.ax.add_patch(obj)

    def line(self, points, color=None, lw=2, arrow=False):
        if len(points) > 2:
            self.line(points[:-1], color, lw)
            points = points[-2:]
        color = color or P["body"]
        if arrow:
            self.ax.add_patch(FancyArrowPatch(points[0], points[-1], arrowstyle="-|>",
                mutation_scale=11 * SCALE, linewidth=lw * SCALE, color=color,
                shrinkA=0, shrinkB=0, clip_on=False, zorder=2.5))
        else:
            self.ax.plot([p[0] for p in points], [p[1] for p in points],
                         color=color, lw=lw * SCALE, solid_capstyle="butt", clip_on=False)

    def title(self, letter, en, zh, x, y=33):
        self.t(x, y, letter, 28, True)
        self.t(x + 42, y, choose(self.lang, en, zh), 26, True)

    def card(self, x, y, w, h, title, lines, fill="white", border=None, divider=True,
             title_size=26, body_size=23):
        self.rect(x, y, w, h, fill, border or P["border"], radius=7)
        self.t(x + w/2, y + 36, title, title_size, True, align="center")
        if divider:
            self.line([(x+28, y+64), (x+w-28, y+64)], P["grid"], 1.5)
        if lines:
            start = y + 95 if divider else y + (h+45)/2
            for i, value in enumerate(lines):
                self.t(x+w/2, start+i*34, value, body_size, color=P["body"], align="center")

    def save(self, folder, formats=("png", "svg", "pdf")):
        folder.mkdir(parents=True, exist_ok=True)
        self.fig.canvas.draw()
        renderer = self.fig.canvas.get_renderer()
        w, h = self.fig.canvas.get_width_height()
        overflow = []
        for text in self.texts:
            b = text.get_window_extent(renderer)
            if b.x0 < -1 or b.y0 < -1 or b.x1 > w+1 or b.y1 > h+1:
                overflow.append(text.get_text())
        if overflow:
            raise ValueError(f"Figure {self.number} {self.lang}: out-of-canvas text: {overflow}")
        for ext in formats:
            metadata = ({"Creator": "Matplotlib", "CreationDate": None, "ModDate": None}
                        if ext == "pdf" else {"Creator": "Matplotlib", "Date": None}
                        if ext == "svg" else {"Software": f"Matplotlib {matplotlib.__version__}"})
            self.fig.savefig(folder / f"Figure_{self.number:02d}.{ext}", dpi=DPI,
                             bbox_inches=None, pad_inches=0, metadata=metadata)
        plt.close(self.fig)
        return {"figure": self.number, "language": self.lang, "font": self.font,
                "pixels": [w, h], "text_bounds": "pass", "formats": list(formats)}


def axis(c, x, y, w, maximum, ticks, top, log=False, label="", label_y=None):
    scale = lambda v: x + (math.log10(v)/math.log10(maximum) if log else v/maximum) * w
    for v in ticks:
        xx = scale(v)
        c.line([(xx, top), (xx, y)], P["grid"], 1.5)
        c.line([(xx, y), (xx, y+9)], P["body"], 1.5)
        s = ({1: "1", 10: "10", 100: "10²", 1000: "10³", 10000: "10⁴", 100000: "10⁵"}.get(v)
             if log else f"{v:,}")
        c.t(xx, y+29, s, 25, color=P["body"], align="center")
    c.line([(x, y), (x+w, y)], P["body"], 2)
    if label:
        c.t(x+w/2, label_y or y+64, label, 25, align="center")
    return scale


def figure1(c, data):
    zh = c.lang == "zh"
    c.title("a", "Construction of the full instruction dataset", "完整指令数据集的构建", 5)
    c.card(5, 80, 440, 90, choose(c.lang, "27 source XML files", "27个源XML文件"), [], divider=False)
    c.card(1115, 80, 480, 90, choose(c.lang, "5,016 annotated sentences", "5,016条标注整句"), [], divider=False)
    c.line([(451,125), (1107,125)], arrow=True)
    c.t(780,106,choose(c.lang,"Extract and normalize","提取与规范化"),22,color=P["body"],align="center")
    # One shared input and one shared output connect all six parallel groups.
    c.rect(5, 205, 1590, 407, "#fafbfd", P["border"], 1.5, radius=8)
    c.line([(1355,170),(1355,187),(800,187),(800,205)],arrow=True)
    groups = [
        ("POS targets","词性目标","91,512 × 2 = 183,024","A3, A6"),
        ("Constituent targets","成分目标","64,459 × 2 = 128,918","A4, A11"),
        ("Clause-level tasks","小句任务","10,864 × 3 = 32,592","A7, A10, A13"),
        ("Sentence tasks and XML checks","整句任务与XML检查","5,016 × 3 + 5,001 = 20,049","M0, A5, A9 + A14"),
        ("Dynamic-word targets","动态词目标","10,941 × 1 = 10,941","A8"),
        ("Predicate-core targets","谓核目标","17,240 × 1 = 17,240","A12")]
    for i,(en,cn,formula,ids) in enumerate(groups):
        x,y = (18 if i%2==0 else 818),220+(i//2)*132
        c.rect(x,y,764,114,"white",P["border"],radius=6)
        c.t(x+22,y+31,cn if zh else en,25,True)
        c.t(x+22,y+77,formula,25)
        c.t(x+740,y+77,ids,22,color=P["muted"],align="right")
    c.line([(800,612),(800,628),(250,628),(250,645)],arrow=True)
    for x,w,fill,border,title,value,detail in [
        (5,500,P["light_blue"],P["blue"],choose(c.lang,"Corpus-derived examples","语料派生样本"),"392,764",choose(c.lang,"1 main + 12 auxiliary tasks","1类主任务＋12类辅助任务")),
        (600,460,P["light_gray"],P["border"],choose(c.lang,"Glossary (54 labels)","符号释义表（54个标记）"),"54 + 53 = 107",choose(c.lang,"A1, A2 symbol tasks","A1、A2符号问答")),
        (1115,480,P["deep_blue"],P["blue"],choose(c.lang,"Full instruction dataset","完整指令数据集"),"392,871",choose(c.lang,"15 task types","15类任务"))]:
        c.rect(x,645,w,140,fill,border,radius=6)
        c.t(x+w/2,678,title,25,True,align="center")
        c.t(x+w/2,722,value,35,True,color=border if border==P["blue"] else P["body"],align="center")
        c.t(x+w/2,758,detail,22,color=P["body"],align="center")
    c.t(550,715,"+",36,color=P["body"],align="center")
    c.line([(1067,715),(1110,715)],arrow=True)
    c.line([(5,855),(1595,855)],P["grid"],1.5)
    c.title("b","Fixed test reference and training set","固定测试参考与训练集",5,916)
    c.rect(5,1015,300,110,P["light_blue"],P["blue"],radius=6)
    c.t(155,1048,choose(c.lang,"Source records","来源记录"),25,True,align="center")
    c.t(155,1088,"5,016",32,True,color=P["blue"],align="center")
    c.line([(305,1070),(360,1070)])
    c.line([(360,1070),(360,1003),(415,1003)],arrow=True)
    c.line([(360,1070),(360,1123),(415,1123)],arrow=True)
    c.rect(420,955,440,95,"white",P["body"],radius=6,dash=True)
    c.t(640,985,choose(c.lang,"Fixed test reference","固定测试参考"),25,True,align="center")
    c.t(640,1022,choose(c.lang,"1,200 records · 1,100 normalized texts","1,200条记录 · 1,100种去空白整句"),21.5,color=P["body"],align="center")
    c.t(920,1004,choose(c.lang,"held out for evaluation","保留用于评价"),21,color=P["muted"],italic=True)
    c.line([(640,1050),(640,1071)],arrow=True)
    c.rect(420,1075,440,95,P["light_blue"],P["blue"],radius=6)
    c.t(640,1104,choose(c.lang,"Remove every text match","排除全部整句匹配"),25,True,align="center")
    c.t(640,1141,"5,016 − 1,381 = 3,635",25,align="center")
    c.line([(865,1122),(975,1122)],arrow=True)
    c.rect(980,1055,615,135,P["deep_blue"],P["blue"],radius=6)
    c.t(1287,1083,choose(c.lang,"Regenerate and sample","重新生成并采样"),25,True,align="center")
    c.t(1287,1120,"3,635 + 12 × 1,000 + 107",23,color=P["body"],align="center")
    c.t(1287,1159,choose(c.lang,"15,742 training examples","15,742条训练样本"),25,True,color=P["blue"],align="center")


def figure2(c, data):
    c.title("a","Annotator judgments","人工标注判断",5)
    c.title("b","Reference XML + rules","参考XML与规则",520)
    c.title("c","Task templates","任务模板",1120)
    c.t(50,85,choose(c.lang,"Recorded in source XML","保存在源XML中"),22,color=P["muted"])
    c.t(555,85,choose(c.lang,"Shared evidence for corpus-derived tasks","语料派生任务的共同依据"),20.5,color=P["muted"])
    c.t(1145,85,choose(c.lang,"12 corpus-derived auxiliary tasks","12类语料派生辅助任务"),22,color=P["muted"])
    # Enclosing reference and auxiliary regions make both buses explicit.
    c.rect(510,110,520,702,"white",P["blue"],1.5,radius=8)
    c.rect(1110,110,488,702,"white",P["blue"],1.5,radius=8)
    left=[("Set clause\nboundaries","界定小句范围"),("Identify\nlexical units","辨识词法单位"),
          ("Analyze\nlocal syntax","分析局部句法"),("Mark structural\nrelations","标记结构关系")]
    mid=[("Sentence–clause\nhierarchy","整句—小句层级"),("POS + word-internal\nrelations","词类与词内关系"),
         ("Constituents + cores\nRule-derived single cores","成分与谓核配置\n规则派生单核结构"),
         ("Structural relations\n+ complete XML","结构关系与完整XML")]
    right=[("Clause segmentation","小句切分","A9"),
           ("Segmentation + dynamic words","分词与动态词","A5, A7, A8"),
           ("POS + constituents","词性与成分","A3, A6 · A4, A11"),
           ("Single-core + scope\nRelations + XML checks","单核、辖域与结构\nXML检查与修复","A10, A12, A13, A14")]
    centers=[]
    for i,y in enumerate([124,300,475,650]):
        center=y+75; centers.append(center)
        c.rect(5,y,420,150,"white",P["border"],radius=7)
        c.t(215,center,choose(c.lang,*left[i]),25,True,align="center")
        c.rect(524,y,492,150,P["light_blue"],None,radius=6)
        c.t(770,center,choose(c.lang,*mid[i]),24,align="center")
        c.line([(428,center),(510,center)],P["border"],arrow=True)
        c.rect(1124,y,470,150,P["light_blue"],None,radius=6)
        en,zh,ids=right[i]
        c.t(1359,y+(52 if i!=2 else 36),choose(c.lang,en,zh),24.5,True,align="center")
        c.t(1359,y+(106 if i!=2 else 76),ids,21.5,color=P["muted"],align="center")
        if i==2:
            c.t(1359,y+114,choose(c.lang,"Given XML: interpret · Text only: analyze","给定XML：解读 · 仅给原句：分析"),20.5,color=P["body"],align="center")
    c.line([(1030,462),(1070,462)])
    c.line([(1070,centers[0]),(1070,centers[-1])])
    for yy in centers:c.line([(1070,yy),(1110,yy)],arrow=True)
    c.rect(5,860,420,120,P["light_gray"],P["border"],radius=7)
    c.t(215,899,choose(c.lang,"Symbol tasks A1, A2","符号任务 A1、A2"),25,True,align="center")
    c.t(215,941,choose(c.lang,"Independent glossary","独立符号释义表"),23,color=P["body"],align="center")
    c.rect(520,860,500,170,P["light_orange"],P["orange"],radius=7)
    c.t(770,896,choose(c.lang,"Whole-sentence main task M0","整句标注主任务 M0"),25,True,align="center")
    c.t(770,935,choose(c.lang,"Input: instruction + sentence","输入：任务要求＋原句"),22,color=P["body"],align="center")
    c.t(770,969,choose(c.lang,"Target: template-generated explanation","目标：模板生成的分步说明"),21.5,color=P["body"],align="center")
    c.t(770,1002,choose(c.lang,"+ the same record’s reference XML","＋同条记录的参考XML"),21.5,color=P["body"],align="center")
    c.line([(770,812),(770,855)],arrow=True)
    c.rect(1120,860,475,170,P["deep_blue"],P["blue"],radius=7)
    c.t(1357,917,choose(c.lang,"Mixed-task SFT","混合任务SFT"),25,True,align="center")
    c.t(1357,968,choose(c.lang,"SPS annotation\n+ explanation","SPS标注与分析说明"),23,color=P["body"],align="center")
    c.line([(1357,812),(1357,855)],arrow=True)
    c.line([(1022,945),(1115,945)],P["orange"],arrow=True)
    c.line([(215,983),(215,1065),(1357,1065),(1357,1034)],P["border"],arrow=True)
    c.t(800,1100,choose(c.lang,"Templates use reference annotations; connections show derivation and combination.",
        "模板按参考标注组织说明；连线表示派生和组合关系。"),20,color=P["muted"],align="center")


def figure3(c, data):
    c.title("a","Full instruction resource","完整指令资源",5)
    c.title("b","Training set","训练集",1180)
    c.t(46,83,"n = 392,871",24.5,color=P["muted"])
    c.t(1220,83,"n = 15,742",24.5,color=P["muted"])
    left=axis(c,600,750,520,400000,[1,10,100,1000,10000,100000],140,True,
              choose(c.lang,"Examples (log scale)","样本数（对数尺度）"))
    right=axis(c,1260,750,300,4300,[0,2000,4000],140,False,
               choose(c.lang,"Examples (linear scale)","样本数（线性尺度）"))
    for i,r in enumerate(data["tasks"]):
        y=160+i*40.7
        main=r["id"]=="M0"; color=P["orange"] if main else P["gray"] if r["id"] in ["A1","A2"] else P["blue"]
        c.t(120,y,r["id"],25,color=P["muted"])
        c.t(592,y,r["label_"+c.lang],25,main,align="right")
        c.rect(600,y-12,left(r["full_n"])-600,25,color)
        c.t(left(r["full_n"])+8,y,f'{r["full_n"]:,}',23)
        c.t(1252,y,r["id"],25,color=P["muted"],align="right")
        c.rect(1260,y-12,max(2,right(r["training_n"])-1260),25,color)
        c.t(right(r["training_n"])+7,y,f'{r["training_n"]:,}',23)
    y=884
    for x,color,en,zh in [(375,P["blue"],"Corpus-derived auxiliary task","语料派生辅助任务"),
                           (780,P["gray"],"Glossary task","符号释义任务"),
                           (1018,P["orange"],"Main task (M0)","主任务（M0）")]:
        c.rect(x,y-11,33,24.5,color)
        c.t(x+44,y,choose(c.lang,en,zh),24)


def figure4(c, data):
    c.title("a","Access points","获取入口",5)
    c.title("b","Reconstruction","公开数据重建",880)
    c.card(5,110,660,155,choose(c.lang,"Instruction data · Zenodo","指令数据 · Zenodo"),
           [choose(c.lang,"sft_tasks/ · 15 JSON files","sft_tasks/ · 15份JSON"),choose(c.lang,"392,871 examples","392,871条样本")],
           P["light_blue"],P["blue"])
    c.card(5,330,660,190,choose(c.lang,"Code + scores · GitHub","代码与评分 · GitHub"),
           ["code/ · configs/ · evaluation/",choose(c.lang,"Scripts, settings and scores","构建、训练与评分材料"),
            choose(c.lang,"reference_selection.json: saved index","reference_selection.json：固定索引")])
    c.card(5,580,660,190,choose(c.lang,"Model outputs · GitHub","模型输出 · GitHub"),
           ["outputs/*.jsonl",choose(c.lang,"6 conditions × 1,200 final outputs","6组条件 × 1,200条最终输出"),"case_id + output"])
    c.card(5,830,660,155,choose(c.lang,"Source treebank · LDC","原始树库 · LDC"),
           [choose(c.lang,"27 source XML files","27个源XML文件"),choose(c.lang,"LDC2025T06 · separate access","LDC2025T06 · 单独获取")],P["light_gray"])
    c.t(5,1045,choose(c.lang,"URLs, versions and file details: Table 7.","网址、版本与文件说明见表7。"),22,color=P["muted"])
    c.card(880,110,715,125,choose(c.lang,"Released main task","已发布整句主任务"),
           [choose(c.lang,"overall_1.json · 5,016 examples","overall_1.json · 5,016条样本")],P["light_blue"],P["blue"])
    c.card(880,310,715,160,choose(c.lang,"Recover pairs + reference","恢复配对与固定参考"),
           [choose(c.lang,"5,016 source pairs · 1,200 test records","5,016条配对 · 1,200条测试参考"),"reproduced/public_reference/"],P["light_blue"],P["blue"])
    c.card(880,545,715,125,choose(c.lang,"Exclude test-text matches","排除整句文本匹配"),
           ["5,016 − 1,381 = 3,635"],P["light_blue"],P["blue"])
    c.card(880,745,715,160,choose(c.lang,"Regenerate and sample","重新生成与采样"),
           [choose(c.lang,"3,635 main + 12,000 auxiliary","3,635条主任务＋12,000条辅助任务"),
            choose(c.lang,"+ 107 independent glossary examples","＋107条独立符号样本")],P["light_blue"],P["blue"])
    c.card(880,980,715,135,choose(c.lang,"Reconstructed training inputs","重建训练输入"),
           [choose(c.lang,"reproduced/training_instance/ · 4 JSON files · 15,742 examples",
                    "reproduced/training_instance/ · 4份JSON · 15,742条样本")],P["deep_blue"],P["blue"],body_size=20.5)
    c.line([(670,185),(875,185)],arrow=True)
    c.t(770,166,choose(c.lang,"download","下载"),21,color=P["muted"],align="center")
    c.line([(670,425),(770,425),(770,390),(875,390)],arrow=True)
    c.t(770,457,choose(c.lang,"run scripts","运行脚本"),21,color=P["muted"],align="center")
    for a,b in [(235,305),(470,540),(670,740),(905,975)]:
        c.line([(1237,a+3),(1237,b)],arrow=True)


def figure5(c, data):
    f=next(x for x in data["figures"] if x["number"]==5)
    tasks={r["stem"]:r for r in data["tasks"]}
    c.title("a","Target-response lengths","目标响应长度分布",5)
    c.line([(620,88),(657,88)],P["body"],1.8)
    c.line([(620,82),(620,94)],P["body"],1.8);c.line([(657,82),(657,94)],P["body"],1.8)
    c.t(667,88,"P10–P90",22)
    c.rect(792,78,40,20,P["blue"]);c.t(844,88,"P25–P75",22)
    c.line([(985,77),(985,100)],P["ink"],3)
    c.t(1013,88,choose(c.lang,"Median","中位数"),22)
    c.t(1470,130,choose(c.lang,"Median","中位数"),25,True,align="right")
    mapx=lambda v:600+math.log10(v)/math.log10(6000)*780
    for v in [1,10,100,1000]:
        x=mapx(v);c.line([(x,149),(x,645)],P["grid"],1.5)
        c.line([(x,645),(x,654)],P["body"],1.8)
        c.t(x,675,f"{v:,}",24.5,color=P["body"],align="center")
    for i,r in enumerate(f["panels"][0]["rows"]):
        t=tasks[r["stem"]];y=169+i*32.7;main=t["id"]=="M0"
        c.t(46,y,t["id"],25,color=P["muted"])
        c.t(590,y,t["label_"+c.lang],25,main,align="right")
        c.line([(mapx(r["p10"]),y),(mapx(r["p90"]),y)],P["body"],1.8)
        for q in ["p10","p90"]:c.line([(mapx(r[q]),y-6),(mapx(r[q]),y+6)],P["body"],1.8)
        c.rect(mapx(r["p25"]),y-10,max(1,mapx(r["p75"])-mapx(r["p25"])),20,P["orange"] if main else P["blue"])
        c.line([(mapx(r["median"]),y-13),(mapx(r["median"]),y+13)],P["ink"],3)
        c.t(1470,y,r["median_display"],25,main,align="right")
    c.line([(600,645),(1380,645)],P["body"],2)
    c.t(990,708,choose(c.lang,"Output length (Unicode code points, log scale)","output长度（Unicode码点，对数尺度）"),25,align="center")
    c.title("b","Supervision formats","监督形式",5,795)
    c.t(46,849,choose(c.lang,"Share of all 392,871 instruction examples","全部392,871条指令样本的构成"),24.5,color=P["muted"])
    width=1586;split=width*210049/392871
    c.rect(7,906,split,58,P["blue"])
    c.rect(7+split+2,906,width-split-2,58,P["gray"])
    c.t(7+split/2,935,choose(c.lang,"Explanation before the answer   210,049 (53.47%)",
                          "答案前附说明   210,049（53.47%）"),25,True,color="white",align="center")
    c.t(7+split+(width-split)/2,935,choose(c.lang,"Direct answer   182,822 (46.53%)",
                          "直接回答   182,822（46.53%）"),25,True,align="center")


def figure6(c, data):
    f=next(x for x in data["figures"] if x["number"]==6)
    c.title("a","Governing scope (scp)","谓核辖域（scp）",5)
    c.title("b","Structural function (fun)","结构功能（fun）",840)
    ma=axis(c,270,420,460,100000,[1,10,100,1000,10000,100000],110,True,
            choose(c.lang,"Occurrences (log scale)","出现次数（对数尺度）"))
    mb=axis(c,1130,420,400,10000,[1,10,100,1000,10000],110,True,
            choose(c.lang,"Occurrences (log scale)","出现次数（对数尺度）"))
    means_en={"V":"No O/C","VO":"V–O","VC":"V–C","VOC":"V–O–C","VOO":"V–O–O","OV":"O–V","VCO":"V–C–O","VOCC":"V–O–C–C"}
    means_zh={"V":"无宾补","VO":"谓宾","VC":"谓补","VOC":"谓宾补","VOO":"谓双宾","OV":"宾谓","VCO":"谓补宾","VOCC":"谓宾双补"}
    for i,r in enumerate(f["panels"][0]["rows"]):
        y=129+i*38.7
        c.t(18,y,r["code"],25,True)
        c.t(255,y,(means_zh if c.lang=="zh" else means_en)[r["code"]],24.5,color=P["body"],align="right")
        c.rect(270,y-12,max(6,ma(r["count"])-270),25,P["blue"])
        c.t(ma(r["count"])+(12 if r["count"]==1 else 8),y,f'{r["count"]:,}',23)
    for i,r in enumerate(f["panels"][1]["rows"]):
        y=129+i*38.7
        meaning=r["meaning_"+c.lang]
        if c.lang=="en" and r["code"].lower()=="coo":meaning="Nominal coord."
        c.t(858,y,r["code"],25,True)
        c.t(1115,y,meaning,24.5,color=P["body"],align="right")
        c.rect(1130,y-12,mb(r["count"])-1130,25,P["blue"])
        c.t(mb(r["count"])+8,y,f'{r["count"]:,}',23)
    c.title("c","Dynamic-word patterns (mod): ten most frequent","动态词结构模式（mod）：频次前十",5,562)
    mc=axis(c,500,990,1000,1050,[0,250,500,750,1000],635,False,
            choose(c.lang,"Pattern occurrences","模式出现次数"),1054)
    for i,r in enumerate(f["panels"][2]["rows"]):
        y=657+i*35
        c.t(20,y,r["code"],25,True)
        c.t(470,y,r["meaning_"+c.lang],24.5,color=P["body"],align="right")
        c.rect(500,y-11,mc(r["count"])-500,24.5,P["blue"])
        c.t(mc(r["count"])+10,y,f'{r["count"]:,}',23)


def figure7(c, data):
    f=next(x for x in data["figures"] if x["number"]==7)
    rows={r["id"]:r for r in f["conditions"]}
    c.rect(570,20,34,24.5,P["gray"]);c.t(620,32,choose(c.lang,"No task SFT","未SFT"),24)
    c.rect(818,20,34,24.5,P["blue"]);c.t(868,32,choose(c.lang,"After task SFT","SFT后"),24)
    groups=choose(c.lang,["Qwen2.5","Qwen3, thinking off","Qwen3, thinking on"],
                         ["Qwen2.5","Qwen3 思考关","Qwen3 思考开"])
    metric_names=choose(c.lang,["Segmentation","POS","Dynamic words","Syntax"],["分词","词性","动态词","句法"])
    for panel in f["panels"]:
        letter=panel["id"]
        col=0 if letter in "ace" else 800
        row=0 if letter in "ab" else 1 if letter in "cd" else 2
        top=[88,454,815][row]
        title=panel["title_"+c.lang]
        if c.lang=="en" and letter in "de": title=title.replace(": thinking",", thinking")+": F1"
        c.title(letter,title,title,col+5,top)
        isf1=panel["metric"]=="f1_percent"
        if isf1:
            den=" / ".join(f"{n:,}" for n in panel["denominators"])
            subtitle=choose(c.lang,f"F1 (%) · parsable predictions n = {den}",f"F1（%）· 可解析预测 n = {den}")
        else:
            subtitle=choose(c.lang,("Exact matches (%)" if letter=="f" else "Outputs (%)")+" · n = 1,200 per condition",
                            ("完全匹配率（%）" if letter=="f" else "输出比例（%）")+" · 每种条件 n = 1,200")
        c.t(col+46,top+42,subtitle,24.5,color=P["muted"])
        base=col+310; width=460
        axisy=392 if letter in "ab" else 1126 if letter=="f" else [370,736,1110][row]
        maximum=45 if letter=="f" else 112
        scale=axis(c,base,axisy,width,maximum,[0,10,20,30,40] if letter=="f" else [0,25,50,75,100],top+70)
        labels=metric_names if isf1 else groups
        centers=([553,604,655,706] if row==1 else [914,965,1016,1067]) if isf1 else (
                  [197,273,349] if row==0 else [936,1010,1084])
        barh=18 if isf1 else 24
        offset=10 if isf1 else 13
        for i,label in enumerate(labels):
            y=centers[i]
            c.t(base-10,y,label,25,align="right")
            for j in [0,1]:
                cond=panel["conditions"][j] if isf1 else panel["groups"][i]["conditions"][j]
                value=rows[cond]["metrics"][panel["metric"]][i] if isf1 else rows[cond]["metrics"][panel["metric"]]
                yy=y+(-offset if j==0 else offset)
                color=P["gray"] if j==0 else P["blue"]
                c.rect(base,yy-barh/2,max(0,scale(value)-base),barh,color)
                c.t(scale(value)+7,yy,f"{value:.2f}",24.5,j==1,color=P["body"] if j==0 else P["ink"])
    c.t(800,1178,choose(c.lang,"F1 uses each condition’s parsable predictions, including text mismatches. Percentages are given at the bar ends.",
        "F1基于各条件的可解析预测，其中包含文本不一致输出。条末标注百分比。"),20,color=P["muted"],align="center")


FUNCTIONS={1:figure1,2:figure2,3:figure3,4:figure4,5:figure5,6:figure6,7:figure7}


def draw(number, lang, output, formats=("png","svg","pdf")):
    data=load_data()
    c=Canvas(number,lang)
    FUNCTIONS[number](c,data)
    return c.save(Path(output)/lang,formats)
