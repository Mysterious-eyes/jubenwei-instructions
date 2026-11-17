# Jubenwei Instructions

Code for **From Human Parsing to Instruction Tuning: A Dataset for Chinese Grammar Teaching in Second Language Acquisition**.

The project converts human Sentence Pattern Structure (SPS) annotations into instruction examples for Chinese grammar teaching. The full resource contains 392,871 examples in 15 tasks, derived from 5,016 annotated sentences and symbol definitions. The reported training set contains 15,923 examples; evaluation uses 1,200 fixed sentence records under six model conditions.

## Repository structure

```text
jubenwei_instructions/
  code/
    build_dataset/      normalization, task generation and training selection
      generators/      the 15 task generators and their analysis helpers
    inference/         Qwen2.5 and Qwen3 service clients and offline tests
    sps_converter/     SPS XML to linear-expression conversion
    evaluate.py        scoring entry point
    verify_release.py  checks for the complete data archive
  configs/             the two LlamaFactory LoRA configurations
  evaluation/
    reference_selection.json  source-position index for the fixed test set
    conditions.json           model-condition and file mapping
  task_catalog.json    task IDs and sample counts
```

This repository supplies code, configurations and structural metadata. The source XML, instruction data, test sentences, model predictions and model weights are separate resources. The source-position index contains identifiers and indices, not sentence text or XML.

## Data access and source

The source annotations originate from the **Chinese Sentence Pattern Structure Treebank**, LDC2025T06: <https://doi.org/10.35111/hx6v-6p30>. They were used in this study with permission from Weiming Peng. Obtain the original treebank under its applicable access terms from [LDC](https://catalog.ldc.upenn.edu/LDC2025T06).

The derived instruction dataset is a separate resource. Its repository DOI and download link will be added after deposit. The LDC DOI identifies the source treebank, not the derived instruction collection.

For reconstruction, place the 27 source XML files in `jubenwei_instructions/source_annotations/`. For exact archive checks and rescoring the six saved model conditions, also obtain the study's associated data files. When the `jubenwei_instructions.zip` archive is available, extract it at this repository root so its `jubenwei_instructions/` directory merges with the directory here. The archive supplies `manifest.json`, data files and saved predictions required by those checks.

## Environment

Dataset construction, verification and offline scoring use Python 3.10+ and its standard library. Inference clients additionally use the dependencies in `jubenwei_instructions/code/inference/requirements.txt`. Training requires a separate [LlamaFactory](https://github.com/hiyouga/LLaMA-Factory) installation; model serving is also separate.

## Reconstruct the dataset

Run from the resource root:

```sh
cd jubenwei_instructions
python -B code/build_dataset/preprocess.py
python -B code/build_dataset/rebuild_test_reference.py
python -B code/build_dataset/generate_all.py --source reproduced/preprocessing/sentence_xml_pairs.json
python -B code/build_dataset/select_training_data.py --source reproduced/preprocessing/sentence_xml_pairs.json --reference reproduced/evaluation_reference/reference.json
```

`select_training_data.py` is the adopted training construction method. It subtracts the 1,200 reference records by occurrence from 5,016 source records, retaining 3,816. Tasks are regenerated from that remainder; 1,000 examples are sampled from each of 12 corpus-derived auxiliary tasks. The four training inputs contain 3,816 main-task examples, 12,000 auxiliary examples, and 54 + 53 symbol examples, totaling 15,923. There is no additional repeated-text or shared-clause exclusion.

The reference index recovers the archived sample; it is not a new random draw or a claim about the historical random seed. See [construction details](jubenwei_instructions/code/build_dataset/README.md). Generated files are written under `reproduced/` and an existing output directory is refused.

## Training

Run LlamaFactory from the `jubenwei_instructions` directory, where the YAML paths are resolved. With the archived `training_instance/` and its `dataset_info.json` in place:

```sh
llamafactory-cli train configs/qwen25_lora_sft.yaml
llamafactory-cli train configs/qwen3_lora_sft.yaml
```

To train on newly reconstructed files instead, set `dataset_dir` to `reproduced/training_instance` in a copy of the configuration. The configurations contain no model weights and reconstruction does not start training.

## Inference and evaluation

Set `VLLM_BASE_URL` and `VLLM_API_KEY` for your model service. Supply a UTF-8 text file with one sentence per line using `--input`; the study's 1,200 test sentences are not included in this code repository.

```sh
python -B code/inference/qwen25_client.py --input /path/to/sentences.txt --model YOUR_SERVED_MODEL
python -B code/inference/qwen3_client.py --input /path/to/sentences.txt --model YOUR_SERVED_MODEL --thinking off
python -B code/inference/qwen3_client.py --input /path/to/sentences.txt --model YOUR_SERVED_MODEL --thinking on
```

Use a distinct `--output` for each run. These are service clients, not model servers. Full details are in the [inference README](jubenwei_instructions/code/inference/README.md).

With the matching data archive installed:

```sh
python -B code/verify_release.py
python -B code/evaluate.py --all
```

These commands verify the fixed archive and rescore saved predictions; they do not invoke a model. Four F1 scores use parsable predictions, including text-inconsistent outputs. The all-input structure match rate uses all 1,200 records.

Offline client checks can run without a model or the corpus:

```sh
python -B -m unittest discover -s code/inference -p test_clients_offline.py
```

## Citation and contact

The manuscript is in preparation. Author and title metadata are provided in `CITATION.cff`; no publication DOI is assigned here.

Corresponding author: Jingbo Sun, Minzu University of China, <sunjingbo@muc.edu.cn>.

## Licensing

No software license has yet been assigned to this repository. Source treebank rights and any future license for the derived dataset are separate from the code. This repository does not redistribute the LDC treebank or grant rights to it.
