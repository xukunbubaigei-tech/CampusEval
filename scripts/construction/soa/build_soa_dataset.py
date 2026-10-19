"""Convert downloaded MinerU JSON into SOA question records in staging.

Original PDF boundaries and answer letters independently anchor OCR pairing.
This script does not publish until all conversion issues have been resolved.
"""
from __future__ import annotations

import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / "workspace/extracted/SOA"
STAGING = ROOT / "workspace/staging/SOA"


def math_text(value: str) -> str:
    value = re.sub(r"(?<=\d)\s*\.\s*(?=\d)", ".", value)
    value = re.sub(r"(?<=\d)\s+(?=\d)", "", value)
    return value.strip()


def table_text(value: str) -> str:
    value = re.sub(r"<eq>(.*?)</eq>", lambda m: "$" + math_text(m[1]) + "$", value, flags=re.S)
    soup = BeautifulSoup(value, "html.parser")
    grid = {}
    for ri, tr in enumerate(soup.find_all("tr")):
        ci = 0
        for cell in tr.find_all(["td", "th"], recursive=False):
            while (ri, ci) in grid:
                ci += 1
            text = cell.get_text(" ", strip=True).replace("|", r"\vert")
            for dr in range(int(cell.get("rowspan", 1))):
                for dc in range(int(cell.get("colspan", 1))):
                    grid[ri + dr, ci + dc] = text if dr == dc == 0 else ""
            ci += int(cell.get("colspan", 1))
    rows = [[grid.get((ri, ci), "") for ci in range(max(c for r, c in grid) + 1)]
            for ri in range(max(r for r, c in grid) + 1)] if grid else []
    if not rows:
        raise ValueError("Empty table")
    width = max(map(len, rows))
    rows = [row + [""] * (width - len(row)) for row in rows]
    return "\n".join(["| " + " | ".join(rows[0]) + " |", "| " + " | ".join(["---"] * width) + " |"]
                     + ["| " + " | ".join(row) + " |" for row in rows[1:]])


def leaf_lines(block: dict):
    if block.get("blocks"):
        for child in block["blocks"]:
            yield from leaf_lines(child)
    else:
        for line in block.get("lines", []):
            texts = []
            for span in line.get("spans", []):
                typ = span.get("type")
                value = span.get("content", "")
                if typ == "inline_equation":
                    texts.append("$" + math_text(value) + "$")
                elif typ == "interline_equation":
                    texts.append("$$\n" + math_text(value) + "\n$$")
                elif typ == "table":
                    texts.append("\n" + table_text(span["html"]) + "\n")
                elif typ in {"image", "chart"}:
                    texts.append(f"[VISUAL:{typ}:{','.join(map(str, span['bbox']))}]")
                else:
                    texts.append(html.unescape(value))
            if texts:
                yield line["bbox"], " ".join(texts).strip()


def read_segments() -> tuple[dict, dict]:
    segments = json.loads((WORK / "segments.json").read_text(encoding="utf-8"))
    result = {kind: defaultdict(list) for kind in segments}
    for kind in segments:
        page_regions = defaultdict(list)
        for number, pieces in segments[kind].items():
            for piece in pieces:
                page_regions[piece["page"]].append((number, piece["rect"][1], piece["rect"][3]))
        files = sorted(WORK.glob(f"MinerU_SOA_{kind}_*.json"))
        if len(files) != 2:
            raise ValueError(f"Expected two precise JSON files for {kind}, got {len(files)}")
        pages_seen = set()
        for file in files:
            start, end = map(int, re.search(r"_(\d{3})_(\d{3})__", file.name).groups())
            data = json.loads(file.read_text(encoding="utf-8"))
            assert len(data["pdf_info"]) == end - start + 1
            for page in data["pdf_info"]:
                pi = page["page_idx"] + start - 1
                assert pi not in pages_seen
                pages_seen.add(pi)
                for block in page["preproc_blocks"]:
                    for bbox, text in leaf_lines(block):
                        center = bbox[1] + 1
                        for number, top, bottom in page_regions[pi]:
                            if top <= center <= bottom:
                                result[kind][number].append(text)
                                break
        assert len(pages_seen) == (300 if kind == "questions" else 211)
    return {kind: {n: "\n".join(lines).strip() for n, lines in values.items()}
            for kind, values in result.items()}, segments


def convert() -> None:
    STAGING.mkdir(parents=True, exist_ok=True)
    extracted, segments = read_segments()
    key = json.loads((WORK / "answer_key.json").read_text())
    corrections_path = ROOT / "scripts/curation/soa/soa_corrections.json"
    corrections = json.loads(corrections_path.read_text(encoding="utf-8")) if corrections_path.exists() else {}
    numeric_options = json.loads((WORK / "numeric_options.json").read_text(encoding="utf-8"))
    records, issues = [], []
    debug = {}
    for index, number in enumerate(sorted(key, key=int), 1):
        override = corrections.get(number, {})
        q = extracted["questions"][number]
        s = extracted["solutions"][number]
        # OCR occasionally attaches the next question's introduction to an option.
        for foreign in re.finditer(r"(?m)^\s*(\d{1,3})[.,]\s+[A-Za-z]", q):
            if int(number) < int(foreign[1]) <= int(number) + 3:
                q = q[:foreign.start()].strip()
                break
        q = re.sub(r"^\s*" + number + r"[.,]?\s*", "", q)
        solution_header = re.match(r"^\s*" + number + r"[.,]?\s*Solution\s*:\s*([A-E])\b\s*", s, re.I)
        if solution_header:
            if solution_header[1] != key[number]:
                issues.append([number, "OCR answer disagrees with original PDF", solution_header[1], key[number]])
            s = s[solution_header.end():].strip()
        elif "solution" not in override:
            issues.append([number, "solution heading not recognized", s[:80]])
        debug[number] = {"question": q, "solution": s}
        q = override.get("question", q)
        s = override.get("solution", s)
        # Start at a line-leading A label, ignoring event names such as (B) in prose.
        first_option = re.search(r"(?m)^\s*\(A\)", q)
        if first_option:
            # Keep match offsets absolute for slicing.
            candidates = list(re.compile(r"\(([A-E])\)").finditer(q, first_option.start()))[:5]
        else:
            candidates = []
        if "options" in override or number in numeric_options:
            body = override.get("body", q[:first_option.start()].strip() if first_option else q)
            values = override.get("options", numeric_options.get(number))
            options = [{"label": letter, "text": value} for letter, value in zip("ABCDE", values)]
            option_matches = None
        else:
            option_matches = candidates
        if option_matches is None:
            pass
        elif [m[1] for m in option_matches] != list("ABCDE"):
            issues.append([number, "option labels", [m[1] for m in option_matches]])
            options = []
            body = q
        else:
            body = q[:option_matches[0].start()].strip()
            options = [{"label": m[1], "text": q[m.end():option_matches[i + 1].start()
                        if i + 1 < len(option_matches) else len(q)].strip()}
                       for i, m in enumerate(option_matches)]
        body = override.get("body", body)
        body = re.split(r"\n\|\s*\(A\)\s*\|", body, maxsplit=1)[0].strip()
        record = {"id": f"soa_p_{index}", "source": "soa",
                  "question": {"text": body, "images": [], "options": options},
                  "answer": {"final_answer": key[number], "solution": s},
                  "metadata": {"paper_name": "SOA Exam P Sample Questions", "question_type": "选择题"}}
        for label, text in [("question", body), ("solution", s)] + [(o["label"], o["text"]) for o in options]:
            if not text:
                issues.append([number, label, "empty"])
            if "[VISUAL:" in text:
                issues.append([number, label, "visual needs transcription", text])
            if text.count("$") % 2:
                issues.append([number, label, "unbalanced math delimiters"])
        records.append(record)
    assert len(records) == 718
    (STAGING / "questions.jsonl").write_bytes(("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n").encode("utf-8"))
    (WORK / "converted_debug.json").write_text(json.dumps(debug, ensure_ascii=False, indent=2), encoding="utf-8")
    (WORK / "conversion_issues.json").write_text(json.dumps(issues, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Records:", len(records), "Issues:", len(issues), dict(Counter(i[1] for i in issues)))


if __name__ == "__main__":
    convert()
