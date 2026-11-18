# Manuscript figures

This folder contains the current figure sources, fixed aggregate inputs, and the English and Chinese images used in the manuscript.

## Ready-to-use figures

- `png/en/Figure_01.png` through `Figure_07.png`: English figures.
- `png/zh/Figure_01.png` through `Figure_07.png`: Chinese figures.
- `captions.json`: captions in both languages.
- `manifest.json`: file sizes and SHA256 checksums.

The 14 PNG files match the images embedded in the corresponding manuscripts. They can be used directly without a graphics runtime.

## Sources and inputs

| Figure | Drawing source | Fixed input |
|---|---|---|
| 1 | `source/figure_01.py` | Expansion-group counts and arithmetic defined in the script |
| 2, 4 | `native/diagrams.mjs` | Structural relationships, labels, and counts defined in the module |
| 3, 5, 6, 7 | `native/statistical_figures.mjs` | `data/figure_data.json` |

`native/helpers.mjs` defines the editable text, shapes, connectors, and chart styles. Shared colors, font families and canvas size are in `data/style.json`. Figures 2 and 4 use native drawing objects; Figures 3, 5, 6 and 7 combine those objects with native bar charts. Logarithmic bars and percentile intervals use explicitly positioned editable shapes, while their input values remain in the original units.

The fixed input is limited to aggregate task counts, output-length quantiles, annotation-label frequencies, and metrics for six model conditions.

## Verify the files

The integrity checks use Python's standard library:

```sh
python verify.py
```

They check package hashes, the 14 PNG hashes, task totals, quantile ordering, annotation counts, and model-condition denominators.

## Rebuild Figure 1

Figure 1 can be rebuilt independently with Python and Pillow:

```sh
python -m pip install -r requirements.txt
python rebuild.py --figures 1 --lang both --check-reference
```

The outputs are `output/en/Figure_01.png`, `output/zh/Figure_01.png`, and corresponding SVG files with editable text and vector shapes. The drawing program also runs directly:

```sh
python source/figure_01.py --lang en --output-dir output/figure1
```

The default fonts are Arial for English and Microsoft YaHei for Chinese. Figure 1 also supports Liberation Sans and Noto Sans CJK when installed. To select font files explicitly, set `FIGURE_FONT_EN`, `FIGURE_FONT_EN_BOLD`, `FIGURE_FONT_ZH`, and `FIGURE_FONT_ZH_BOLD`. Font binaries are not included. Different fonts may change text widths and pixel comparison results.

## Rebuild Figures 2–7

These figures use the `Presentation` API from **@oai/artifact-tool 2.8.180**. Rendering requires a separate compatible installation of this private host runtime; `requirements.txt` supplies Pillow only. The runner uses a local Presentation instance without a Spaces session.

When that runtime is installed, provide its `artifact_tool.mjs` entry point:

```sh
python rebuild.py --figures all --lang both --artifact-module "/path/to/artifact_tool.mjs" --check-reference
```

Use `--node "/path/to/node"` if Node.js is not on `PATH`. Alternatively, set `ARTIFACT_TOOL_MODULE` and `NODE` in the environment. For native figures alone:

```sh
node render_native.mjs --lang en --figures 2,3,4,5,6,7 --artifact-module "/path/to/artifact_tool.mjs"
```

The unified `rebuild.py` command removes only blank vertical margins from the native exports, retains the full width, and writes the finished PNGs under `output/en/` and `output/zh/`. Existing outputs require `--overwrite`. The `--check-reference` option compares all rebuilt PNG pixels with the reference files in `png/`; the result is recorded in the generated `render_check.json`.

The sources were tested on Windows with Python 3.12.14, Pillow 13.0.0, Node.js 24.22.3, and @oai/artifact-tool 2.8.180, using Arial and Microsoft YaHei. Both Figure 1 PNGs matched the reference files byte for byte; all 14 rebuilt figures matched the reference pixels. Rendering with a different font or native-runtime version can produce layout differences.

## Edit a figure

- Change Figure 1's labels, count groups and positions in `source/figure_01.py`.
- Change the flow diagrams in `native/diagrams.mjs`.
- Change statistical inputs in `data/figure_data.json` and statistical layouts in `native/statistical_figures.mjs`.
- Change native font families in `data/style.json`. Statistical figures use its palette; flow-diagram colors are declared in `native/diagrams.mjs`, and Figure 1 colors in its Python source.
- Rebuild into `output/` and inspect the resulting figure at its intended publication size.

The numeric checks enforce the reported snapshot. For a new dataset version, update the relevant input values and checks together. Keep the provided PNGs as reference images when making edits.

To recompute counts, quantiles and annotation statistics from the Zenodo ZIP, use [profile_dataset.py](../jubenwei_instructions/code/profile_dataset.py), which performs 144 comparisons against the reported values. To recompute the Figure 7 metrics from the public model outputs, follow the [evaluation guide](../jubenwei_instructions/evaluation/README.md). The figure runners redraw the resulting aggregate values.
