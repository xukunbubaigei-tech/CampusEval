"""Aggregate protocol-v2 judgments into per-answer scores and summary.

Reads the judgments JSONL produced by ``evaluate_subjective_answers.py``,
validates every judgment against the v2 schema + business rules, groups by
answer, aggregates (single or three-judge per config), and writes summary /
disagreement / human-review artifacts into the output directory.

Run::

    .venv/Scripts/python scripts/evaluation/aggregate_subjective_scores.py \\
        --answers runs/subjective/answers.jsonl \\
        --judgments runs/subjective/judgments/judgments.jsonl \\
        --output-dir runs/subjective/aggregated
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT.parent) not in sys.path:  # parent dir exposes the CampusEval package
    sys.path.insert(0, str(ROOT.parent))

from CampusEval.subjective.aggregation import aggregate_judgments, summary
from CampusEval.subjective.common import ensure_run_output_dir, latency_total, usage_summary
from CampusEval.subjective.io_utils import read_jsonl, write_json
from CampusEval.subjective.validation import validate_judgment

DEFAULT_MAX_SCORE = 20.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--answers", type=Path, required=True)
    parser.add_argument("--judgments", type=Path, required=True)
    parser.add_argument("--rubrics", type=Path, default=ROOT / "datasets/subjective_50/rubrics.jsonl")
    parser.add_argument("--raw-responses", type=Path)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/subjective_evaluation.json")
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    answers = {r["answer_id"]: r for r in read_jsonl(args.answers)}
    rubric_ids = {r["question_id"] for r in read_jsonl(args.rubrics)}
    judge_mode = cfg.get("default_judge_mode", "three")
    configured = [j for j in cfg.get("judges", []) if not str(j.get("model", "")).startswith("CONFIGURE_ME")]
    expected_judge_count = len(configured) if judge_mode == "three" else 1

    groups: dict[str, list[dict]] = defaultdict(list)
    invalid: list[dict] = []
    for judgment in read_jsonl(args.judgments):
        errors = validate_judgment(judgment, subjective_ids=rubric_ids,
                                   expected_max_score=DEFAULT_MAX_SCORE, config=cfg)
        if errors:
            invalid.append({"answer_id": judgment.get("answer_id"),
                            "judge_slot": judgment.get("judge_slot"),
                            "question_id": judgment.get("question_id"), "errors": errors})
        else:
            groups[judgment["answer_id"]].append(judgment)

    rows = []
    for answer_id, judgments in groups.items():
        answer = answers[answer_id]
        rows.append(aggregate_judgments(
            judgments, cfg,
            candidate_model=answer.get("candidate_model"),
            expected_judge_count=expected_judge_count,
        ))

    raw_path = args.raw_responses or args.judgments.with_name("raw_responses.jsonl")
    raw = read_jsonl(raw_path) if raw_path.exists() else []
    usage = usage_summary(raw)
    latency = latency_total(raw)

    args.output_dir = ensure_run_output_dir(args.output_dir, ROOT)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "aggregated_scores.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
    )
    write_json(args.output_dir / "summary.json", {
        **summary(rows), "usage": usage, "latency_seconds": round(latency, 3),
        "estimated_cost": None,
        "cost_note": "Token usage is measured; configure verified model pricing before estimating cost.",
    })
    flagged = [row for row in rows if row["needs_human_review"]]
    write_json(args.output_dir / "disagreement_report.json", {"flagged": len(flagged), "records": flagged})
    write_json(args.output_dir / "human_review_queue.json", {
        "records": [{"answer_id": row["answer_id"], "question_id": row["question_id"],
                     "reasons": row["review_reasons"], "status": "pending"} for row in flagged]
    })
    write_json(args.output_dir / "invalid_judgments.json", {"records": invalid})
    print(json.dumps({
        "aggregated": len(rows), "invalid_judgments": len(invalid),
        "flagged": len(flagged), "usage": usage, "latency_seconds": round(latency, 3),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
