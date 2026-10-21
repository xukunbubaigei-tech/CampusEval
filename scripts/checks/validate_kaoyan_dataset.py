"""Validate the standalone kaoyan import without changing main/mini datasets."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import jsonschema

BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "datasets/kaoyan"


def unbalanced_math_groups(text):
    bad = []
    for formula in re.findall(r"\$([^$]+)\$", text):
        count = 0
        for i, char in enumerate(formula):
            if char not in "{}":
                continue
            j = i-1
            while j >= 0 and formula[j] == "\\":
                j -= 1
            if (i-j-1) % 2:
                continue
            count += 1 if char == "{" else -1
        if count:
            bad.append(formula[:180])
    return bad


def main():
    raw = (DATA / "questions.jsonl").read_bytes()
    records = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line]
    schema = json.loads((BASE / "schemas/dataset.schema.json").read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    errors, ids, texts, assets = [], set(), set(), set()
    for r in records:
        errors.extend(f"{r['id']}: {e.message}" for e in validator.iter_errors(r))
        if r["id"] in ids:
            errors.append(f"Duplicate ID: {r['id']}")
        ids.add(r["id"])
        text = re.sub(r"\s+", "", r["question"]["text"])
        if text in texts:
            errors.append(f"Duplicate question text: {r['id']}")
        texts.add(text)
        if r["metadata"]["question_type"] == "选择题":
            labels = [o["label"] for o in r["question"]["options"]]
            final = r["answer"]["final_answer"]
            if labels != ["A", "B", "C", "D"] or not final or any(c not in labels for c in final) or len(set(final)) != len(final):
                errors.append(f"Invalid MCQ options/answer: {r['id']}")
            if any(not o["text"].strip() for o in r["question"]["options"]):
                errors.append(f"Empty MCQ option without graphic mapping: {r['id']}")
        paths = r["question"]["images"][:]
        for field in r["answer"].values():
            paths += re.findall(r"!\[[^]]*\]\(([^)]+)\)", field)
        for path in paths:
            assets.add(path)
            if not (BASE / path).is_file():
                errors.append(f"Missing image: {path}")
        for field in [r["question"]["text"], *r["answer"].values(), *[o["text"] for o in r["question"]["options"]]]:
            if "\ufffd" in field or field.count("$") % 2:
                errors.append(f"Broken OCR character or math delimiter: {r['id']}")
            if unbalanced_math_groups(field):
                errors.append(f"Unbalanced math braces: {r['id']}: {unbalanced_math_groups(field)}")
    pending_path = DATA / "pending_review.jsonl"
    pending = [json.loads(line) for line in pending_path.read_text(encoding="utf-8").splitlines() if line.strip()] if pending_path.exists() else []
    pending_ids = {p["record"]["id"] for p in pending}
    if ids & pending_ids or len(pending_ids) != len(pending):
        errors.append("Published and pending IDs overlap, or pending IDs repeat")
    report = {"passed": not errors, "records": len(records), "pending": len(pending),
              "referenced_images": len(assets), "empty_solutions": sum(not r["answer"]["solution"] for r in records),
              "questions_sha256": hashlib.sha256(raw).hexdigest(),
              "checks": ["JSON Schema", "unique IDs", "exact-text deduplication", "MCQ answer-label agreement",
                         "local image references", "math delimiter and brace balance", "published/pending separation"],
              "not_verified": "逐题公式转写准确性与数学正确性", "errors": errors}
    report_path = BASE / "workspace/reports/kaoyan_validation.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
