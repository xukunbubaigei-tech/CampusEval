"""Validate that curated formal evaluation reports are readable and complete."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def jsonl_count(path: Path) -> int:
    count = 0
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if line.strip():
            json.loads(line)
            count += 1
    return count


def main() -> int:
    reports = ROOT / "reports"
    errors: list[str] = []
    parsed_files = 0
    for path in reports.rglob("*.json"):
        if path.name == "VALIDATION_REPORT.json":
            continue
        try:
            json.loads(path.read_text(encoding="utf-8-sig"))
            parsed_files += 1
        except Exception as exc:
            errors.append(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    for path in reports.rglob("*.jsonl"):
        try:
            jsonl_count(path)
            parsed_files += 1
        except Exception as exc:
            errors.append(f"invalid JSONL {path.relative_to(ROOT)}: {exc}")

    base = reports / "subjective/qwen3.6-35b-a3b"
    expected_counts = {
        base / "answers.jsonl": 50,
        base / "three_judges/judgments.jsonl": 150,
        base / "three_judges/aggregate/aggregated_scores.jsonl": 50,
        base / "thinking_pilot/judgments.jsonl": 30,
        base / "thinking_pilot/aggregate/aggregated_scores.jsonl": 10,
    }
    actual_counts: dict[str, int | None] = {}
    for path, expected in expected_counts.items():
        relative = str(path.relative_to(ROOT)).replace("\\", "/")
        if not path.is_file():
            errors.append(f"missing formal report file: {relative}")
            actual_counts[relative] = None
            continue
        actual = jsonl_count(path)
        actual_counts[relative] = actual
        if actual != expected:
            errors.append(f"{relative}: expected {expected}, got {actual}")

    objective_runs = [path for path in (reports / "objective").iterdir() if path.is_dir()]
    for run in objective_runs:
        if not any((run / name).is_file() for name in ("rescored_results.jsonl", "results.jsonl")):
            errors.append(f"objective run has no per-question results: {run.name}")

    report = {
        "ok": not errors,
        "objective_run_directories": len(objective_runs),
        "json_files_parsed": parsed_files,
        "subjective_counts": actual_counts,
        "errors": errors,
    }
    output = reports / "VALIDATION_REPORT.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
