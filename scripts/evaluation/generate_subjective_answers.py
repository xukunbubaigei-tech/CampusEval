"""Generate full worked answers for a subjective JSONL dataset."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

from CampusEval.subjective.common import (classify_error, ensure_run_output_dir,
                                                     is_image_support_error, load_api_key,
                                                     multimodal_content)
from CampusEval.subjective.io_utils import append_jsonl, latest_by_key, read_jsonl, write_json

DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def prompt(record: dict) -> str:
    return (
        "请独立解答下面的高中数学主观题。必须给出完整、清晰、可评分的推导过程和最终结论；"
        "不要引用参考答案，也不要省略关键步骤。\n\n题目：\n" + record["question"]["text"]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=ROOT / "datasets/subjective_50/questions.jsonl")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "runs/subjective/candidate_answers")
    parser.add_argument("--model", default="qwen3.5-27b")
    parser.add_argument("--base-url", default=os.getenv("SUBJECTIVE_LLM_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--api-key-env", default="DASHSCOPE_API_KEY")
    parser.add_argument("--modality", choices=["auto", "text-only", "multimodal"], default="auto")
    parser.add_argument("--max-tokens", type=int, default=8192)
    parser.add_argument("--temperature", type=float, default=0)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--no-thinking", action="store_true", help="Request direct answer mode for providers supporting enable_thinking.")
    parser.add_argument(
        "--reasoning-effort",
        choices=["none", "low", "medium", "high", "xhigh", "max"],
        help="Reasoning strength for providers supporting reasoning_effort.",
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument("--offset", type=int, default=0)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    args.output_dir = ensure_run_output_dir(args.output_dir, ROOT)
    rows = read_jsonl(args.dataset)
    rows = rows[args.offset:]
    if args.limit is not None:
        rows = rows[:args.limit]
    image_rows = [row for row in rows if row.get("question", {}).get("images")]
    text_rows = [row for row in rows if not row.get("question", {}).get("images")]
    planned = text_rows if args.modality == "text-only" else rows
    preflight = {
        "model": args.model, "dataset_records": len(rows), "text_only_records": len(text_rows),
        "image_records": len(image_rows), "modality": args.modality, "planned_records": len(planned),
        "network_requests": 0 if args.dry_run else None,
        "note": "auto processes text first and probes the first image record; clear unsupported-input errors exclude all image records.",
    }
    write_json(args.output_dir / "preflight_report.json", preflight)
    if args.dry_run:
        print(json.dumps(preflight, ensure_ascii=False, indent=2)); return
    api_key = load_api_key(args.api_key_env)
    answers_path = args.output_dir / "answers.jsonl"
    failures_path = args.output_dir / "failures.jsonl"
    existing = latest_by_key(read_jsonl(answers_path) if answers_path.exists() else [], ("answer_id",))
    session = requests.Session()
    ordered = text_rows + image_rows if args.modality == "auto" else planned
    image_supported: bool | None = None
    for row in ordered:
        answer_id = f"{args.model}:{row['id']}"
        if (answer_id,) in existing:
            continue
        has_image = bool(row.get("question", {}).get("images"))
        if has_image and args.modality == "auto" and image_supported is False:
            continue
        started = time.perf_counter(); error = None
        for attempt in range(1, args.retries + 1):
            try:
                response = session.post(
                    args.base_url.rstrip("/") + "/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={"model": args.model, "messages": [{"role": "user", "content": multimodal_content(
                        prompt(row), row.get("question", {}).get("images", []) if has_image else [], ROOT, args.dataset)}],
                          "temperature": args.temperature, "max_tokens": args.max_tokens,
                          **({"enable_thinking": False} if args.no_thinking else {}),
                          **({"reasoning_effort": args.reasoning_effort} if args.reasoning_effort else {})},
                          timeout=args.timeout,
                )
                response.raise_for_status(); payload = response.json(); answer = payload["choices"][0]["message"]["content"]
                append_jsonl(answers_path, {"answer_id": answer_id, "question_id": row["id"], "candidate_model": args.model,
                                            "answer": answer, "usage": payload.get("usage", {}),
                                            "latency_seconds": round(time.perf_counter()-started, 3), "has_image": has_image})
                if has_image: image_supported = True
                error = None; break
            except (requests.RequestException, KeyError, ValueError) as exc:
                error = classify_error(exc)
                if has_image and args.modality == "auto" and is_image_support_error(exc):
                    image_supported = False; break
                if attempt < args.retries: time.sleep(attempt * 2)
        if error:
            append_jsonl(failures_path, {"question_id": row["id"], "has_image": has_image, "error": error})
    write_json(args.output_dir / "modality_report.json", {
        "requested_mode": args.modality, "image_supported": image_supported,
        "excluded_image_ids": [row["id"] for row in image_rows] if image_supported is False else [],
    })


if __name__ == "__main__":
    main()
