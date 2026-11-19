# Jubenwei Instructions

An instruction tuning dataset for teaching Chinese grammar, built from the Chinese Sentence Pattern Structure Treebank. The 5,016 annotated sentences yield 392,764 sentence-, clause- and node-level examples. A symbol glossary contributes another 107 examples, bringing the total to **392,871 across 15 tasks**.

| Resource | Where to find it |
|---|---|
| Instruction dataset · 15 JSON task files | [Zenodo · DOI 10.5281/zenodo.24343396](https://doi.org/10.5281/zenodo.24343396) · [GitHub ZIP mirror](https://github.com/Mysterious-eyes/jubenwei-instructions/releases/download/data-v1.0.0/jubenwei-instructions-data-v1.0.0.zip) · [Task catalog](jubenwei_instructions/task_catalog.json) |
| Original treebank · 27 XML files | [LDC2025T06](https://catalog.ldc.upenn.edu/LDC2025T06) · [DOI 10.35111/hx6v-6p30](https://doi.org/10.35111/hx6v-6p30) |
| Six model conditions · 1,200 test records each | [Summary CSV](jubenwei_instructions/evaluation/summary.csv) · [Per-sentence scores](jubenwei_instructions/evaluation/per_case_metrics.csv) · [7,200 final answers (ZIP)](https://github.com/Mysterious-eyes/jubenwei-instructions/releases/download/validation-v1.0.0/model-outputs-v1.0.0.zip) |
| Data construction, model training and scoring | [Construction guide](jubenwei_instructions/code/build_dataset/README.md) · [LoRA configurations](jubenwei_instructions/configs/) · [Inference](jubenwei_instructions/code/inference/README.md) · [Evaluation](jubenwei_instructions/evaluation/README.md) |
| Figures 1–7 | [Manuscript figures, source files and plotted values](figures/) |

## Model validation

Both models were fine-tuned on the same 15,742 training examples. The fixed test set contains 1,200 records representing 1,100 distinct whole-sentence texts. Each row below represents one run on the same 1,200 test records. **Task SFT** refers to the fine-tuning performed for this dataset. The two tuned Qwen3 rows use the same checkpoint with thinking disabled or enabled at inference.

All six conditions used the same [system prompt](jubenwei_instructions/code/inference/qwen3_shared_system_prompt.txt), which describes the SPS tags and attributes and contains two annotated sentence examples. A user message then supplies the sentence-annotation request. Both clients in [code release v1.1.1](https://github.com/Mysterious-eyes/jubenwei-instructions/releases/tag/v1.1.1) load this prompt by default.

| Model | Task SFT | Thinking | Parsable XML (%) | Segmentation F1 (%) | POS F1 (%) | Dynamic-word F1 (%) | Syntactic F1 (%) | Exact structure, all inputs (%) |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Qwen2.5-7B-Instruct | Before | — | 69.25 | 61.33 | 30.88 | 0.00 | 13.94 | 0.33 |
| Qwen2.5-7B-Instruct | After  | — | 93.00 | 95.20 | 91.29 | 66.03 | 85.96 | 34.50 |
| Qwen3-4B | Before | Off | 61.58 | 56.55 | 29.49 | 1.30 | 14.16 | 1.75 |
| Qwen3-4B | Before | On  | 75.42 | 67.68 | 54.05 | 4.20 | 26.69 | 6.08 |
| Qwen3-4B | After  | Off | 83.25 | 90.44 | 58.52 | 4.18 | 34.24 | 4.00 |
| Qwen3-4B | After  | On  | 94.75 | 94.34 | 90.27 | 61.72 | 83.93 | 29.92 |

Each F1 score pools matched, spurious and missed units over the parsable outputs for that condition, including outputs with text mismatches. The final column gives exact matches of the linear sentence-pattern expression over all 1,200 inputs. The [full results table](jubenwei_instructions/evaluation/summary.csv) also gives the denominators and text-fidelity counts.

## Reproduce Table 10 and Figure 7

Download the instruction ZIP from Zenodo and the model-output ZIP listed above. Run the following from a clone with Python 3.10 or later. Scoring uses the Python standard library.

```sh
cd jubenwei_instructions
python -B code/rescore_release.py --dataset /path/to/jubenwei-instructions-data-v1.0.0.zip --outputs /path/to/model-outputs-v1.0.0.zip --check
```

The scorer recovers the test reference from the whole-sentence task and the saved [selection index](jubenwei_instructions/evaluation/reference_selection.json). It verifies the checksum of the 1,200 reference records, parses the saved model answers and compares the recomputed measures with the published summary. The [evaluation guide](jubenwei_instructions/evaluation/README.md) describes each field and the per-sentence calculations.

## Use the data

Extract the instruction ZIP under the inner `jubenwei_instructions/` directory to read the task files in `sft_tasks/`. Each record contains `instruction`, `input` and `output`. The instruction includes the request and its context. In the main task, the output contains the clause-by-clause explanation followed by the reference XML.

To recover the training inputs from the **public dataset ZIP**, run these commands from the inner directory:

```sh
python -B code/reference_from_tasks.py --dataset /path/to/jubenwei-instructions-data-v1.0.0.zip --source-pairs
python -B code/build_dataset/select_training_data.py --source reproduced/public_reference/sentence_xml_pairs.json --reference reproduced/public_reference/reference.json
```

To regenerate the task counts, response-length quantiles and XML attribute frequencies in Figures 1, 3, 5 and 6, run:

```sh
python -B code/profile_dataset.py --dataset /path/to/jubenwei-instructions-data-v1.0.0.zip --check-figure-data ../figures/data/figure_data.json
```

The selector compares entire sentences after removing whitespace, retaining punctuation and case. The 1,100 distinct test texts match 1,381 of the 5,016 source records. All matches are excluded, including records with a different XML annotation. The remaining 3,635 source records retain their order and can share clauses with test sentences. The generators rebuild the main task and the 12 corpus-derived auxiliary tasks from those records. Sampling 1,000 examples per auxiliary task and adding 54 + 53 glossary examples gives 3,635 + 12,000 + 107 = **15,742 training examples**.

The four training inputs from `select_training_data.py` are written to `reproduced/training_instance/`. Set `dataset_dir` to that directory in a copy of the appropriate [LlamaFactory configuration](jubenwei_instructions/configs/) before training. For reconstruction starting with the licensed LDC files, follow the [XML preprocessing and task generation guide](jubenwei_instructions/code/build_dataset/README.md). To run inference on a served checkpoint, use the [model clients](jubenwei_instructions/code/inference/README.md).

## Citation

**Dataset:** Yang, X. et al. *From Human Parsing to Instruction Tuning: A Dataset for Chinese Grammar Teaching in Second Language Acquisition*. Zenodo (2026). [10.5281/zenodo.24343396](https://doi.org/10.5281/zenodo.24343396). The Zenodo record specifies CC BY 4.0 for the derived dataset.

**Source treebank:** Peng, W. et al. *Chinese Sentence Pattern Structure Treebank*, LDC2025T06. Linguistic Data Consortium (2025). [10.35111/hx6v-6p30](https://doi.org/10.35111/hx6v-6p30).

**Software and results:** [Code and shared-prompt clients v1.1.1](https://github.com/Mysterious-eyes/jubenwei-instructions/releases/tag/v1.1.1) · [Training-set construction v1.1.0](https://github.com/Mysterious-eyes/jubenwei-instructions/releases/tag/v1.1.0) · [Archived model answers and scores validation-v1.0.0](https://github.com/Mysterious-eyes/jubenwei-instructions/releases/tag/validation-v1.0.0) · [Software citation](CITATION.cff). The instruction data, training construction and archived scores are unchanged by the client update.

Correspondence: Jingbo Sun, Minzu University of China ([sunjingbo@muc.edu.cn](mailto:sunjingbo@muc.edu.cn)).
