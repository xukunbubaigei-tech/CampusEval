from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def latest_by_key(rows: Iterable[dict], keys: tuple[str, ...]) -> dict[tuple, dict]:
    result: dict[tuple, dict] = {}
    for row in rows:
        result[tuple(row.get(key) for key in keys)] = row
    return result


def canonical_hash(payload: object) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def rubric_source_hash(question_id: str, question: str, final_answer: str, solution: str, max_score: float) -> str:
    return canonical_hash({
        "question_id": question_id,
        "question": question,
        "final_answer": final_answer,
        "solution": solution,
        "max_score": max_score,
    })


def extract_json_object(text: str) -> dict:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        stripped = "\n".join(lines[1:-1]).strip()
    decoder = json.JSONDecoder()
    starts = [i for i, char in enumerate(stripped) if char == "{"]
    for start in starts:
        try:
            value, _ = decoder.raw_decode(stripped[start:])
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            continue
    raise ValueError("response does not contain a JSON object")

