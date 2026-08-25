"""Tests for the plain-text rubric protocol v2 (rubric validation, judgment
validation, blind prompt, aggregation, and dry-run behaviour).

Runnable with either ``python -m unittest tests.test_subjective_evaluation``
or pytest.
"""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from gaokao_math_benchmark.subjective.aggregation import aggregate_judgments, summary
from gaokao_math_benchmark.subjective.io_utils import read_jsonl
from gaokao_math_benchmark.subjective.prompts import judge_prompt
from gaokao_math_benchmark.subjective.validation import validate_judgment, validate_rubric

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests/fixtures/subjective"
CONFIG = ROOT / "configs/subjective_evaluation.json"


def _rubric(idx: int = 0) -> dict:
    return read_jsonl(FIX / "rubrics.jsonl")[idx]


def _judgment(idx: int = 0) -> dict:
    return read_jsonl(FIX / "judgments.jsonl")[idx]


def _subjective_ids() -> set[str]:
    return {q["id"] for q in read_jsonl(FIX / "questions.jsonl")}


def _config() -> dict:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    cfg["judges"] = [
        {"slot": "judge_a", "model": "qwen-judge", "max_tokens": 1024},
        {"slot": "judge_b", "model": "deepseek-judge", "max_tokens": 1024},
        {"slot": "judge_c", "model": "glm-judge", "max_tokens": 1024},
    ]
    return cfg


class RubricValidationTests(unittest.TestCase):
    def test_rubric_schema_valid(self):
        self.assertEqual(validate_rubric(_rubric(0)), [])
        self.assertEqual(validate_rubric(_rubric(1)), [])

    def test_rubric_rejects_old_fields(self):
        rubric = copy.deepcopy(_rubric(0))
        rubric["scoring_items"] = [{"id": "I1", "points": 1}]
        self.assertTrue(validate_rubric(rubric))  # schema forbids extra fields

    def test_rubric_requires_solution1(self):
        rubric = copy.deepcopy(_rubric(0))
        rubric["reference_solution_1"] = ""
        self.assertTrue(validate_rubric(rubric))


class JudgmentValidationTests(unittest.TestCase):
    def test_valid_judgment_passes(self):
        self.assertEqual(validate_judgment(_judgment(0), subjective_ids=_subjective_ids()), [])

    def test_score_bounds(self):
        high = copy.deepcopy(_judgment(0))
        high["score"], high["max_score"] = 3, 2
        self.assertTrue(any("outside" in e for e in validate_judgment(high)))
        negative = copy.deepcopy(_judgment(0))
        negative["score"] = -0.1
        self.assertTrue(validate_judgment(negative))

    def test_score_must_be_numeric(self):
        bad = copy.deepcopy(_judgment(0))
        bad["score"] = "16.5"
        self.assertTrue(validate_judgment(bad))

    def test_reason_required(self):
        bad = copy.deepcopy(_judgment(0))
        bad["reason"] = ""
        self.assertTrue(any("reason" in e for e in validate_judgment(bad)))

    def test_question_id_must_exist(self):
        bad = copy.deepcopy(_judgment(0))
        bad["question_id"] = "no_such_id"
        self.assertTrue(
            any("unknown question_id" in e for e in validate_judgment(bad, subjective_ids=_subjective_ids()))
        )

    def test_high_score_with_errors_requires_review(self):
        bad = copy.deepcopy(_judgment(0))
        bad["score"], bad["max_score"] = 2, 2
        bad["errors"] = ["存在逻辑错误"]
        bad["needs_human_review"] = False
        self.assertTrue(any("human_review" in e for e in validate_judgment(bad, config=_config())))

    def test_low_confidence_requires_review(self):
        bad = copy.deepcopy(_judgment(0))
        bad["confidence"] = 0.4
        bad["needs_human_review"] = False
        self.assertTrue(any("human_review" in e for e in validate_judgment(bad, config=_config())))


class PromptTests(unittest.TestCase):
    def test_blind_prompt_hides_identity(self):
        text = judge_prompt("题目", _rubric(0), "考生作答", "none")
        for leaked in ("candidate_model", "qwen-fixture", "CONFIGURE_ME", "candidate:", "rubric_version", "generator_model"):
            self.assertNotIn(leaked, text)
        for required in ("题目", "参考解法一", "参考解法二", "考生作答", "score", "max_score"):
            self.assertIn(required, text)


class AggregationTests(unittest.TestCase):
    def test_aggregate_single_judge(self):
        out = aggregate_judgments([_judgment(0)], _config(), candidate_model="m", expected_judge_count=1)
        self.assertEqual(out["final_score"], 2.0)
        self.assertFalse(out["needs_human_review"])

    def test_three_judge_disagreement_triggers_review(self):
        judgments = read_jsonl(FIX / "judgments.jsonl")[1:4]  # q2 scores: 4 / 1 / 3.5
        out = aggregate_judgments(judgments, _config(), candidate_model="m", expected_judge_count=3)
        self.assertTrue(out["needs_human_review"])
        self.assertIn("score_range_threshold", out["review_reasons"])
        self.assertEqual(out["score_range"], 3.0)

    def test_incomplete_panel_triggers_review(self):
        out = aggregate_judgments([_judgment(1)], _config(), candidate_model="m", expected_judge_count=3)
        self.assertIn("incomplete_judge_panel", out["review_reasons"])

    def test_summary_shape(self):
        rows = [aggregate_judgments([_judgment(0)], _config(), candidate_model="m", expected_judge_count=1)]
        summary_report = summary(rows)
        self.assertEqual(summary_report["answers"], 1)
        self.assertEqual(summary_report["average_score_rate"], 1.0)


class DryRunTests(unittest.TestCase):
    def test_dry_run_makes_zero_network_requests(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "out"
            cfg_path = Path(tmp) / "cfg.json"
            cfg_path.write_text(json.dumps(_config(), ensure_ascii=False), encoding="utf-8")
            cmd = [
                sys.executable, str(ROOT / "scripts/evaluate_subjective_answers.py"),
                "--answers", str(FIX / "answers.jsonl"),
                "--questions", str(FIX / "questions.jsonl"),
                "--rubrics", str(FIX / "rubrics.jsonl"),
                "--config", str(cfg_path),
                "--output-dir", str(out_dir),
                "--judge-mode", "three",
                "--dry-run",
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
            self.assertEqual(proc.returncode, 0, proc.stderr)
            report = json.loads((out_dir / "preflight_report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["network_requests"], 0)
            self.assertEqual(report["planned_requests"], 2 * 3)  # 2 answers x 3 judges


if __name__ == "__main__":
    unittest.main()
