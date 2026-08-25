"""Regenerate the 70/50 mini datasets from the canonical main JSONL files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def main() -> int:
    benchmark = {record["id"]: record for record in read_jsonl(ROOT / "datasets/main/benchmark.jsonl")}
    training = {record["id"]: record for record in read_jsonl(ROOT / "datasets/main/training.jsonl")}
    all_records = benchmark | training
    for name in ("objective_70", "subjective_50"):
        folder = ROOT / "datasets" / name
        ids = json.loads((folder / "ids.json").read_text(encoding="utf-8"))
        missing = [record_id for record_id in ids if record_id not in all_records]
        if missing:
            raise ValueError(f"{name} IDs absent from main datasets: {missing}")
        write_jsonl(folder / "questions.jsonl", [all_records[record_id] for record_id in ids])
        print(f"{name}: {len(ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
