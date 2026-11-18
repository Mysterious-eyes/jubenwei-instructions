"""Bilingual, editable SVG and print-resolution PNG for Figure 1.

Run with Python and Pillow. No dataset files are read or modified.
The six expansion groups and their arithmetic are checked before drawing.
"""
from pathlib import Path
import os
import json
import math
from html import escape
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "output" / "figure1"
W, H = 3200, 2720
P = {
    "ink": "#17334F", "muted": "#54697C", "blue": "#3A7296",
    "teal": "#00838D", "orange": "#BC7A36", "line": "#C8D5DF",
    "faint": "#F6F8FA", "pale_blue": "#F2F6FA", "pale_teal": "#EFF7F7",
    "pale_orange": "#FCF6EF", "white": "#FFFFFF",
}

GROUPS = [
    ("词类目标", "Word-class targets", "91,512 × 2 = 183,024", "A3 / A6", 91512 * 2),
    ("成分目标", "Constituent targets", "64,459 × 2 = 128,918", "A4 / A11", 64459 * 2),
    ("小句任务", "Clause-level tasks", "10,864 × 3 = 32,592", "A7 / A10 / A13", 10864 * 3),
    ("整句任务与XML检查", "Sentence tasks and XML checks", "5,016 × 3 + 5,001 = 20,049", "M0 / A5 / A9  +  A14", 5016 * 3 + 5001),
    ("动态词目标", "Dynamic-word targets", "10,941 × 1 = 10,941", "A8", 10941),
    ("谓核目标", "Predicate-core targets", "17,240 × 1 = 17,240", "A12", 17240),
]
assert sum(g[4] for g in GROUPS) == 392764
assert 54 + 53 == 107
assert 392764 + 107 == 392871
assert 5016 - 6 * 200 == 3816
assert 3816 + 12 * 1000 + 107 == 15923


def font_path(lang, bold):
    """Resolve font files, with explicit environment-variable overrides."""
    key = f"FIGURE_FONT_{lang.upper()}" + ("_BOLD" if bold else "")
    if os.environ.get(key):
        p = Path(os.environ[key])
        if p.is_file():
            return p
        raise FileNotFoundError(f"{key} does not point to a font file: {p}")
    if lang == "zh":
        candidates = [
            Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        ]
    else:
        candidates = [
            Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
            Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
        ]
    for p in candidates:
        if p.is_file():
            return p
    raise FileNotFoundError(f"Install an appropriate font or set {key} to its path.")


class Canvas:
    def __init__(self, lang):
        self.lang = lang
        self.im = Image.new("RGB", (W, H), P["white"])
        self.draw = ImageDraw.Draw(self.im)
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
                    '<title>Instruction dataset construction and training-set selection</title>',
                    f'<rect width="{W}" height="{H}" fill="white"/>']
        self.fonts = {}
        self.text_audit = []

    def font(self, size, bold=False):
        key = size, bold
        if key not in self.fonts:
            self.fonts[key] = ImageFont.truetype(str(font_path(self.lang, bold)), size)
        return self.fonts[key]

    def text(self, x, y, s, size=64, bold=False, color=None, align="left", width=None):
        assert size >= 64, (s, size)
        color = color or P["ink"]
        f = self.font(size, bold)
        anchor = {"left": "ls", "center": "ms", "right": "rs"}[align]
        bounds = self.draw.textbbox((x, y), s, font=f, anchor=anchor)
        if width is not None:
            assert bounds[2] - bounds[0] <= width, (s, bounds[2]-bounds[0], width)
        assert bounds[0] >= 0 and bounds[1] >= 0 and bounds[2] <= W and bounds[3] <= H, (s, bounds)
        self.draw.text((x, y), s, font=f, fill=color, anchor=anchor)
        family = "Microsoft YaHei, Noto Sans CJK SC, sans-serif" if self.lang == "zh" else "Arial, Liberation Sans, sans-serif"
        ta = {"left": "start", "center": "middle", "right": "end"}[align]
        self.svg.append(f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}" text-anchor="{ta}">{escape(s)}</text>')
        self.text_audit.append({"text": s, "font_px": size, "bounds": bounds})

    def rect(self, x, y, w, h, fill="white", stroke=None, sw=3):
        self.draw.rectangle((x, y, x+w, y+h), fill=fill, outline=stroke, width=sw)
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke or "none"}" stroke-width="{sw}"/>')

    def line(self, points, color=None, sw=4, arrow=False):
        color = color or P["muted"]
        self.draw.line(points, fill=color, width=sw, joint="curve")
        coords = " ".join(f"{x},{y}" for x, y in points)
        self.svg.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linejoin="round"/>')
        if arrow:
            (x0, y0), (x1, y1) = points[-2:]
            angle = math.atan2(y1-y0, x1-x0)
            length, breadth = 24, 11
            pts = [(x1, y1),
                   (x1-length*math.cos(angle)+breadth*math.sin(angle), y1-length*math.sin(angle)-breadth*math.cos(angle)),
                   (x1-length*math.cos(angle)-breadth*math.sin(angle), y1-length*math.sin(angle)+breadth*math.cos(angle))]
            self.draw.polygon(pts, fill=color)
            coords = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
            self.svg.append(f'<polygon points="{coords}" fill="{color}"/>')

    def card(self, x, y, w, h, color, fill="white"):
        self.rect(x, y, w, h, fill, P["line"], 3)
        self.rect(x, y, w, 8, color)

    def save(self):
        OUT.mkdir(parents=True, exist_ok=True)
        stem = f"Figure_01_{self.lang}"
        (OUT / f"{stem}.svg").write_text("\n".join(self.svg + ["</svg>"]), encoding="utf-8")
        self.im.save(OUT / f"{stem}.png", dpi=(533.3333, 533.3333), optimize=True)
        return self.text_audit


def make(lang):
    c = Canvas(lang)
    zh = lang == "zh"
    c.text(120, 120, "a  完整指令数据集的构建" if zh else "a  Construction of the full instruction dataset", 82, True)

    c.rect(120, 190, 2960, 160, P["faint"], P["line"])
    c.text(490, 292, "27个源XML文件" if zh else "27 source XML files", 70, True, align="center", width=700)
    c.text(1270, 250, "整句提取与规范化" if zh else "Extract and normalize", 64, align="center", width=840)
    c.line([(850, 295), (1690, 295)], P["muted"], 4, True)
    c.text(2390, 292, "5,016条整句" if zh else "5,016 sentences", 80, True, align="center", width=1200)
    c.line([(1600, 350), (1600, 417)], P["muted"], 4, True)

    # The outer outline groups parallel expansions, not sequential operations.
    c.rect(120, 420, 2960, 870, P["faint"], P["line"], 3)
    for i, (cn, en, formula, codes, _) in enumerate(GROUPS):
        x, y = (150 if i % 2 == 0 else 1640), 450 + (i // 2) * 280
        accent = P["blue"] if i < 2 else P["teal"]
        c.card(x, y, 1410, 245, accent)
        c.text(x+45, y+77, cn if zh else en, 66, True, width=1320)
        c.text(x+45, y+156, formula, 74, True, width=1320)
        c.text(x+45, y+220, codes, 64, color=P["muted"], width=1320)
    c.line([(570, 1290), (570, 1384)], P["blue"], 4, True)

    c.card(120, 1390, 900, 280, P["blue"], P["pale_blue"])
    c.text(570, 1465, "语料派生问答" if zh else "Corpus-derived examples", 64, True, align="center", width=820)
    c.text(570, 1560, "392,764", 100, True, align="center")
    c.text(570, 1630, "1类主任务＋12类辅助任务" if zh else "1 main + 12 auxiliary tasks", 64, align="center", width=840)

    c.text(1085, 1550, "+", 90, True, align="center", color=P["muted"])
    c.card(1150, 1390, 900, 280, P["orange"], P["pale_orange"])
    c.text(1600, 1465, "独立符号释义表" if zh else "Independent symbol tasks", 64, True, align="center", width=830)
    c.text(1600, 1557, "54 + 53 = 107", 80, True, align="center", width=840)
    c.text(1600, 1630, "A1 / A2", 64, align="center")
    c.line([(2070, 1530), (2160, 1530)], P["muted"], 4, True)

    c.card(2180, 1390, 900, 280, P["teal"], P["pale_teal"])
    c.text(2630, 1465, "完整指令数据集" if zh else "Full instruction dataset", 66, True, align="center", width=830)
    c.text(2630, 1560, "392,871", 100, True, align="center", color=P["teal"])
    c.text(2630, 1630, "15类任务" if zh else "15 task types", 64, align="center")

    c.line([(120, 1780), (3080, 1780)], P["line"], 3)
    c.text(120, 1885, "b  固定测试参考与训练集" if zh else "b  Fixed test reference and training set", 82, True)

    c.card(120, 2160, 600, 220, P["blue"], P["pale_blue"])
    c.text(420, 2240, "来源整句记录" if zh else "Source records", 64, True, align="center", width=550)
    c.text(420, 2335, "5,016", 96, True, align="center")
    c.line([(720, 2270), (830, 2270)], P["muted"], 4)
    c.line([(830, 2270), (830, 2090), (1015, 2090)], P["blue"], 4, True)
    c.line([(830, 2270), (830, 2415), (1015, 2415)], P["teal"], 4, True)

    c.card(1030, 1990, 900, 200, P["blue"], P["pale_blue"])
    c.text(1480, 2065, "先抽取固定测试参考" if zh else "Fix the test sample first", 64, True, align="center", width=830)
    c.text(1480, 2150, "6组 × 200 = 1,200" if zh else "6 groups × 200 = 1,200", 72, True, align="center", width=840)

    c.card(1030, 2315, 900, 200, P["teal"], P["pale_teal"])
    c.text(1480, 2390, "剩余训练来源" if zh else "Remaining source records", 64, True, align="center", width=830)
    c.text(1480, 2485, "3,816", 96, True, align="center")
    c.line([(1930, 2415), (2090, 2415)], P["teal"], 4, True)

    c.card(2110, 2315, 970, 280, P["teal"], P["pale_teal"])
    c.text(2595, 2390, "重新生成任务并采样" if zh else "Regenerate and sample", 64, True, align="center", width=900)
    c.text(2595, 2475, "3,816 + 12 × 1,000 + 107", 64, align="center", width=900)
    c.text(2595, 2560, "15,923条训练样本" if zh else "15,923 training examples", 74, True, align="center", width=900)
    return c.save()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lang", choices=["en", "zh", "both"], default="both")
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    OUT = args.output_dir.resolve()
    languages = ("en", "zh") if args.lang == "both" else (args.lang,)
    audits = {lang: make(lang) for lang in languages}
    metadata = {
        "width_px": W, "height_px": H, "height_width_ratio": H / W,
        "minimum_font_px": 64, "minimum_font_pt_at_6_in_width": 64 / W * 6 * 72,
        "corpus_groups": [dict(label_en=g[1], formula=g[2], tasks=g[3], subtotal=g[4]) for g in GROUPS],
        "corpus_derived": 392764, "symbols": 107, "full_dataset": 392871,
        "source_records": 5016, "test_records": 1200, "remaining_records": 3816,
        "sampled_auxiliary": 12000, "training_examples": 15923,
        "layout_validation": "All text stays within canvas and specified label widths.",
        "svg_text": True, "raster_embedded_in_svg": False,
        "text_objects": {k: len(v) for k, v in audits.items()},
    }
    (OUT / "figure_01_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=True))
