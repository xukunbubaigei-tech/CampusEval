"""Deterministically backfill the top-level ``source`` field.

``source`` is derived from the question id prefix, so the migration is
idempotent and fully reproducible. Run from the project root::

    .venv/Scripts/python scripts/archive/migrate_add_source.py

The four canonical datasets (benchmark, training, objective_70,
subjective_50) are updated in place and ``datasets/RELEASE_MANIFEST.json``
hashes/sizes are refreshed. The rubric file is intentionally untouched.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASETS = PROJECT_ROOT / "datasets"

FILES = {
    "benchmark": DATASETS / "main/benchmark.jsonl",
    "training": DATASETS / "main/training.jsonl",
    "objective_70": DATASETS / "objective_70/questions.jsonl",
    "subjective_50": DATASETS / "subjective_50/questions.jsonl",
}

KNOWN_SOURCES = {"gaokao", "conic10k", "aime", "university_exam", "umath", "soa"}


def source_of(record_id: str) -> str:
    if record_id.startswith("soa_p_"):
        return "soa"
    if record_id.startswith("umath_"):
        return "umath"
    if record_id.startswith("gaokao_math_"):
        return "gaokao"
    if record_id.startswith("train_conic10k_") or record_id.startswith("conic10k_"):
        return "conic10k"
    if record_id.startswith("train_"):  # GAOKAO-Bench items are gaokao
        return "gaokao"
    if record_id.startswith("aime_"):
        return "aime"
    if record_id.startswith("university_"):
        return "university_exam"
    raise ValueError(f"Cannot derive source for id: {record_id}")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> int:
    manifest_path = DATASETS / "RELEASE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    ok = True
    for label, path in FILES.items():
        records = read_jsonl(path)
        dist: dict[str, int] = {}
        for record in records:
            src = source_of(record["id"])
            if src not in KNOWN_SOURCES:
                print(f"[FAIL] {label}: unknown source {src} for {record['id']}")
                ok = False
                continue
            record["source"] = src
            dist[src] = dist.get(src, 0) + 1
        write_jsonl(path, records)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        size = path.stat().st_size
        manifest["files"][label]["sha256"] = digest
        manifest["files"][label]["bytes"] = size
        print(f"[OK] {label}: {len(records)} records, sources={dist}")
    if ok:
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("Manifest updated.")
    else:
        print("Aborted manifest update due to unknown sources.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
