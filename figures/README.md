# Manuscript figures

Seven English and seven Chinese figures are supplied in png/en/ and png/zh/.
captions.json contains their captions. The package also includes drawing code
and aggregate plotting values. Download the complete [figure ZIP](https://github.com/Mysterious-eyes/jubenwei-instructions/releases/download/v1.0.0/jubenwei-instructions-figures-v1.0.0.zip) from release v1.0.0.

## Rebuild

Install the common Python dependencies once:

    python -m pip install -r requirements.txt
    python rebuild.py --lang both --figures all --check-reference

The build runs locally and offline. It writes PNG, SVG and PDF files to
output/en/ and output/zh/. SVG retains editable text and vector objects;
PDF embeds the font subsets. All panels of each figure are combined in one file.
Use --figures 3,5 or --lang en for selected figures, and --formats png
if only raster images are needed. Existing outputs require --overwrite.

The drawing source is source/figures.py; statistical inputs are in
data/figure_data.json. The input contains aggregate task sizes, length
quantiles, annotation frequencies and the six model conditions.
There are no source sentences or model responses in this directory.

Figure 1 groups the six parallel corpus expansions under one common input
and one common output. Figure 2 distinguishes recorded grammatical judgments,
reference structures and template-derived targets; the independent glossary
tasks join training separately. Figure 4 distinguishes download locations from
the local reconstruction route. Figures 3 and 5 use task order A1–A14, then M0.

## Fonts and repeatability

The reference build uses Arial for English and Microsoft YaHei for Chinese.
The reference environment is Python 3.12.14, Matplotlib 3.11.2, NumPy 2.5.4 and Pillow 13.0.0.
Install Noto Sans CJK SC on systems without Microsoft YaHei. A CJK font is
also needed for the literal fullwidth vertical-line symbol in the English SPS
labels. Font files are not included.

The renderer detects installed fonts. To select a particular file, set
FIGURE_FONT_EN and FIGURE_FONT_ZH to its path. English fallback choices
include Liberation Sans and the DejaVu Sans supplied with Matplotlib.
Different fonts or library versions can change pixels or text widths.
The generated render_check.json records the environment, selected fonts,
dimensions and reference-pixel comparison. Missing glyphs or text extending
beyond the canvas stop the build.

## Verify and edit

    python verify.py

This uses manifest.json to check package integrity, fourteen reference images, task totals, task order,
quantile ordering, annotation counts and evaluation denominators.
Edit labels and layout in source/figures.py, and numerical inputs in
data/figure_data.json. Rebuild to a separate output directory and inspect
the figures at their intended publication size.

To recompute counts, quantiles and annotation frequencies from the public
instruction ZIP, use [profile_dataset.py](../jubenwei_instructions/code/profile_dataset.py),
which performs 144 comparisons against the reported values. To reproduce the
Figure 7 metrics from the released model answers, follow the
[evaluation guide](../jubenwei_instructions/evaluation/README.md).
