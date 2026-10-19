"""Crop original PDF figures from the locally rendered page inventory."""
import json
import re
from pathlib import Path
from PIL import Image

WORK = Path(__file__).resolve().parents[3] / "workspace/extracted/kaoyan/precise"


def main():
    jobs = json.loads((WORK / "figure_jobs.rendered.json").read_text(encoding="utf-8-sig"))
    root = WORK.parents[3]
    records = [json.loads(line) for line in (root / 'datasets/kaoyan/questions.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    used = {ref for r in records for ref in r['question']['images']}
    for record in records:
        used.update(re.findall(r'!\[[^\]]*\]\(([^)]+)\)', record['answer']['solution']))
    saved = 0
    for job in jobs:
        with Image.open(job["rendered_page"]) as page:
            sx = page.width / job["page_size"][0]
            sy = page.height / job["page_size"][1]
            x0, y0, x1, y1 = job["bbox"]
            box = (max(0, int(x0*sx)-5), max(0, int(y0*sy)-5),
                   min(page.width, int(x1*sx)+5), min(page.height, int(y1*sy)+5))
            target = Path(job["target"])
            if "assets" in target.parts:
                target = root / "data/images/kaoyan" / target.name
            if target.resolve().relative_to(root).as_posix() not in used:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            page.crop(box).save(target)
            saved += 1
    print(f"Saved {saved} referenced original PDF figures")


if __name__ == "__main__":
    main()
