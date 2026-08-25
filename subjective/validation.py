"""Validation for the plain-text rubric protocol v2.

- ``validate_rubric`` checks the three-field plain-text rubric schema.
- ``validate_judgment`` checks the new holistic judgment schema plus business
  rules: numeric score within [0, max_score], non-empty reason, question_id
  belonging to the subjective set, unified max_score, and automatic human
  review flags for high-score-with-serious-errors / low confidence.
"""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]

SERIOUS_ERROR_MARKERS = ("概念", "逻辑", "推理", "conceptual", "logical", "unsupported_claim")


def validate_schema(instance: dict, schema_name: str) -> list[str]:
    schema = json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    return [f"{'/'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
            for error in sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))]


def validate_rubric(rubric: dict) -> list[str]:
    errors = validate_schema(rubric, "subjective_rubric.schema.json")
    if not rubric.get("rubric"):
        errors.append("rubric text is empty")
    if not rubric.get("reference_solution_1"):
        errors.append("reference_solution_1 is empty")
    return errors


def _has_serious_error(errors: list[str]) -> bool:
    return any(marker in error.lower() for error in errors for marker in SERIOUS_ERROR_MARKERS)


def validate_judgment(
    judgment: dict,
    subjective_ids: set[str] | None = None,
    expected_max_score: float | None = None,
    config: dict | None = None,
) -> list[str]:
    errors = validate_schema(judgment, "subjective_judgment.schema.json")
    score = judgment.get("score")
    max_score = judgment.get("max_score")
    if not isinstance(score, (int, float)) or isinstance(score, bool):
        errors.append("score must be numeric")
        return errors
    if not isinstance(max_score, (int, float)) or isinstance(max_score, bool):
        errors.append("max_score must be numeric")
        return errors
    score_f, max_f = float(score), float(max_score)
    if not (0 <= score_f <= max_f):
        errors.append(f"score {score:g} outside [0, {max_f:g}]")
    if expected_max_score is not None and abs(max_f - float(expected_max_score)) > 1e-9:
        errors.append(f"max_score {max_f:g} != expected {expected_max_score:g}")
    if not judgment.get("reason"):
        errors.append("reason is empty")
    if subjective_ids is not None and judgment.get("question_id") not in subjective_ids:
        errors.append(f"unknown question_id: {judgment.get('question_id')}")

    cfg = config or {}
    high_ratio = float(cfg.get("high_score_serious_error_ratio", 0.8))
    min_confidence = float(cfg.get("minimum_confidence", 0.6))
    review = bool(judgment.get("needs_human_review"))
    answer_errors = judgment.get("errors") or []
    if _has_serious_error(answer_errors) and max_f > 0 and score_f / max_f >= high_ratio and not review:
        errors.append("high score with serious errors requires needs_human_review=true")
    confidence = judgment.get("confidence")
    if isinstance(confidence, (int, float)) and not isinstance(confidence, bool) \
            and float(confidence) < min_confidence and not review:
        errors.append("low confidence requires needs_human_review=true")
    return errors
