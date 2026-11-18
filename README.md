# Jubenwei Instructions

This project converts manual Sentence Pattern Structure (SPS) annotations into instruction tuning examples for teaching Chinese grammar. The full collection contains **392,871 examples across 15 tasks**, derived from **5,016 annotated sentences** and symbol definitions. The study uses **15,923 training examples** and a fixed **1,200-record test set** under six model conditions.

[Download data v1.0.0](https://github.com/Mysterious-eyes/jubenwei-instructions/releases/download/data-v1.0.0/jubenwei-instructions-data-v1.0.0.zip) · [Code release v1.0.0](https://github.com/Mysterious-eyes/jubenwei-instructions/releases/tag/v1.0.0) · [Task catalog](jubenwei_instructions/task_catalog.json) · [Construction guide](jubenwei_instructions/code/build_dataset/README.md) · [Inference guide](jubenwei_instructions/code/inference/README.md)

## Instruction data

The [dataset release](https://github.com/Mysterious-eyes/jubenwei-instructions/releases/tag/data-v1.0.0) contains the complete instruction collection. Extract the ZIP inside `jubenwei_instructions/` to create `sft_tasks/`. Each of the 15 files is a UTF-8 JSON array. The task catalog lists the file names and example counts. To reconstruct the training and test sets, use the source files and commands below.

## Source XML and repository locations

The original annotations come from the **Chinese Sentence Pattern Structure Treebank (LDC2025T06)**.

- [LDC catalog and access information](https://catalog.ldc.upenn.edu/LDC2025T06)
- [Source treebank DOI: 10.35111/hx6v-6p30](https://doi.org/10.35111/hx6v-6p30)
- [Annotation documentation](https://catalog.ldc.upenn.edu/docs/LDC2025T06/introduction_SPS_Treebank_v1.0.pdf)

This GitHub repository contains code, training configurations, and metadata. Obtain the source XML separately through LDC. The construction workflow expects the 27 XML files in `jubenwei_instructions/source_annotations/`. The [reference selection index](jubenwei_instructions/evaluation/reference_selection.json) identifies the source files and sentence positions used to recover the fixed test set.

| Resource | Location relative to the repository root |
|---|---|
| Downloaded instruction data | `jubenwei_instructions/sft_tasks/` |
| Source XML, obtained separately | `jubenwei_instructions/source_annotations/` |
| Preprocessing and 15 task generators | [jubenwei_instructions/code/build_dataset/](jubenwei_instructions/code/build_dataset/) |
| Training configurations | [jubenwei_instructions/configs/](jubenwei_instructions/configs/) |
| Inference clients | [jubenwei_instructions/code/inference/](jubenwei_instructions/code/inference/) |
| Evaluation code | [jubenwei_instructions/code/evaluate.py](jubenwei_instructions/code/evaluate.py) |
| Test selection index and model-condition metadata | [jubenwei_instructions/evaluation/](jubenwei_instructions/evaluation/) |
| Files produced by reconstruction | `jubenwei_instructions/reproduced/` |



## Reconstruct the data

Use Python 3.10 or later. Dataset construction and offline scoring use the standard library.

Run from the resource directory inside this repository. Subsequent command examples use the same working directory:

```sh
cd jubenwei_instructions
python -B code/build_dataset/preprocess.py
python -B code/build_dataset/rebuild_test_reference.py
python -B code/build_dataset/generate_all.py --source reproduced/preprocessing/sentence_xml_pairs.json
python -B code/build_dataset/select_training_data.py --source reproduced/preprocessing/sentence_xml_pairs.json --reference reproduced/evaluation_reference/reference.json
```

| Output | Contents |
|---|---|
| `reproduced/preprocessing/` | 5,016 extracted and normalized sentence–XML pairs |
| `reproduced/evaluation_reference/reference.json` | The fixed 1,200-record reference, in its saved order |
| `reproduced/full_collection/sft_tasks/` | All 15 task files, totaling 392,871 examples |
| `reproduced/training_instance/` | Four training input files, totaling 15,923 examples, plus configuration and construction reports |

`select_training_data.py` implements the study's training-set construction method. It subtracts each of the 1,200 test records once from the source records, retaining 3,816. Tasks are regenerated from these records, and 1,000 examples are sampled from each of 12 corpus-derived auxiliary tasks. The training set combines 3,816 main-task examples, 12,000 auxiliary examples, and 54 + 53 symbol examples.

Each instruction example has three string fields: `instruction` contains the task request and context, `input` is empty, and `output` contains the target answer. Some outputs include a reference-derived explanation inside `<think>...</think>` before the answer. The main task ends with the normalized XML annotation.

The [construction guide](jubenwei_instructions/code/build_dataset/README.md) describes the matching rules, generator files, output options, and validation reports. Construction commands create a new output directory and refuse to overwrite an existing one.

## Train a model

Training requires [LlamaFactory](https://github.com/hiyouga/LLaMA-Factory) and the selected model checkpoint. The supplied configurations load the four JSON files through `training_instance/dataset_info.json`.

For reconstructed data, set `dataset_dir` to `reproduced/training_instance` in a copy of the configuration and pass that file to LlamaFactory. With the study's `training_instance/` directory installed, the supplied paths can be used directly:

```sh
llamafactory-cli train configs/qwen25_lora_sft.yaml
llamafactory-cli train configs/qwen3_lora_sft.yaml
```

## Run inference

Install `code/inference/requirements.txt`, start an OpenAI-compatible model service, and set `VLLM_BASE_URL` and `VLLM_API_KEY`. Supply a UTF-8 file with one input sentence per line:

```sh
python -B code/inference/qwen25_client.py --input /path/to/sentences.txt --model YOUR_SERVED_MODEL
python -B code/inference/qwen3_client.py --input /path/to/sentences.txt --model YOUR_SERVED_MODEL --thinking off
python -B code/inference/qwen3_client.py --input /path/to/sentences.txt --model YOUR_SERVED_MODEL --thinking on
```

Use a different `--output` for each condition. Outputs are saved under `reproduced/inference/` by default. See the [inference guide](jubenwei_instructions/code/inference/README.md) for response fields and available options.

## Evaluate saved predictions

Score a generated prediction file against the reference reconstructed above:

```sh
python -B code/evaluate.py --prediction reproduced/inference/YOUR_RESULT.txt --reference reproduced/evaluation_reference/reference.json
```

The evaluator scores the final XML in saved predictions. The four F1 scores use parsable predictions, including text-inconsistent outputs; the all-input structure match rate uses all 1,200 test records.

To rescore the study's six saved conditions, obtain the corresponding prediction files separately, place them in `evaluation/predictions/`, and run:

```sh
python -B code/evaluate.py --all --reference reproduced/evaluation_reference/reference.json
```

`verify_release.py` checks a complete study archive against its `manifest.json`. It requires that manifest and all listed files, beyond the 15-file instruction-data ZIP.

The offline client checks use simulated responses:

```sh
python -B -m unittest discover -s code/inference -p test_clients_offline.py
```

## Citation and contact

For the instruction examples, cite [Chinese grammar instruction dataset v1.0.0](https://github.com/Mysterious-eyes/jubenwei-instructions/releases/tag/data-v1.0.0). Software citation metadata are in [CITATION.cff](CITATION.cff). Cite the [LDC treebank](https://doi.org/10.35111/hx6v-6p30) when using its source annotations.

Corresponding author: Jingbo Sun, Minzu University of China, [sunjingbo@muc.edu.cn](mailto:sunjingbo@muc.edu.cn).
