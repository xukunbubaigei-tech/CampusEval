"""Validate the complete SOA batch against the schema and native PDF answer key."""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

import pymupdf
from jsonschema import Draft202012Validator

import runpy

ROOT = Path(__file__).resolve().parents[2]
DELETED = runpy.run_path(str(ROOT / "scripts/construction/soa/prepare_soa_segments.py"))["DELETED"]


def validate(path: Path) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 718
    validator = Draft202012Validator(json.loads((ROOT / "schemas/dataset.schema.json").read_text(encoding="utf-8")))
    pdf = pymupdf.open(ROOT / "workspace/extracted/SOA/exam_p_solutions.pdf")
    original = "\n".join(page.get_text() for page in pdf)
    key = {int(m[1]): m[2] for m in re.finditer(r"(?m)^\s*(\d{1,3})\.\s*Solution\s*:\s*([A-E])\b", original)
           if int(m[1]) not in DELETED}
    assert len(key) == 718
    assert len({row["question"]["text"] for row in rows}) == 718
    for index, (number, row) in enumerate(zip(sorted(key), rows), 1):
        validator.validate(row)
        assert row["id"] == f"soa_p_{index}"
        assert row["source"] == "soa"
        assert row["metadata"]["question_type"] == "选择题"
        assert row["question"]["images"] == []
        assert row["answer"]["final_answer"] == key[number], number
        assert row["answer"]["solution"].strip(), number
        options = row["question"]["options"]
        assert [o["label"] for o in options] == list("ABCDE"), number
        compact = lambda text: re.sub(r"\s+", "", text)
        assert len({compact(o["text"]) for o in options}) == 5, (number, "Duplicate option text")
        last_line = row["question"]["text"].strip().splitlines()[-1]
        assert not any(compact(last_line) == compact(f"({o['label']}) {o['text']}")
                       for o in options), (number, "Option duplicated at end of question")
        fields = [row["question"]["text"], row["answer"]["solution"]] + [o["text"] for o in options]
        for text in fields:
            assert text.strip() and "[VISUAL:" not in text, number
            assert not re.search(r"</?(?:sup|sub)\b", text, re.I), (number, "Unconverted HTML superscript/subscript")
            assert not any(c == "\ufffd" or unicodedata.category(c) == "Co"
                           or (unicodedata.category(c) == "Cc" and c not in "\n\r\t")
                           for c in text), (number, "Replacement/private-use/control character")
            assert "http://" not in text and "https://" not in text, number
            assert text.count("$") % 2 == 0, number
            assert len(re.findall(r"(?<!\\)\{", text)) == len(re.findall(r"(?<!\\)\}", text)), number
    print("Passed: 718 sequential IDs, unique questions, five options each, 718 official answer matches, nonempty textual solutions, schema and delimiters.")
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=ROOT / "datasets/SOA/questions.jsonl")
    args = parser.parse_args()
    validate(args.path)
