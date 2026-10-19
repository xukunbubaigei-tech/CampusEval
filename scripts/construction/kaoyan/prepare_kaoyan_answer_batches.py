"""Prepare reversible upload batches; preserve annual page provenance."""
import hashlib
import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "CampusEval/workspace/extracted/kaoyan/precise"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = next(ROOT.glob("考研*/【1】*/01-*/答案解析"))
    files = sorted(source.glob("*.pdf"))
    files = [p for p in files if not p.name.startswith("2023")]
    manifest = []
    for i in range(0, len(files), 12):
        group = files[i:i + 12]
        writer = PdfWriter()
        entries = []
        for pdf in group:
            reader = PdfReader(pdf)
            start = len(writer.pages) + 1
            writer.append(reader)
            entries.append({"year": int(pdf.name[:4]), "source_file": str(pdf),
                            "start_page": start, "end_page": len(writer.pages),
                            "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest()})
        name = f"answers_{group[0].name[:4]}_{group[-1].name[:4]}.pdf"
        target = OUT / name
        writer.write(target)
        manifest.append({"file": str(target), "pages": len(writer.pages),
                         "annual_sources": entries})
    (OUT / "answer_batches.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    for item in manifest:
        print(item["file"], item["pages"])


if __name__ == "__main__":
    main()
