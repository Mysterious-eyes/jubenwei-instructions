# Jubenwei Instructions

An instruction dataset for teaching Chinese grammar and training models to annotate sentence structure. It contains **392,871 examples across 15 tasks**: 392,764 examples derived from 5,016 annotated sentences, plus 107 symbol-definition examples. The source annotations follow the Sentence Pattern Structure (SPS) scheme.

This repository provides the construction code, model clients, offline evaluation and bilingual figures accompanying *From human parsing to instruction tuning: a Chinese grammar teaching dataset for second language acquisition*. All repository assets are available in [release v1.0.0](https://github.com/Mysterious-eyes/jubenwei-instructions/releases/tag/v1.0.0).

## Data and downloads

| Material | Access |
|---|---|
| Instruction data: 15 JSON task files | [Zenodo · DOI 10.5281/zenodo.24343396](https://doi.org/10.5281/zenodo.24343396) · [Data ZIP](https://github.com/Mysterious-eyes/jubenwei-instructions/releases/download/v1.0.0/jubenwei-instructions-data-v1.0.0.zip) · [Task catalog](jubenwei_instructions/task_catalog.json) |
| Figures 1–7 in English and Chinese, drawing code and captions | [Browse figures](figures/) · [Figure package ZIP](https://github.com/Mysterious-eyes/jubenwei-instructions/releases/download/v1.0.0/jubenwei-instructions-figures-v1.0.0.zip) |
| Final model answers: six conditions × 1,200 records | [model-outputs-v1.0.0.zip](https://github.com/Mysterious-eyes/jubenwei-instructions/releases/download/v1.0.0/model-outputs-v1.0.0.zip) |
| Evaluation summary and per-case counts | [Summary](jubenwei_instructions/evaluation/summary.csv) · [Per-case metrics](jubenwei_instructions/evaluation/per_case_metrics.csv) · [Download summary.csv](https://github.com/Mysterious-eyes/jubenwei-instructions/releases/download/v1.0.0/summary.csv) · [Download per_case_metrics.csv](https://github.com/Mysterious-eyes/jubenwei-instructions/releases/download/v1.0.0/per_case_metrics.csv) |
| Original treebank: 27 XML files | [LDC2025T06](https://catalog.ldc.upenn.edu/LDC2025T06) · [DOI 10.35111/hx6v-6p30](https://doi.org/10.35111/hx6v-6p30) |

The instruction ZIP contains `sft_tasks/`. Each file is a UTF-8 JSON array with three string fields: `instruction` holds the request and its context, `input` is empty, and `output` holds the target answer. In the whole-sentence task, the target contains a template-generated explanation followed by the normalized reference XML. Other tasks address symbol meanings, lexical and syntactic decisions, and XML checking.

The rights holders authorized distribution of these derived instruction files under **CC BY 4.0**, including the original text and normalized XML for all 5,016 source records. The original XML treebank is obtained separately under the LDC2025T06 terms. Source XML files, training files and model checkpoints are not stored in the Git checkout.

## Reproduce the model evaluation

Download the instruction and model-output ZIPs above. From the inner `jubenwei_instructions/` directory, run with Python 3.10 or later:

```sh
cd jubenwei_instructions
python -B code/rescore_release.py --dataset /path/to/jubenwei-instructions-data-v1.0.0.zip --outputs /path/to/model-outputs-v1.0.0.zip --check
```

This standard-library command recovers the ordered test reference from the main task and the saved selection index, scores all 7,200 final answers, and checks the result against `evaluation/summary.csv`. It does not contact a model service. To check the summary using only the published per-case counts:

```sh
python -B code/aggregate_metrics.py --check evaluation/summary.csv
```

| Model | Project-specific SFT | Thinking | Parsable XML (%) | Exact structure, all 1,200 inputs (%) |
|---|---|---|---:|---:|
| Qwen2.5-7B-Instruct | No | — | 69.25 | 0.33 |
| Qwen2.5-7B-Instruct | Yes | — | 93.00 | 34.50 |
| Qwen3-4B | No | Off | 61.58 | 1.75 |
| Qwen3-4B | No | On | 75.42 | 6.08 |
| Qwen3-4B | Yes | Off | 83.25 | 4.00 |
| Qwen3-4B | Yes | On | 94.75 | 29.92 |

All conditions use the same 1,200 test records and the same [system prompt](jubenwei_instructions/code/inference/qwen3_shared_system_prompt.txt), containing SPS conventions and two complete annotated sentence examples. A user message supplies the test sentence. Qwen3 thinking modes are compared on the same checkpoint within each fine-tuning stage.

The [full summary](jubenwei_instructions/evaluation/summary.csv) gives four component F1 scores, text fidelity and both structural-match denominators. F1 pools unit counts over each condition's parsable predictions, including text mismatches; the contributing cases can differ between conditions. Structural matching compares linear expressions regenerated from the reference and predicted XML. The all-input rate includes every test record. See the [evaluation guide](jubenwei_instructions/evaluation/README.md) for alignment rules and per-case reproduction.

## Rebuild the figures and data statistics

From the repository root:

```sh
cd figures
python -m pip install -r requirements.txt
python rebuild.py --lang both --figures all
python verify.py
```

The renderer writes PNG, editable SVG and PDF files under `figures/output/`. Captions and aggregate plotting values accompany the drawing source. The [figure guide](figures/README.md) describes fonts, reference-image checking and selected-figure builds.

To recompute task counts, response-length quantiles and XML attribute frequencies from the instruction ZIP, run from `jubenwei_instructions/`:

```sh
python -B code/profile_dataset.py --dataset /path/to/jubenwei-instructions-data-v1.0.0.zip --check-figure-data ../figures/data/figure_data.json
```

## Reconstruct the training inputs

Run from `jubenwei_instructions/`:

```sh
python -B code/reference_from_tasks.py --dataset /path/to/jubenwei-instructions-data-v1.0.0.zip --source-pairs
python -B code/build_dataset/select_training_data.py --source reproduced/public_reference/sentence_xml_pairs.json --reference reproduced/public_reference/reference.json
```

The fixed test set contains 1,100 distinct whole-sentence texts after whitespace removal. Excluding all 1,381 matching source records leaves 3,635 records, preserving punctuation, case, retained duplicates and shared clauses. The generators rebuild tasks from those records. The training set combines 3,635 whole-sentence examples, 1,000 examples from each of 12 auxiliary tasks, and 54 + 53 glossary examples: **15,742 examples** in four JSON files.

Outputs are written to `reproduced/training_instance/`. Use this directory as `dataset_dir` in a copy of the appropriate [LoRA configuration](jubenwei_instructions/configs/). The [construction guide](jubenwei_instructions/code/build_dataset/README.md) also covers reconstruction from licensed XML and validation of the generated files. The [inference guide](jubenwei_instructions/code/inference/README.md) explains how to supply an endpoint and run either model client. Offline reconstruction and scoring do not download checkpoints, train models or run inference.

## Citation

**Dataset:** Yang, X. et al. *From Human Parsing to Instruction Tuning: A Chinese Grammar Teaching Dataset for Second Language Acquisition*. Zenodo (2026). [10.5281/zenodo.24343396](https://doi.org/10.5281/zenodo.24343396).

**Source treebank:** Peng, W. et al. *Chinese Sentence Pattern Structure Treebank*, LDC2025T06. Linguistic Data Consortium (2025). [10.35111/hx6v-6p30](https://doi.org/10.35111/hx6v-6p30).

For software and figures, see [CITATION.cff](CITATION.cff) and [release v1.0.0](https://github.com/Mysterious-eyes/jubenwei-instructions/releases/tag/v1.0.0).

Correspondence: Jingbo Sun, Minzu University of China ([sunjingbo@muc.edu.cn](mailto:sunjingbo@muc.edu.cn)).
