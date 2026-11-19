"""Rebuild the seven manuscript figures with ordinary offline Python tools."""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import warnings

import matplotlib
import numpy
import PIL
from PIL import Image, ImageChops
from source.figures import draw

ROOT=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lang",choices=["en","zh","both"],default="both")
    parser.add_argument("--figures",default="all",help="all or comma-separated numbers 1–7")
    parser.add_argument("--formats",default="png,svg,pdf",help="comma-separated png,svg,pdf")
    parser.add_argument("--output-dir",type=Path,default=ROOT/"output")
    parser.add_argument("--overwrite",action="store_true")
    parser.add_argument("--check-reference",action="store_true",help="Require PNG pixels identical to png/ references")
    args=parser.parse_args()
    numbers=list(range(1,8)) if args.figures=="all" else sorted(set(map(int,args.figures.split(","))))
    formats=tuple(x.strip() for x in args.formats.split(","))
    if not numbers or any(n not in range(1,8) for n in numbers):parser.error("--figures must be 1–7")
    if not formats or any(f not in ["png","svg","pdf"] for f in formats):parser.error("Use png,svg,pdf formats")
    if args.check_reference and "png" not in formats:parser.error("--check-reference requires PNG output")
    output=args.output_dir.resolve()
    for folder in ["png","source","data"]:
        if output.is_relative_to(ROOT/folder):parser.error("Use a generated-output directory, not a reference/source directory")
    languages=["en","zh"] if args.lang=="both" else [args.lang]
    for lang in languages:
        for n in numbers:
            for ext in formats:
                if (output/lang/f"Figure_{n:02d}.{ext}").exists() and not args.overwrite:
                    parser.error("Output exists; choose a new directory or use --overwrite")
    warnings.filterwarnings("error",message="Glyph .* missing from font")
    rows=[]
    for lang in languages:
        for n in numbers:
            row=draw(n,lang,output,formats)
            if "png" in formats:
                image_path=output/lang/f"Figure_{n:02d}.png"
                reference=ROOT/"png"/lang/f"Figure_{n:02d}.png"
                a=Image.open(image_path).convert("RGB")
                same=None
                if reference.exists():
                    b=Image.open(reference).convert("RGB")
                    same=a.size==b.size and ImageChops.difference(a,b).getbbox() is None
                row.update(reference_pixels_equal=same,sha256=hashlib.sha256(image_path.read_bytes()).hexdigest())
            rows.append(row)
            print(f"{lang} Figure {n}: {row['pixels']}",flush=True)
    report={"environment":{"python":platform.python_version(),"matplotlib":matplotlib.__version__,
                           "numpy":numpy.__version__,"pillow":PIL.__version__},
            "figures":rows}
    (output/"render_check.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if args.check_reference and not all(r["reference_pixels_equal"] for r in rows):
        raise SystemExit("Pixel comparison failed. Check source values, fonts and library versions.")
    print(f"Generated {len(rows)} figures. Pixel matches: {sum(r.get('reference_pixels_equal') is True for r in rows)}.")


if __name__=="__main__":
    main()
