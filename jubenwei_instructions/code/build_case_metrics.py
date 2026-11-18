"""Rebuild case-level metric counts from the public instruction and output ZIPs."""
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import sys
from zipfile import ZipFile

import metrics
from aggregate_metrics import COUNT_FIELDS, DIAGNOSTIC_FIELDS, METRICS, aggregate, csv_text, micro_f1
from reference_from_tasks import RESOURCE, load_pairs, recover_reference
from rescore_release import read_outputs
from scoring import evaluate_outputs

F1_KEYS = ("separated_f1", "pos_f1", "dynamic_f1", "grammar_f1")


def check_equal(actual, expected, label):
    if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12):
        raise AssertionError(f"Metric mismatch: {label}")


def case_metrics(reference, output, case_id, condition):
    """Return numeric diagnostics; never include the reference or answer text."""
    score = evaluate_outputs([reference], [output])
    valid = int(score["valid"] == 1)
    row = {"case_id": case_id, "condition": condition,
           "xml_parsable": valid,
           "text_consistent": int(not score["text_mismatches"]) if valid else "",
           "f1_eligible": valid, "structure_comparable": score["structure_evaluated"],
           "structure_exact": score["structure_correct"],
           **{field: "" for field in COUNT_FIELDS}}
    if valid:
        tokens, gold_xml, pred_xml = [reference[0]], [reference[1]], [output]
        counts = {
            "segmentation": metrics.compute_separated_word_F1(tokens, gold_xml, pred_xml, return_counts=True),
            "pos": metrics.compute_pos_F1(tokens, gold_xml, pred_xml, return_counts=True),
            "dynamic": metrics.compute_dynamic_word_F1(tokens, gold_xml, pred_xml, return_counts=True),
            "syntax": metrics.compute_grammar_F1(gold_xml, pred_xml, "text", return_counts=True),
        }
        for metric, source_key in zip(METRICS, F1_KEYS):
            for part, count in zip(("tp", "fp", "fn"), counts[metric]):
                row[f"{metric}_{part}"] = count
            check_equal(micro_f1(*counts[metric]), score[source_key], f"{condition}/{case_id}/{metric}")
    return row


def build_case_metrics(dataset, outputs_zip):
    """Read public inputs, preserve all failed outputs, and verify aggregate scores."""
    metadata = json.loads((RESOURCE / "evaluation/conditions.json").read_bytes())
    manifest = json.loads((RESOURCE / "evaluation/outputs_manifest.json").read_bytes())
    if sha256(outputs_zip.read_bytes()).hexdigest() != manifest["sha256"]:
        raise ValueError("Output ZIP checksum differs from outputs_manifest.json")
    reference = recover_reference(load_pairs(dataset))
    members = {member["condition"]: member for member in manifest["conditions"]}
    conditions = metadata["conditions"]
    if len(members) != len(manifest["conditions"]) or set(members) != {c["id"] for c in conditions}:
        raise ValueError("Condition metadata and output manifest do not match")

    rows, source_scores = [], {}
    with ZipFile(outputs_zip) as archive:
        for condition in conditions:
            cid = condition["id"]
            outputs = read_outputs(archive, members[cid])
            source_scores[cid] = evaluate_outputs(reference, outputs)
            for position, (ref, output) in enumerate(zip(reference, outputs), 1):
                rows.append(case_metrics(ref, output, f"T{position:04d}", cid))
            print(f"Checked {cid}: {len(outputs)} cases", file=sys.stderr)

    summary, totals = aggregate(rows, metadata)
    for row in summary:
        cid = row["condition"]
        original, counts = source_scores[cid], totals[cid]
        for metric, source_key in zip(METRICS, F1_KEYS):
            check_equal(micro_f1(*(counts[f"{metric}_{part}"] for part in ("tp", "fp", "fn"))),
                        original[source_key], f"{cid}/{metric}")
        for field, source_key in {"n_inputs": "total", "n_xml_parsable": "valid",
                                  "n_xml_unparsable": "invalid", "n_structure_comparable": "structure_evaluated",
                                  "n_structure_exact": "structure_correct"}.items():
            if int(row[field]) != original[source_key]:
                raise AssertionError(f"Count mismatch: {cid}/{field}")
        if int(row["n_text_inconsistent"]) != len(original["text_mismatches"]):
            raise AssertionError(f"Text-consistency mismatch: {cid}")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, type=Path,
                        help="Public instruction-data ZIP, or extracted sft_tasks/overall_1.json")
    parser.add_argument("--outputs", required=True, type=Path, help="Public model-output ZIP")
    parser.add_argument("--output", type=Path, help="Write diagnostics to a new CSV file")
    parser.add_argument("--check", type=Path, nargs="?",
                        const=RESOURCE / "evaluation/per_case_metrics.csv",
                        help="Compare byte for byte; defaults to evaluation/per_case_metrics.csv")
    args = parser.parse_args()
    if args.output and args.output.exists():
        raise FileExistsError(f"Refusing to overwrite {args.output}")
    rows = build_case_metrics(args.dataset, args.outputs)
    text = csv_text(rows, DIAGNOSTIC_FIELDS)
    if args.check and text.encode("utf-8") != args.check.read_bytes():
        raise AssertionError("Rebuilt diagnostics differ from the supplied CSV")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8", newline="") as handle:
            handle.write(text)
    if args.check:
        print(json.dumps({"status": "passed", "diagnostic_records": len(rows),
                          "conditions": len({r["condition"] for r in rows}), "byte_equal": True}))
    elif not args.output:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
