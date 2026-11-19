# Build the instruction dataset

The workflow constructs the full 15-task collection and the training set used in the study. `select_training_data.py` excludes **every source record whose whole-sentence text matches a test sentence after whitespace removal**, regenerates tasks from all remaining records, and samples auxiliary tasks. Punctuation and case are preserved. XML differences do not prevent exclusion; duplicates within the retained training sources and sentences that share only a clause are kept.

Use Python 3.10 or later. All construction scripts use the standard library. Run the examples from `jubenwei_instructions/`, the resource directory inside the repository. Relative data paths are resolved against this directory.

The input is the 27 source XML files described on the [LDC2025T06 page](https://catalog.ldc.upenn.edu/LDC2025T06). Place them in `source_annotations/`. The repository's `evaluation/reference_selection.json` records the source filenames, sentence positions, and hashes used for the fixed reference. See the [main README](../../../README.md) for data access and repository layout.

The precomputed full collection is also available in [release v1.0.0](https://github.com/Mysterious-eyes/jubenwei-instructions/releases/download/v1.0.0/jubenwei-instructions-data-v1.0.0.zip). That ZIP contains the 15 task files; the steps below reconstruct the full collection, fixed reference, and training set from the source XML.

The [Zenodo dataset](https://doi.org/10.5281/zenodo.24343396) also provides the 5,016 whole-sentence XML targets. To reconstruct the exact test reference and training set directly from the published ZIP, run from the resource directory:

```sh
python -B code/reference_from_tasks.py --dataset /path/to/jubenwei-instructions-data-v1.0.0.zip --source-pairs
python -B code/build_dataset/select_training_data.py --source reproduced/public_reference/sentence_xml_pairs.json --reference reproduced/public_reference/reference.json
```

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

### Draw a new grouped test sample

Use this separate entry point when designing a new split:

```sh
python -B code/build_dataset/sample_test_records.py --seed 42 --output-dir reproduced/new_test_sample
```

The grouping and sampling rule is: filenames ending in `-<digits>.xml` belong to the same prefix group; each larger group contributes `--per-group 200` sentence records sampled without replacement, and a group with at most 200 records is retained in full. For the supplied corpus, the six groups each contribute 200 records, totaling 1,200. Sampling acts on raw `ju` occurrences before XML normalization and retains the draw order within each group.

The entry point sorts groups and filenames and accepts an optional `--seed`. Repeating a seed with the same source files and Python environment reproduces the new sample; omitting it draws a fresh sample. This creates a new sample rather than recovering the paper's fixed test set. Use `rebuild_test_reference.py` above for that set.

The new output directory contains:

- `sampled_pairs.json`: selected sentence text and original serialized XML, before normalization.
- `reference.json`: the same selected records with normalized XML retaining `scp`, `fun` and `mod`.
- `sentences.txt`: one selected sentence per line for model inference.
- `sampling_index.json`: seed, group counts, source-file checksums, and each selected record's source filename, `ju` position, group/source index and output order. Its output checksums identify the three data files.

`--source-dir` accepts another XML directory; `--per-group` changes the quota. Source files are read only, output within the source directory is rejected, and existing output directories are never overwritten. For a new training split, pass this `reference.json` to `select_training_data.py --reference`; do not substitute it when rescoring the paper's archived predictions.

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

The fixed 1,200-record reference contains 1,100 distinct whole-sentence texts after whitespace removal. The study rule excludes all 1,381 matching records from the 5,016 source records, leaving 3,635 training sources in their original order. The reference remains a 1,200-record collection; it is not deduplicated. Only membership of the normalized whole-sentence text is used for exclusion. Other repeated training sentences and shared clauses are retained.

Tasks are regenerated from the 3,635 retained records, including controlled XML perturbations. The 12 corpus-derived auxiliary files are processed in sorted filename order and contribute 1,000 examples each. The two static dictionary files are retained in full. Together the four files contain the 15,742 examples used for training.

| Training input | Records |
|---|---:|
| `integrated_data.json` | 12,000 |
| `learn_tag_1.json` | 54 |
| `learn_tag_2.json` | 53 |
| `overall_1.json` | 3,635 |
| **Total** | **15,742** |

The directory also contains `dataset_info.json`, `training_source.json`, `split_report.json`, `generation_report.json`, and the intermediate `generated_tasks/` directory. These provide loading configuration, the retained sources, construction checks, and the task collection before auxiliary sampling.

## Output options and checks

All commands create a new output directory. Within the resource directory, generated files stay under `reproduced/`. To choose another output location, retain the input paths and change `--output-dir`:

```sh
python -B code/build_dataset/select_training_data.py --source reproduced/preprocessing/sentence_xml_pairs.json --reference reproduced/evaluation_reference/reference.json --output-dir /path/to/new/training_run
```

`--source`, `--reference` (also accepted as `--test`), `--per-task`, and `--seed` allow reuse with another input collection or task quota. Add `--dry-run` to `select_training_data.py` to inspect its paths and settings without creating output.

Reports record input/output hashes, task counts, selected and excluded source indices, the named selection policy, and whole-sentence and shared-clause diagnostics. The conservation check is **3,635 retained + 1,381 excluded = 5,016 source records**. It is not a sum of retained records and the 1,200 test occurrences. The retained whole-sentence/test-text intersection must be empty; the shared-clause diagnostic is not used to remove records.

Check an independently constructed training directory without requiring a complete study archive:

```sh
python -B code/verify_release.py --training-dir reproduced/training_instance --source reproduced/public_reference/sentence_xml_pairs.json --reference reproduced/public_reference/reference.json --expect-selection-policy exclude_all_matching_test_sentences
```

Use the source/reference paths from the construction command if you followed the XML preprocessing route instead. If the complete task files have also been extracted, add `--symbol-dir sft_tasks` to compare the two dictionary files with that independent copy. Training-only verification checks its report, source indices, exclusion rule, all four training inputs and recorded hashes. It is reported separately from complete-archive manifest verification.

## Regression checks

```sh
python -B -m unittest discover -s code/build_dataset -p test_selection_rules.py
```

The checks exercise sentence matching, annotation-independent exclusion, retained duplicates, shared clauses and report consistency. Construction and verification run offline and do not train or query a model.
