"""Aggregation for the plain-text rubric protocol v2.

Supports both single-judge and multi-judge panels through configuration.
Multi-judge disagreement (score range, low confidence, judge-requested
review, incomplete panel) triggers ``needs_human_review``.
"""
from __future__ import annotations

import math
import statistics


def aggregate_judgments(
    judgments: list[dict],
    config: dict | None = None,
    candidate_model: str | None = None,
    expected_judge_count: int | None = None,
) -> dict:
    if not judgments:
        raise ValueError("no judgments to aggregate")
    cfg = config or {}
    thresholds = cfg.get("disagreement", {})
    scores = [float(j["score"]) for j in judgments]
    max_score = float(judgments[0]["max_score"])
    if any(abs(float(j["max_score"]) - max_score) > 1e-9 for j in judgments):
        raise ValueError("judgments disagree on max_score")
    final = statistics.mean(scores)
    score_range = max(scores) - min(scores)

    reasons: list[str] = []
    if expected_judge_count is not None and len(judgments) != expected_judge_count:
        reasons.append("incomplete_judge_panel")
    if max_score > 0 and score_range / max_score > float(thresholds.get("score_range_ratio_threshold", 0.25)):
        reasons.append("score_range_threshold")
    min_confidence = float(thresholds.get("minimum_confidence", 0.6))
    if any(float(j.get("confidence", 0)) < min_confidence for j in judgments):
        reasons.append("low_confidence")
    if thresholds.get("any_judge_requests_review", True) and any(j.get("needs_human_review") for j in judgments):
        reasons.append("judge_requested_review")

    return {
        "question_id": judgments[0]["question_id"],
        "answer_id": judgments[0]["answer_id"],
        "candidate_model": candidate_model,
        "max_score": max_score,
        "final_score": round(final, 6),
        "score_rate": round(final / max_score, 6) if max_score else None,
        "judge_scores": scores,
        "score_range": score_range,
        "needs_human_review": bool(reasons),
        "review_reasons": reasons,
        "judge_details": [
            {
                "judge_slot": j.get("judge_slot"),
                "judge_model": j.get("judge_model"),
                "score": j.get("score"),
                "confidence": j.get("confidence"),
                "needs_human_review": j.get("needs_human_review"),
            }
            for j in judgments
        ],
    }


def summary(rows: list[dict]) -> dict:
    count = len(rows)
    max_total = sum(float(r["max_score"]) for r in rows)
    earned = sum(float(r["final_score"]) for r in rows)
    return {
        "answers": count,
        "average_score_rate": earned / max_total if max_total else None,
        "full_score_rate": sum(math.isclose(r["final_score"], r["max_score"], abs_tol=1e-9) for r in rows) / count if count else None,
        "human_review_rate": sum(bool(r["needs_human_review"]) for r in rows) / count if count else None,
        "judge_consistency": {
            "mean_score_range_ratio": (sum(r["score_range"] / r["max_score"] for r in rows) / count if count else None)
        },
        "by_question": {
            r["question_id"]: {"score_rate": r["score_rate"], "needs_human_review": r["needs_human_review"]}
            for r in rows
        },
    }
