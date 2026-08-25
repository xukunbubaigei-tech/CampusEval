"""Blindly score pre-existing candidate-answer JSONL under protocol v2.

The judge only sees the question, the plain-text rubric, the two reference
solutions and the candidate answer (no candidate identity, no other judges,
no rubric generator metadata, no historical results).

Dry-run performs no network requests. All new runs write under ``runs/`` and
never overwrite ``reports/``.

Run::

    .venv/Scripts/python scripts/evaluate_subjective_answers.py \\
        --answers runs/subjective/answers.jsonl --dry-run
    .venv/Scripts/python scripts/evaluate_subjective_answers.py \\
        --answers runs/subjective/answers.jsonl --execute \\
        --base-url "$SUBJECTIVE_LLM_BASE_URL"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT.parent) not in sys.path:  # parent dir exposes the gaokao_math_benchmark package
    sys.path.insert(0, str(ROOT.parent))

import requests

from gaokao_math_benchmark.subjective.client import chat_completion
from gaokao_math_benchmark.subjective.common import classify_error, ensure_run_output_dir, load_api_key
from gaokao_math_benchmark.subjective.io_utils import append_jsonl, extract_json_object, latest_by_key, read_jsonl
from gaokao_math_benchmark.subjective.prompts import judge_prompt, load_few_shots
from gaokao_math_benchmark.subjective.validation import validate_judgment

DEFAULT_MAX_SCORE = 20.0  # unified experimental scale per project decision


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--answers", type=Path, required=True, help="JSONL: answer_id, question_id, answer, candidate_model")
    parser.add_argument("--questions", type=Path, default=ROOT / "datasets/subjective_50/questions.jsonl")
    parser.add_argument("--rubrics", type=Path, default=ROOT / "datasets/subjective_50/rubrics.jsonl")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "runs/subjective/judgments")
    parser.add_argument("--config", type=Path, default=ROOT / "configs/subjective_evaluation.json")
    parser.add_argument("--base-url", default=os.getenv("SUBJECTIVE_LLM_BASE_URL", ""))
    parser.add_argument("--api-key-env", default="SUBJECTIVE_LLM_API_KEY")
    parser.add_argument("--judge-mode", choices=["single", "three"], default=None, help="override config default_judge_mode")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--question-id", action="append", default=[])
    parser.add_argument("--retries", type=int, default=2, help="retries after the first attempt for request/parse/validation failures")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="print plan, make zero network requests")
    mode.add_argument("--execute", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    judge_mode = args.judge_mode or cfg.get("default_judge_mode", "three")
    if judge_mode not in ("single", "three"):
        raise SystemExit(f"invalid judge_mode: {judge_mode}")

    answers = read_jsonl(args.answers)
    if args.question_id:
        wanted = set(args.question_id)
        answers = [r for r in answers if r["question_id"] in wanted]
    answers = answers[args.offset:]
    if args.limit is not None:
        answers = answers[: args.limit]

    questions = {r["id"]: r for r in read_jsonl(args.questions)}
    rubrics = {r["question_id"]: r for r in read_jsonl(args.rubrics)}
    subjective_ids = set(questions)

    all_judges = [j for j in cfg.get("judges", []) if not str(j.get("model", "")).startswith("CONFIGURE_ME")]
    panel = all_judges if judge_mode == "three" else all_judges[:1]
    missing = sorted({r["question_id"] for r in answers} - set(rubrics))
    usable = [r for r in answers if r["question_id"] in rubrics]
    report = {
        "protocol_version": cfg.get("protocol_version"),
        "judge_mode": judge_mode,
        "answers": len(answers),
        "usable": len(usable),
        "missing_rubric_ids": missing,
        "panel": [j["slot"] for j in panel],
        "planned_requests": len(usable) * len(panel),
        "network_requests": 0,
    }
    args.output_dir = ensure_run_output_dir(args.output_dir, ROOT)
    (args.output_dir / "preflight_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.dry_run:
        return 0
    if missing:
        raise SystemExit("all answers require a rubric")
    if not panel:
        raise SystemExit("configure at least one judge slot before --execute")
    if not args.base_url:
        raise SystemExit("base URL required")
    api_key = load_api_key(args.api_key_env)

    few_shots = load_few_shots(ROOT / cfg["few_shot_file"])
    out = args.output_dir / "judgments.jsonl"
    existing = latest_by_key(read_jsonl(out) if out.exists() else [], ("answer_id", "judge_slot"))
    session = requests.Session()

    for answer in answers:
        rubric = rubrics[answer["question_id"]]
        question_text = questions[answer["question_id"]]["question"]["text"]
        for judge in panel:
            key = (answer["answer_id"], judge["slot"])
            if key in existing:
                continue
            prompt = judge_prompt(question_text, rubric, answer["answer"], few_shots)
            completed = False
            errors: list[str] = []
            for attempt in range(1, args.retries + 2):
                raw = ""
                usage: dict = {}
                latency = 0.0
                try:
                    raw, usage, latency = chat_completion(
                        session, args.base_url, api_key, judge["model"], prompt,
                        max_tokens=int(judge.get("max_tokens", 8192)),
                        enable_thinking=judge.get("enable_thinking"),
                        thinking_budget=judge.get("thinking_budget"),
                        reasoning_effort=judge.get("reasoning_effort"),
                    )
                    record = extract_json_object(raw)
                    record.update({
                        "question_id": answer["question_id"],
                        "answer_id": answer["answer_id"],
                        "judge_slot": judge["slot"],
                        "judge_model": judge["model"],
                        "prompt_version": cfg.get("judge_prompt_version", "judge_blind_zh_v1"),
                    })
                    errors = validate_judgment(record, subjective_ids=subjective_ids,
                                               expected_max_score=DEFAULT_MAX_SCORE, config=cfg)
                except Exception as exc:  # noqa: BLE001 - surface any failure for retry bookkeeping
                    errors = [classify_error(exc)]
                append_jsonl(args.output_dir / "raw_responses.jsonl", {
                    "answer_id": answer["answer_id"], "question_id": answer["question_id"],
                    "judge_slot": judge["slot"], "judge_model": judge["model"],
                    "attempt": attempt, "raw_response": raw, "usage": usage,
                    "latency_seconds": latency, "validation_errors": errors,
                })
                if not errors:
                    append_jsonl(out, record)
                    existing[key] = record
                    completed = True
                    break
                if attempt <= args.retries:
                    time.sleep(min(2 ** (attempt - 1), 4))
            if not completed:
                append_jsonl(args.output_dir / "failures.jsonl", {
                    "answer_id": answer["answer_id"], "question_id": answer["question_id"],
                    "judge_slot": judge["slot"], "judge_model": judge["model"],
                    "attempts": args.retries + 1, "errors": errors,
                })
    return 0


if __name__ == "__main__":
    sys.exit(main())
