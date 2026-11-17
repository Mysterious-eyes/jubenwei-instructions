# Formal data construction workflow

`select_training_data.py` is the **official training-instance construction entry point**. It subtracts the fixed reference records by multiplicity, regenerates tasks from every remaining record, and samples auxiliary tasks. It does not apply additional repeated-text or shared-clause exclusion. The complete task collection is a separate research resource, not a second training-selection route.

All data-building scripts use the Python standard library. Run the commands below from the release root. Relative data paths are resolved against that root, so the scripts can also be launched by their full paths from another working directory.

## Construction stages

### 1. Extract and normalize the source annotations

```text
python -B code/build_dataset/preprocess.py
```

Default input: `source_annotations/`.

Default output: `reproduced/preprocessing/`:

- `extracted_pairs.json`: each source `ju` serialized with its original attributes and paired with its text.
- `sentence_xml_pairs.json`: the same pairs retaining only `scp`, `fun` and `mod`, with formatting whitespace normalized.
- `preprocess_report.json`: counts and source/output hashes.

The 27 XML files produce 5,016 sentence pairs. Filename order and document-order sentence traversal are preserved; records are not deduplicated.

### 2. Recover the fixed reference sample

```text
python -B code/build_dataset/rebuild_test_reference.py
```

This uses `evaluation/reference_selection.json` to write `reproduced/evaluation_reference/reference.json`, matching the archived 1,200-record reference byte for byte. The index is a recovery mapping, not the historical random draw or an inferred seed. For 109 records with indistinguishable source positions, it chooses unused equivalent positions in file/document order; the other 1,091 locations are unique within their source groups.

### 3. Generate the complete 15-task collection

```text
python -B code/build_dataset/generate_all.py --source reproduced/preprocessing/sentence_xml_pairs.json
```

Default output: `reproduced/full_collection/`, containing `sft_tasks/`, `generation_report.json` and generation logs. This produces and validates all 15 task files, totaling 392,871 instruction records. Each generator retains the project's task logic and language templates. `generation_paths.py` supplies independent input/output locations.

### 4. Construct the formal training instance

```text
python -B code/build_dataset/select_training_data.py --source reproduced/preprocessing/sentence_xml_pairs.json --reference reproduced/evaluation_reference/reference.json
```

The reference defaults to `evaluation/reference.json`; the output defaults to `reproduced/training_instance/`. The official settings use record-multiplicity subtraction, `--per-task 1000` and `--seed 0`.

The matching key is the whitespace-normalized sentence together with canonicalized XML (`strip_text=True`). Every reference occurrence consumes one equivalent source occurrence in source order; records with the same text but different annotations remain distinct keys. All remaining duplicate occurrences and shared-clause records are retained. Exactly 1,200 records are deducted from 5,016, leaving 3,816. All tasks are regenerated from that remainder; the 12 corpus-derived auxiliary task files are processed in sorted filename order and each contributes 1,000 records. The main task and both dictionary tasks are preserved in full for this instance.

| Training file | Records |
|---|---:|
| `integrated_data.json` | 12,000 |
| `learn_tag_1.json` | 54 |
| `learn_tag_2.json` | 53 |
| `overall_1.json` | 3,816 |
| Total | 15,923 |

The output also includes `training_source.json`, `split_report.json`, `dataset_info.json`, `generation_report.json` and the intermediate `generated_tasks/` directory. Source/audit files and intermediate tasks are not additional training inputs. The public entry point publishes the two static dictionary files alongside the corpus-derived files so that all four configured training inputs are present.

Controlled XML perturbations are regenerated after record subtraction. Therefore the training instance is not defined as an exact row subset of every complete task file. The source-record multiset is conserved: reference records plus remaining records equal the original source, including multiplicity.

## Independent output locations

All entry points refuse an existing output directory. Within the release, outputs must stay under `reproduced/`. To use a different independent location:

```text
python -B code/build_dataset/select_training_data.py --output-dir /path/to/new/training_run
```

`--source`, `--reference` (also accepted as `--test`), `--per-task` and `--seed` are available for reuse. The documented defaults define the archived training instance. `--dry-run` reports the selected paths and settings without creating outputs.

No entry point overwrites `source_annotations/`, `normalized/`, `sft_tasks/`, `training_instance/` or the saved evaluation files. No training or model inference is performed by this workflow.

## Archived validation

The complete data archive retains reproduction reports and file checksums. The code repository provides the construction entry points and source-position index; the source corpus and archived data must be acquired separately. All task-generation and selection algorithms are retained, including the single-core analysis helpers under `generators/`.
