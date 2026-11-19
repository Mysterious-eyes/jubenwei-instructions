# Evaluation of sentence annotation

All six conditions used the same 1,200 test records in the same order. The trained checkpoints used 15,742 examples under whole-sentence text exclusion. Release v1.1.0 corrects the earlier training-set reconstruction. The prediction files and their scores are those archived in validation-v1.0.0. Test IDs run from `T0001` through `T1200`. They link the model answers, diagnostics and reference records. The condition IDs and model settings are in [conditions.json](conditions.json).

The experimenter confirmed that all six conditions, including both Qwen2.5 conditions, used the same [system prompt](../code/inference/qwen3_shared_system_prompt.txt). It specifies the SPS annotation conventions and includes two annotated sentence examples, followed by the sentence-specific request in the user message. The file's original name is retained. The clients in [v1.1.1](https://github.com/Mysterious-eyes/jubenwei-instructions/releases/tag/v1.1.1) now share that default prompt. This update does not replace the archived predictions or scores; configurable client defaults are not used to infer the decoding settings of the original runs.

| File | Contents |
|---|---|
| [summary.csv](summary.csv) | Six rows with counts, four micro-F1 scores, and structural match rates for Table 10 and Figure 7. |
| [per_case_metrics.csv](per_case_metrics.csv) | One row per test case and condition. Includes eligibility flags and the TP, FP and FN counts for each component score. |
| [scores/](scores/) | Six original text score reports. |
| [Model answers ZIP](https://github.com/Mysterious-eyes/jubenwei-instructions/releases/download/validation-v1.0.0/model-outputs-v1.0.0.zip) · [file checksums](outputs_manifest.json) | Six UTF-8 JSONL files under `outputs/`. Each row contains the `case_id` and the exact final `output` string read by the scorer, including malformed and empty answers. |
| [reference_selection.json](reference_selection.json) | Source positions for the fixed test set and the SHA-256 of the ordered reference. |

### Recompute from model outputs

Run from `jubenwei_instructions/` with the [instruction ZIP](https://doi.org/10.5281/zenodo.24343396) and [model answers ZIP](https://github.com/Mysterious-eyes/jubenwei-instructions/releases/tag/validation-v1.0.0).

```sh
python -B code/rescore_release.py --dataset /path/to/jubenwei-instructions-data-v1.0.0.zip --outputs /path/to/model-outputs-v1.0.0.zip --check
```

The default output, without `--check`, is a six-row CSV. The reference XML is recovered from the final answers in `sft_tasks/overall_1.json` using the original test indices. The reference records and each condition’s model outputs are verified by SHA-256 before scoring. To write the reference and the ordered sentences for inference:

```sh
python -B code/reference_from_tasks.py --dataset /path/to/jubenwei-instructions-data-v1.0.0.zip
```

### Read the metrics

- **XML parsability** counts well-formed final answers. **Text fidelity** compares the concatenated text fragments with the reference sentence in XML order. The two percentages shown in Figure 7a–b use 1,200 as the denominator.
- **Segmentation, POS and dynamic-word F1** use character-aligned units. **Syntactic F1** matches fragment-text/tag pairs within each sentence, including repeated pairs. For each condition, counts are pooled over its parsable outputs, including text mismatches. Micro-F1 is calculated as `2 × TP / (2 × TP + FP + FN)`.
- **Structural agreement** compares linear expressions regenerated from reference and output XML. The conditional rate uses the number of comparable pairs. The all-input rate counts exact matches out of 1,200. Every parsable output in this experiment could be converted. Generated explanation text is outside the scoring target.

For an unparsable answer, `text_consistent` and the twelve F1 count fields are empty in the case-level CSV. Its `structure_exact` flag is zero for the all-input rate. Rates are reported in percent to two decimal places.

### Check the per-case scores

From the resource directory, aggregate the checked-in counts:

```sh
python -B code/aggregate_metrics.py --check evaluation/summary.csv
```

To derive the 7,200 diagnostic rows again from the released answers and compare them with the CSV:

```sh
python -B code/build_case_metrics.py --dataset /path/to/jubenwei-instructions-data-v1.0.0.zip --outputs /path/to/model-outputs-v1.0.0.zip --check
```
