"""Offline integrity checks for the compact canonical release."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()
    root = args.project_root.resolve()
    datasets = root / "datasets"
    manifest = json.loads((datasets / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))

    paths = {
        "benchmark": datasets / "main/benchmark.jsonl",
        "training": datasets / "main/training.jsonl",
        "objective_70": datasets / "objective_70/questions.jsonl",
        "subjective_50": datasets / "subjective_50/questions.jsonl",
        "rubrics": datasets / "subjective_50/rubrics.jsonl",
    }
    for name in ("kaoyan", "MIT", "U-MATH", "SOA"):
        path = datasets / name / "questions.jsonl"
        if path.exists():
            paths[name] = path
    records = {label: read_jsonl(path) for label, path in paths.items()}
    counts = manifest.get("counts", {})
    expected = {
        "benchmark": counts.get("benchmark", len(records["benchmark"])),
        "training": counts.get("training", len(records["training"])),
        "objective_70": counts.get("objective_70", len(records["objective_70"])),
        "subjective_50": counts.get("subjective_50", len(records["subjective_50"])),
        "rubrics": counts.get("approved_rubrics", len(records["rubrics"])),
    }
    for name in paths.keys() - expected.keys():
        expected[name] = counts.get(name, len(records[name]))
    errors: list[str] = []
    dataset_schema = json.loads((root / "schemas/dataset.schema.json").read_text(encoding="utf-8"))
    schema_validator = Draft202012Validator(dataset_schema)
    rubric_schema = json.loads((root / "schemas/subjective_rubric.schema.json").read_text(encoding="utf-8"))
    rubric_validator = Draft202012Validator(rubric_schema)
    for label, count in expected.items():
        if len(records[label]) != count:
            errors.append(f"{label}: expected {count}, got {len(records[label])}")
        key = "question_id" if label == "rubrics" else "id"
        if len({record[key] for record in records[label]}) != count:
            errors.append(f"{label}: duplicate IDs")
        if digest(paths[label]) != manifest["files"][label]["sha256"]:
            errors.append(f"{label}: manifest hash mismatch")
        if label != "rubrics":
            for record in records[label]:
                first_error = next(schema_validator.iter_errors(record), None)
                if first_error is not None:
                    errors.append(f"{label}: schema error for {record.get('id')}: {first_error.message}")
                serialized = json.dumps(record, ensure_ascii=False).lower()
                # Legacy main/mini forbid URLs; imported problem text can
                # legitimately contain a hyperlink. Image paths are checked
                # separately for every dataset below.
                if label in ("benchmark", "training", "objective_70", "subjective_50") and ("http://" in serialized or "https://" in serialized):
                    errors.append(f"{label}: external URL found in {record.get('id')}")

    benchmark = {record["id"]: record for record in records["benchmark"]}
    training = {record["id"]: record for record in records["training"]}
    for label in ("objective_70", "subjective_50"):
        for record in records[label]:
            canonical = benchmark.get(record["id"], training.get(record["id"]))
            if canonical != record:
                errors.append(f"{label}: not canonical: {record['id']}")

    subjective_ids = {record["id"] for record in records["subjective_50"]}
    rubric_ids = {record["question_id"] for record in records["rubrics"]}
    if subjective_ids != rubric_ids:
        errors.append("subjective/rubric ID mismatch")
    for rubric in records["rubrics"]:
        first_error = next(rubric_validator.iter_errors(rubric), None)
        if first_error is not None:
            errors.append(f"rubric schema error for {rubric.get('question_id')}: {first_error.message}")
        if not rubric.get("rubric"):
            errors.append(f"rubric empty text: {rubric.get('question_id')}")
        if not rubric.get("reference_solution_1"):
            errors.append(f"rubric missing solution 1: {rubric.get('question_id')}")
        if "scoring_items" in rubric:
            errors.append(f"rubric still uses old scoring_items: {rubric.get('question_id')}")
        s1 = rubric.get("reference_solution_1")
        s2 = rubric.get("reference_solution_2")
        if s2 is not None and s2 == s1:
            errors.append(f"rubric duplicate solutions: {rubric.get('question_id')}")

    primary = [record for label, group in records.items()
               if label not in ("rubrics", "objective_70", "subjective_50") for record in group]
    if len({r["id"] for r in primary}) != len(primary):
        errors.append("Duplicate IDs across primary datasets")

    def strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, list):
            for child in value:
                yield from strings(child)
        elif isinstance(value, dict):
            for child in value.values():
                yield from strings(child)

    image_refs: set[str] = set()
    for record in [r for group in records.values() for r in group]:
        question = record.get("question", {})
        candidates = list(question.get("images") or [])
        if question.get("image"):
            candidates.append(question["image"])
        image_refs.update(value for value in candidates if isinstance(value, str) and value)
        for text in strings(record):
            image_refs.update(re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text))
    for value in image_refs:
        if not value.startswith("data/images/") or not (root / value).resolve().is_relative_to((root / "data/images").resolve()):
            errors.append(f"Noncanonical or unsafe image path: {value}")
    missing_images = sorted(value for value in image_refs if not (root / value).is_file())
    image_files = {
        path.relative_to(root).as_posix()
        for path in (root / "data/images").rglob("*")
        if path.is_file()
    }
    unreferenced_images = sorted(image_files - image_refs)
    errors.extend(f"missing image: {value}" for value in missing_images)
    errors.extend(f"unreferenced image: {value}" for value in unreferenced_images)
    if counts.get("images") is not None and len(image_files) != counts["images"]:
        errors.append(f"image file count {len(image_files)} != manifest {counts['images']}")

    report = {
        "ok": not errors,
        "counts": {label: len(value) for label, value in records.items()},
        "image_references": len(image_refs),
        "primary_records": len(primary),
        "missing_images": missing_images,
        "unreferenced_images": unreferenced_images,
        "errors": errors,
    }
    report_path = datasets / "VALIDATION_REPORT.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
