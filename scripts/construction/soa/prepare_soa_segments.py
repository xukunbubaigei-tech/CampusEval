"""Locate SOA question/solution boundaries for visual review and conversion."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / "workspace/extracted/SOA"
DELETED = {123, 234, 235, 236, 271, 272, 273, 275, 276, 277,
           278, 279, 280, 281, 282, 283, 287, 356, 427}


def headings(doc: pymupdf.Document, kind: str) -> list[dict]:
    found = []
    for page_number, page in enumerate(doc):
        if page_number == 0:
            continue
        lines = [line for block in page.get_text("dict")["blocks"]
                 for line in block.get("lines", [])]
        for index, line in enumerate(lines):
            text = "".join(span["text"] for span in line["spans"]).strip()
            if not 60 <= line["bbox"][0] <= 90 or line["bbox"][1] > 735:
                continue
            match = re.match(r"^(\d{1,3})[.,](?:\s|$)", text)
            if not match:
                continue
            number = int(match[1])
            if kind == "solutions":
                rest = text[match.end():].strip()
                if not rest:
                    rest = " ".join(
                        "".join(s["text"] for s in other["spans"])
                        for other in lines[index + 1:index + 4]
                        if abs(other["bbox"][1] - line["bbox"][1]) < 2)
                if not re.match(r"(?:Solution\s*:|Deleted|DELETED|[–-])", rest):
                    continue
            found.append({"number": number, "page": page_number,
                          "top": line["bbox"][1], "heading": text})
    assert all(a["number"] < b["number"] for a, b in zip(found, found[1:])), found
    assert {h["number"] for h in found} >= set(range(1, 738)) - DELETED
    return found


def segments(doc: pymupdf.Document, labels: list[dict]) -> dict[str, list[dict]]:
    result = {}
    for index, heading in enumerate(labels):
        number = heading["number"]
        if number in DELETED:
            continue
        following = labels[index + 1] if index + 1 < len(labels) else {
            "page": len(doc) - 1, "top": 735}
        pieces = []
        for pi in range(heading["page"], following["page"] + 1):
            top = heading["top"] - 3 if pi == heading["page"] else 45
            bottom = following["top"] - 4 if pi == following["page"] else 735
            if bottom <= top:
                continue
            region = pymupdf.Rect(48, top, doc[pi].rect.width - 42, bottom)
            words = [w for w in doc[pi].get_text("words")
                     if pymupdf.Rect(w[:4]).intersects(region) and str(w[4]).strip()]
            if not words:
                continue
            # Keep math glyphs and diagrams in the full vertical interval.
            pieces.append({"page": pi, "rect": list(region)})
        result[str(number)] = pieces
    assert len(result) == 718
    return result


def numeric_options(doc: pymupdf.Document, mapping: dict) -> dict:
    """Recover plain numeric options from native text, leaving complex math to OCR."""
    result = {}
    word_cache = {pi: page.get_text("words") for pi, page in enumerate(doc)}
    for number, pieces in mapping.items():
        labels = []
        for piece in pieces:
            rect = pymupdf.Rect(piece["rect"])
            labels.extend((piece["page"], w) for w in word_cache[piece["page"]]
                          if re.fullmatch(r"\([A-E]\)", w[4]) and rect.y0 <= w[1] <= rect.y1)
        if "".join(w[4][1] for pi, w in labels) != "ABCDE":
            continue
        values = []
        for pi, label in labels:
            center = (label[1] + label[3]) / 2
            words = sorted((w for w in word_cache[pi] if w[0] > label[2] + 3
                            and abs((w[1] + w[3]) / 2 - center) < 2.5), key=lambda w: w[0])
            values.append(" ".join(w[4] for w in words))
        if all(re.fullmatch(r"[\d.,/%+\- ]+", value) for value in values):
            result[number] = values
    return result


if __name__ == "__main__":
    maps = {}
    for kind in ("questions", "solutions"):
        doc = pymupdf.open(WORK / f"exam_p_{kind}.pdf")
        labels = headings(doc, kind)
        maps[kind] = segments(doc, labels)
        if kind == "questions":
            (WORK / "numeric_options.json").write_text(
                json.dumps(numeric_options(doc, maps[kind]), indent=2), encoding="utf-8")
        print(kind, "headings", len(labels), "active", len(maps[kind]),
              "multi-page", sum(len(p) > 1 for p in maps[kind].values()))
    assert maps["questions"].keys() == maps["solutions"].keys()
    (WORK / "segments.json").write_text(json.dumps(maps, indent=2), encoding="utf-8")
