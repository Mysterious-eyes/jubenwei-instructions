# Build the instruction dataset

The workflow constructs the full 15-task collection and the training set used in the study. `select_training_data.py` implements training-set construction by subtracting the fixed test records, regenerating tasks from the remaining source records, and sampling auxiliary tasks.

Use Python 3.10 or later. All construction scripts use the standard library. Run the examples from `jubenwei_instructions/`, the resource directory inside the repository. Relative data paths are resolved against this directory.

The input is the 27 source XML files described on the [LDC2025T06 page](https://catalog.ldc.upenn.edu/LDC2025T06). Place them in `source_annotations/`. The repository's `evaluation/reference_selection.json` records the source filenames, sentence positions, and hashes used for the fixed reference. See the [main README](../../../README.md) for data access and repository layout.

The precomputed full collection is also available as [data-v1.0.0](https://github.com/Mysterious-eyes/jubenwei-instructions/releases/tag/data-v1.0.0). That ZIP contains the 15 task files; the steps below reconstruct the full collection, fixed reference, and training set from the source XML.

## 1. Extract and normalize the source annotations

```sh
python -B code/build_dataset/preprocess.py
```

Input: `source_annotations/`. Output: `reproduced/preprocessing/`.

- `extracted_pairs.json`: original sentence text paired with its serialized `ju`, including source attributes.
- `sentence_xml_pairs.json`: the same pairs with only `scp`, `fun`, and `mod` retained and formatting whitespace normalized.
- `preprocess_report.json`: counts and source/output hashes.

The 27 files yield 5,016 pairs. Files are traversed in sorted path order and `ju` elements in document order, preserving each source occurrence.

## 2. Rebuild the fixed test reference

```sh
python -B code/build_dataset/rebuild_test_reference.py
```

The script extracts the positions listed in `evaluation/reference_selection.json` and applies the same normalization. It checks the resulting checksum against the saved reference and writes `reproduced/evaluation_reference/reference.json`, containing 1,200 records in the study's evaluation order.

The index is a recovery mapping for that fixed sample. Where a raw record has equivalent source positions, it selects unused positions in file/document order. The index documents these mappings and the normalization needed to reproduce the reference.

## 3. Generate all 15 tasks

```sh
python -B code/build_dataset/generate_all.py --source reproduced/preprocessing/sentence_xml_pairs.json
```

Output: `reproduced/full_collection/`.

- `sft_tasks/`: 15 JSON files totaling 392,871 instruction examples.
- `generation_report.json`: task counts and consistency checks.
- `generation_stdout.txt` and `generation_stderr.txt`: generator output and diagnostics.

Each task has a generator named `generators/generate_data_<task_name>.py`. For example, `generate_data_overall_1.py` builds the whole-sentence task. `jubenwei_utils.py` supplies symbol definitions, and the helpers under `generators/download_tools/self_explain/` support single-core analysis. The [task catalog](../../task_catalog.json) lists all task names and counts.

The whole-sentence target combines a template-based explanation derived from the reference annotation with the normalized XML. Auxiliary tasks cover symbol definitions, annotation interpretation, lexical and syntactic analysis, and XML checking.

## 4. Construct the training set

```sh
python -B code/build_dataset/select_training_data.py --source reproduced/preprocessing/sentence_xml_pairs.json --reference reproduced/evaluation_reference/reference.json
```

Output: `reproduced/training_instance/`. The study settings use `--per-task 1000` and `--seed 0`.

Records are matched by whitespace-normalized sentence text and canonicalized XML (`strip_text=True`). Each test occurrence consumes one equivalent source occurrence in source order. Subtracting 1,200 test records from 5,016 leaves 3,816 training sources. Tasks are regenerated from this remainder, including the controlled XML perturbations. The 12 corpus-derived auxiliary files are processed in sorted filename order and contribute 1,000 examples each.

| Training input | Records |
|---|---:|
| `integrated_data.json` | 12,000 |
| `learn_tag_1.json` | 54 |
| `learn_tag_2.json` | 53 |
| `overall_1.json` | 3,816 |
| **Total** | **15,923** |

The directory also contains `dataset_info.json`, `training_source.json`, `split_report.json`, `generation_report.json`, and the intermediate `generated_tasks/` directory. These provide loading configuration, the retained sources, construction checks, and the task collection before auxiliary sampling.

## Output options and checks

All commands create a new output directory. Within the resource directory, generated files stay under `reproduced/`. To choose another output location, retain the input paths and change `--output-dir`:

```sh
python -B code/build_dataset/select_training_data.py --source reproduced/preprocessing/sentence_xml_pairs.json --reference reproduced/evaluation_reference/reference.json --output-dir /path/to/new/training_run
```

`--source`, `--reference` (also accepted as `--test`), `--per-task`, and `--seed` allow reuse with another input collection or task quota. Add `--dry-run` to any construction command to inspect its paths and settings without creating output.

Reports record input and output hashes, counts, validation results, and the selection parameters. The test reference plus the remaining source records conserve the original 5,016 records, including their occurrence counts.
