"""Import local U-MATH Parquet with reviewed corrections and exclusions.

The golden_answer initializes final_answer before reviewed corrections. The input has no
separate derivation field, so solution is left empty rather than fabricated.
No provenance manifest or conversion report is written.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import re
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq
from jsonschema import Draft202012Validator
from PIL import Image

try:
    from .corrections import curate
except ImportError:  # Direct script execution.
    from corrections import curate

ROOT = Path(__file__).resolve().parents[3]


def build(parquet: Path, license_path: Path, output: Path) -> None:
    rows = pq.read_table(parquet).to_pylist()
    if len(rows) != 1100:
        raise ValueError(f"Expected all 1100 rows, got {len(rows)}")
    license_bytes = license_path.read_bytes()
    if b"MIT License" not in license_bytes or b"Toloka" not in license_bytes:
        raise ValueError("Missing U-MATH license and copyright notice")
    validator = Draft202012Validator(json.loads(
        (ROOT / "schemas/dataset.schema.json").read_text(encoding="utf-8")))
    records, images, seen = [], {}, set()
    for index, row in enumerate(rows, start=1):
        uuid = row["uuid"]
        if not re.fullmatch(r"[0-9a-f-]{36}", uuid) or uuid in seen:
            raise ValueError(f"Invalid or duplicate UUID: {uuid}")
        seen.add(uuid)
        image_refs = []
        image = row["image"]
        if bool(image) != bool(row["has_image"]):
            raise ValueError(f"Inconsistent image flag: {uuid}")
        if image:
            header, encoded = image.split(",", 1)
            if header != "data:image/png;base64":
                raise ValueError(f"Unexpected image encoding: {uuid}: {header}")
            payload = base64.b64decode(encoded, validate=True)
            with Image.open(io.BytesIO(payload)) as picture:
                picture.verify()
            target = ROOT / "data/images/U-MATH" / f"{uuid}.png"
            image_refs.append(target.relative_to(ROOT).as_posix())
            images[target] = payload
        record = {
            "id": f"umath_{index}",
            "source": "umath",
            "question": {"text": row["problem_statement"], "images": image_refs, "options": []},
            "answer": {"final_answer": row["golden_answer"], "solution": ""},
            "metadata": {"paper_name": "umath", "question_type": "解答题"},
        }
        record = curate(record)
        if record is not None:
            validator.validate(record)
            records.append(record)

    # Validate every row and image before publishing; do not silently overwrite edits.
    payload = ("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n").encode("utf-8")
    writes = {output / "questions.jsonl": payload, output / "LICENSE": license_bytes, **images}
    for target, content in writes.items():
        if target.exists() and target.read_bytes() != content:
            raise FileExistsError(f"Existing file differs; refusing to overwrite: {target}")
    for target, content in writes.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(content)

    # Round-trip checks preserve curated records, stable IDs and original image bytes.
    published = [json.loads(line) for line in (output / "questions.jsonl").read_text(encoding="utf-8").splitlines()]
    assert published == records
    assert len(published) == 1099
    assert all(path.read_bytes() == data for path, data in images.items())
    print(json.dumps({"records": len(records), "images": len(images),
                      "subjects": dict(Counter(r["subject"] for r in rows)),
                      "schema_and_round_trip": "passed"}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parquet", type=Path, required=True)
    parser.add_argument("--license", type=Path, required=True)
    args = parser.parse_args()
    build(args.parquet, args.license, ROOT / "datasets/U-MATH")
