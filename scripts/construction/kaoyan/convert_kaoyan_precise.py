"""Convert saved MinerU webpage JSON to local, page-addressable intermediates.

This step preserves OCR text and never claims mathematical verification.
"""
from __future__ import annotations
import json
import re
import html
from collections import Counter
from pathlib import Path

WORK = Path(__file__).resolve().parents[3] / "workspace/extracted/kaoyan/precise"


def span_text(span):
    content = span.get("content", "")
    if span.get("type") == "table":
        raw = re.sub(r"<eq>(.*?)</eq>", r"$\1$", span.get("html", ""), flags=re.S)
        rows = []
        for row in re.findall(r"<tr[^>]*>(.*?)</tr>", raw, flags=re.S):
            cells = [html.unescape(re.sub(r"<[^>]+>", "", c))
                     for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, flags=re.S)]
            rows.append(" | ".join(cells))
        return "\n".join(rows)
    if span.get("type") in {"inline_equation", "interline_equation"}:
        return " $" + content.strip() + "$ "
    return content


def block_text(block):
    if block.get("blocks"):
        return "\n".join(block_text(b) for b in block["blocks"])
    return "\n".join("".join(span_text(s) for s in line.get("spans", []))
                     for line in block.get("lines", []))


def convert(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    pages = []
    for page in data["pdf_info"]:
        blocks = [{"type": b["type"], "bbox": b.get("bbox"),
                   "text": block_text(b), "raw": b}
                  for b in page.get("para_blocks", [])]
        pages.append({"page": page["page_idx"] + 1,
                      "page_size": page["page_size"], "blocks": blocks})
    path.with_suffix(".pages.json").write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
    path.with_suffix(".md").write_text("\n\n".join(
        f"<!-- PDF_PAGE {p['page']} -->\n\n" + "\n\n".join(
            ("## " if b["type"] == "title" else "") + b["text"] for b in p["blocks"])
        for p in pages), encoding="utf-8")
    print(path.name, len(pages), dict(Counter(b["type"] for p in pages for b in p["blocks"])))


def main():
    manifest_path = WORK / "answer_batches.json"
    if manifest_path.exists():
        for batch in json.loads(manifest_path.read_text(encoding="utf-8")):
            path = WORK / (Path(batch["file"]).stem + ".json")
            if not path.exists():
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            assert len(data["pdf_info"]) == batch["pages"], path
            for item in batch["annual_sources"]:
                pages = data["pdf_info"][item["start_page"] - 1:item["end_page"]]
                pages = [dict(page, page_idx=i) for i, page in enumerate(pages)]
                annual = {k: v for k, v in data.items() if k != "pdf_info"}
                annual["pdf_info"] = pages
                (WORK / f"answers_{item['year']}.json").write_text(
                    json.dumps(annual, ensure_ascii=False), encoding="utf-8")
    for path in sorted(WORK.glob("*.json")):
        if path.name == "answer_batches.json" or ".pages." in path.name:
            continue
        convert(path)


if __name__ == "__main__":
    main()
