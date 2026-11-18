"""Recompute reported metrics from text-free per-case counts (standard library only)."""
import argparse
import csv
import io
import json
import re
import sys
from pathlib import Path

RESOURCE = Path(__file__).resolve().parents[1]
METRICS = ("segmentation", "pos", "dynamic", "syntax")
COUNT_FIELDS = tuple(f"{metric}_{part}" for metric in METRICS for part in ("tp", "fp", "fn"))
DIAGNOSTIC_FIELDS = (
    "case_id", "condition", "xml_parsable", "text_consistent", "f1_eligible",
    "structure_comparable", "structure_exact", *COUNT_FIELDS,
)
SUMMARY_FIELDS = (
    "condition", "model", "project_sft", "thinking_mode", "n_inputs",
    "n_xml_parsable", "n_xml_unparsable", "n_text_consistent", "n_text_inconsistent",
    "n_f1_scored", "n_structure_comparable", "n_structure_exact",
    "xml_parsable_pct", "text_consistent_pct_all",
    "segmentation_f1_pct", "pos_f1_pct", "dynamic_f1_pct", "syntax_f1_pct",
    "structure_exact_pct_comparable", "structure_exact_pct_all",
)


def bool_value(value, field):
    value = str(value).strip()
    if value not in {"0", "1"}:
        raise ValueError(f"{field} must be 0 or 1")
    return int(value)


def count_value(value, field):
    value = str(value).strip()
    if not re.fullmatch(r"\d+", value):
        raise ValueError(f"{field} must be a nonnegative integer")
    return int(value)


def micro_f1(tp, fp, fn):
    denominator = 2 * tp + fp + fn
    return 2 * tp / denominator if denominator else 0.0


def percentage(numerator, denominator):
    return f"{100 * numerator / denominator:.2f}" if denominator else ""


def read_csv(path, fields):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != tuple(fields):
            raise ValueError(f"Unexpected columns in {Path(path).name}")
        return list(reader)


def csv_text(rows, fields):
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue()


def aggregate(rows, metadata):
    """Validate the record roster and aggregate sufficient statistics by condition."""
    conditions = metadata["conditions"]
    ids = [item["id"] for item in conditions]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate condition IDs")
    groups = {}
    for item in conditions:
        groups[item["id"]] = {
            "cases": set(), "n_inputs": 0, "n_xml_parsable": 0,
            "n_text_consistent": 0, "n_f1_scored": 0,
            "n_structure_comparable": 0, "n_structure_exact": 0,
            **{field: 0 for field in COUNT_FIELDS},
        }
    for row_number, row in enumerate(rows, 1):
        if set(row) != set(DIAGNOSTIC_FIELDS):
            raise ValueError(f"Unexpected fields at diagnostic row {row_number}")
        condition = row["condition"]
        if condition not in groups:
            raise ValueError(f"Unknown condition at diagnostic row {row_number}")
        group = groups[condition]
        case = row["case_id"]
        if not re.fullmatch(r"T\d{4}", case) or case in group["cases"]:
            raise ValueError(f"Invalid or duplicate case ID at diagnostic row {row_number}")
        group["cases"].add(case)
        parsable = bool_value(row["xml_parsable"], "xml_parsable")
        eligible = bool_value(row["f1_eligible"], "f1_eligible")
        comparable = bool_value(row["structure_comparable"], "structure_comparable")
        exact = bool_value(row["structure_exact"], "structure_exact")
        if eligible != parsable or comparable > parsable or exact > comparable:
            raise ValueError(f"Inconsistent eligibility flags at diagnostic row {row_number}")
        if parsable:
            consistent = bool_value(row["text_consistent"], "text_consistent")
            for field in COUNT_FIELDS:
                group[field] += count_value(row[field], field)
        else:
            if row["text_consistent"] != "" or any(row[field] != "" for field in COUNT_FIELDS):
                raise ValueError(f"Excluded F1/text fields must be blank at diagnostic row {row_number}")
            consistent = 0
        group["n_inputs"] += 1
        group["n_xml_parsable"] += parsable
        group["n_text_consistent"] += consistent
        group["n_f1_scored"] += eligible
        group["n_structure_comparable"] += comparable
        group["n_structure_exact"] += exact

    summary, totals = [], {}
    for item in conditions:
        condition = item["id"]
        group = groups[condition]
        expected_cases = {f"T{i:04d}" for i in range(1, item["records"] + 1)}
        if group["cases"] != expected_cases:
            raise ValueError(f"Incomplete case roster for {condition}")
        total = group["n_inputs"]
        valid = group["n_xml_parsable"]
        values = {
            "condition": condition, "model": item["model"],
            "project_sft": "1" if item["task_sft"] else "0",
            "thinking_mode": "on" if item.get("thinking_enabled") is True else "off" if item.get("thinking_enabled") is False else "not_applicable",
            "n_inputs": str(total), "n_xml_parsable": str(valid),
            "n_xml_unparsable": str(total - valid),
            "n_text_consistent": str(group["n_text_consistent"]),
            "n_text_inconsistent": str(valid - group["n_text_consistent"]),
            "n_f1_scored": str(group["n_f1_scored"]),
            "n_structure_comparable": str(group["n_structure_comparable"]),
            "n_structure_exact": str(group["n_structure_exact"]),
            "xml_parsable_pct": percentage(valid, total),
            "text_consistent_pct_all": percentage(group["n_text_consistent"], total),
            "structure_exact_pct_comparable": percentage(group["n_structure_exact"], group["n_structure_comparable"]),
            "structure_exact_pct_all": percentage(group["n_structure_exact"], total),
        }
        for metric in METRICS:
            f1 = micro_f1(*(group[f"{metric}_{part}"] for part in ("tp", "fp", "fn")))
            values[f"{metric}_f1_pct"] = f"{100 * f1:.2f}" if group["n_f1_scored"] else ""
        summary.append(values)
        totals[condition] = {k: v for k, v in group.items() if k != "cases"}
    return summary, totals


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagnostics", type=Path, default=RESOURCE / "evaluation" / "per_case_metrics.csv")
    parser.add_argument("--conditions", type=Path, default=RESOURCE / "evaluation" / "conditions.json")
    parser.add_argument("--check", type=Path, nargs="?", const=RESOURCE / "evaluation" / "summary.csv",
                        help="Compare with a saved summary CSV; defaults to evaluation/summary.csv")
    parser.add_argument("--output", type=Path, help="Write recomputed summary to a new file")
    args = parser.parse_args()
    metadata = json.loads(args.conditions.read_text(encoding="utf-8-sig"))
    rows = read_csv(args.diagnostics, DIAGNOSTIC_FIELDS)
    summary, _ = aggregate(rows, metadata)
    if args.check:
        expected = read_csv(args.check, SUMMARY_FIELDS)
        if summary != expected:
            raise ValueError("Recomputed summary does not match the supplied summary CSV")
    if args.output:
        with args.output.open("x", encoding="utf-8", newline="") as handle:
            handle.write(csv_text(summary, SUMMARY_FIELDS))
    if args.check:
        print(json.dumps({"status": "passed", "conditions": len(summary), "diagnostic_records": len(rows)}))
    elif not args.output:
        sys.stdout.write(csv_text(summary, SUMMARY_FIELDS))


if __name__ == "__main__":
    main()
