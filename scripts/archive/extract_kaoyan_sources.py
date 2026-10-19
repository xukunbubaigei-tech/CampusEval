"""Resumable MinerU extraction of the explicitly selected local Math I PDFs.

Intermediate extraction only: this script never publishes dataset records.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / "CampusEval/workspace/extracted/kaoyan"
BASE = "https://mineru.net/api/v1/agent"


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def run_one(key: str, pdf: Path) -> dict:
    folder = WORK / key
    folder.mkdir(parents=True, exist_ok=True)
    md_path = folder / "document.md"
    state_path = folder / "task.private.json"
    if md_path.exists() and (folder / "receipt.json").exists():
        print(f"{key}: cached", flush=True)
        return {"key": key, "state": "cached"}
    session = requests.Session()
    if state_path.exists():
        task = json.loads(state_path.read_text(encoding="utf-8"))
    else:
        options = {"file_name": key + ".pdf", "language": "ch", "enable_table": True,
                   "is_ocr": True, "enable_formula": True}
        response = session.post(BASE + "/parse/file", json=options, timeout=90)
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") != 0:
            raise RuntimeError(f"{key}: submission rejected: {payload.get('msg')}")
        task = {**payload["data"], "uploaded": False, "options": options}
        save(state_path, task)
    if not task.get("uploaded"):
        with pdf.open("rb") as handle:
            response = session.put(task["file_url"], data=handle, timeout=300)
        response.raise_for_status()
        task["uploaded"] = True
        save(state_path, task)
        print(f"{key}: uploaded", flush=True)
    deadline = time.monotonic() + 2400
    previous = None
    while time.monotonic() < deadline:
        response = session.get(BASE + "/parse/" + task["task_id"], timeout=90)
        response.raise_for_status()
        status = response.json()
        data = status.get("data", {})
        state = data.get("state")
        if state != previous:
            print(f"{key}: {state}", flush=True)
            previous = state
        if state == "failed":
            save(folder / "failure.json", status)
            raise RuntimeError(f"{key}: MinerU failed; see failure.json")
        if state == "done":
            response = session.get(data["markdown_url"], timeout=180)
            response.raise_for_status()
            md_path.write_text(response.content.decode("utf-8"), encoding="utf-8")
            save(folder / "receipt.json", {"source_file": str(pdf),
                 "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
                 "task_id": task["task_id"], "options": task.get("options"),
                 "final_status": status})
            print(f"{key}: saved {md_path.stat().st_size} bytes", flush=True)
            return {"key": key, "state": "done"}
        time.sleep(5)
    raise TimeoutError(f"{key}: unfinished; task id saved for resume")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["pilot", "all", "answers"], default="pilot")
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    source_root = next(ROOT.glob("考研*/【1】*/01-*"))
    questions = next(source_root.glob("【合集】*.pdf"))
    answers = sorted((source_root / "答案解析").glob("*.pdf"))
    jobs = []
    if args.mode != "answers":
        parts = sorted((WORK / "question_parts").glob("questions_p*.pdf"))
        if not parts:
            raise SystemExit("Split the question collection into files below 10MB first")
        jobs.extend((pdf.stem, pdf) for pdf in parts)
    for pdf in answers:
        if args.mode != "pilot" or pdf.name.startswith("2023"):
            jobs.append(("answers_" + pdf.name[:4], pdf))
    WORK.mkdir(parents=True, exist_ok=True)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_one, *job): job[0] for job in jobs}
        for future in concurrent.futures.as_completed(futures):
            key = futures[future]
            try:
                results.append(future.result())
            except Exception as exc:
                results.append({"key": key, "state": "error", "error": str(exc)})
                print(f"{key}: ERROR {exc}", flush=True)
    save(WORK / (args.mode + "_run.json"), {"results": results})
    if any(x["state"] == "error" for x in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
