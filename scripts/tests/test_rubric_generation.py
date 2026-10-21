"""Verify draft acceptance rules without making network requests."""
import importlib.util
from pathlib import Path
from threading import Event
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "rubric_generation", ROOT / "scripts/evaluation/generate_subjective_rubrics.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)
EXPORT_SPEC = importlib.util.spec_from_file_location(
    "rubric_export", ROOT / "scripts/maintenance/finalize_rubric_drafts.py")
EXPORT = importlib.util.module_from_spec(EXPORT_SPEC)
EXPORT_SPEC.loader.exec_module(EXPORT)


def envelope():
    return {
        "rubric_record": {"question_id": "q1", "rubric": (
            "【关键知识点】求导\n【评分要点（满分20分）】\n"
            "- （12分）求得导函数；公式正确但计算错给6分。\n"
            "- （8分）代入求值；只写结果给4分。\n"
            "【等价解法认可】导数定义\n【常见错误与不完全作答】遗漏系数\n"
            "【评卷提示】按推理评分"),
            "reference_solution_1": "由幂函数求导法则得结果。", "reference_solution_2": None},
        "needs_review": False, "source_issues": [], "review_notes": []}


class AcceptanceTests(unittest.TestCase):
    def test_accepts_nullable_alternative_and_partial_credit_numbers(self):
        self.assertEqual(MOD.content_errors(envelope(), "q1"), [])

    def test_rejects_incorrect_sum_and_wrong_id(self):
        row = envelope()
        row["rubric_record"]["rubric"] = row["rubric_record"]["rubric"].replace("（8分）", "（9分）")
        errors = MOD.content_errors(row, "other")
        self.assertTrue(any("sum must be 20" in error for error in errors))
        self.assertIn("question_id mismatch", errors)

    def test_allows_small_question_summary_without_counting_it_twice(self):
        row = envelope()
        row["rubric_record"]["rubric"] = row["rubric_record"]["rubric"].replace(
            "【评分要点（满分20分）】", "【评分要点（满分20分）】\n第(I)问12分，第(II)问8分。")
        self.assertEqual(MOD.content_errors(row, "q1"), [])

    def test_ascii_score_parentheses_have_the_same_score_caps(self):
        row = envelope()
        row["rubric_record"]["rubric"] = row["rubric_record"]["rubric"].replace("（12分）", "(12分)").replace("（8分）", "(8分)")
        self.assertEqual(MOD.content_errors(row, "q1"), [])

    def test_rejects_unflagged_source_conflict(self):
        row = envelope()
        row["source_issues"] = ["题干与原解析冲突"]
        self.assertIn("source issues require needs_review=true", MOD.content_errors(row, "q1"))

    def test_local_metadata_repair_does_not_change_rubric(self):
        row = envelope()
        original = dict(row["rubric_record"])
        row["source_issues"] = [{"issue": "笔误", "correction": "更正符号"}]
        changes = MOD.normalize_review_metadata(row)
        self.assertTrue(changes)
        self.assertTrue(row["needs_review"])
        self.assertIsInstance(row["source_issues"][0], str)
        self.assertEqual(row["rubric_record"], original)
        self.assertEqual(MOD.content_errors(row, "q1"), [])

    def test_misnested_solutions_are_moved_without_content_edits(self):
        row = envelope()
        original = dict(row["rubric_record"])
        row["reference_solution_1"] = row["rubric_record"].pop("reference_solution_1")
        row["reference_solution_2"] = row["rubric_record"].pop("reference_solution_2")
        row.pop("needs_review")
        MOD.normalize_review_metadata(row)
        self.assertEqual(row["rubric_record"], original)
        self.assertTrue(row["needs_review"])
        self.assertEqual(MOD.content_errors(row, "q1"), [])

    def test_rejects_duplicate_solutions_and_extra_rubric_fields(self):
        row = envelope()
        row["rubric_record"]["reference_solution_2"] = row["rubric_record"]["reference_solution_1"]
        row["rubric_record"]["model"] = "private metadata"
        errors = MOD.content_errors(row, "q1")
        self.assertIn("reference solutions identical", errors)
        self.assertTrue(any("Additional properties" in error for error in errors))

    def test_extracts_question_and_solution_images_without_duplicates(self):
        row = {"question": {"text": "![图](q.png)", "images": ["q.png"]},
               "answer": {"solution": "![解析](s.png)"}}
        self.assertEqual(MOD.image_refs(row), ["q.png", "s.png"])

    def test_repairs_uniform_escape_layer_preserving_matrix_row_breaks(self):
        correct = r"\(\begin{pmatrix}1&0\\0&1\end{pmatrix}\)"
        self.assertEqual(EXPORT.normalize_latex(correct.replace("\\", "\\\\")), correct)
        self.assertEqual(EXPORT.normalize_latex(correct), correct)

    def test_leaves_mixed_and_bare_matrix_escaping_for_review(self):
        mixed = r"\\(x\\) and \frac{1}{2}"
        self.assertEqual(EXPORT.normalize_latex(mixed), mixed)
        bare = r"1&0\\0&1"
        self.assertEqual(EXPORT.normalize_latex(bare), bare)
        spaced = r"1&0\\[4pt]0&1"
        self.assertEqual(EXPORT.normalize_latex(spaced), spaced)
        self.assertIsNone(EXPORT.DOUBLED_DELIMITER.search(spaced))

    def test_quota_error_prevents_later_requests(self):
        stop = Event()
        args = SimpleNamespace(dataset=ROOT / "datasets/kaoyan/questions.jsonl", retries=3,
                               model="test", max_tokens=100, base_url="https://example.invalid/v1", timeout=1)
        row = {"id": "q1", "question": {"text": "求值", "images": []},
               "answer": {"solution": "计算"}}
        with patch.object(MOD.requests, "Session") as session:
            response = session.return_value.__enter__.return_value.post.return_value
            response.status_code = 403
            response.json.return_value = {"error": {"code": "insufficient_quota"}}
            first = MOD.generate(row, args, "dummy-key", "system", stop)
            second = MOD.generate(row, args, "dummy-key", "system", stop)
            self.assertTrue(first["failed"])
            self.assertTrue(second["failed"])
            self.assertTrue(stop.is_set())
            self.assertEqual(session.return_value.__enter__.return_value.post.call_count, 1)

    def test_truncated_completion_increases_cap_without_repeating_partial_text(self):
        args = SimpleNamespace(dataset=ROOT / "datasets/kaoyan/questions.jsonl", retries=2,
                               model="test", max_tokens=100, base_url="https://example.invalid/v1", timeout=1)
        row = {"id": "q1", "question": {"text": "求值", "images": []}, "answer": {"solution": "计算"}}
        with patch.object(MOD.requests, "Session") as session:
            post = session.return_value.__enter__.return_value.post
            response = post.return_value
            response.status_code = 200
            response.json.side_effect = [
                {"choices": [{"message": {"content": '{"partial":'}, "finish_reason": "length"}]},
                {"choices": [{"message": {"content": __import__('json').dumps(envelope())}, "finish_reason": "stop"}]},
            ]
            result = MOD.generate(row, args, "dummy-key", "system", Event())
            self.assertNotIn("failed", result)
            self.assertEqual([call.kwargs["json"]["max_tokens"] for call in post.call_args_list], [100, 200])
            self.assertEqual(len(post.call_args_list[-1].kwargs["json"]["messages"]), 2)

    def test_invalid_json_is_preserved_and_repaired(self):
        args = SimpleNamespace(dataset=ROOT / "datasets/kaoyan/questions.jsonl", retries=2,
                               model="test", max_tokens=100, base_url="https://example.invalid/v1", timeout=1)
        row = {"id": "q1", "question": {"text": "求值", "images": []}, "answer": {"solution": "计算"}}
        with patch.object(MOD.requests, "Session") as session:
            post = session.return_value.__enter__.return_value.post
            response = post.return_value
            response.status_code = 200
            response.json.side_effect = [
                {"choices": [{"message": {"content": "not JSON"}, "finish_reason": "stop"}]},
                {"choices": [{"message": {"content": __import__('json').dumps(envelope())}, "finish_reason": "stop"}]},
            ]
            result = MOD.generate(row, args, "dummy-key", "system", Event())
            self.assertNotIn("failed", result)
            self.assertEqual(result["rejected_attempts"][0]["raw_content"], "not JSON")
            self.assertEqual(post.call_args_list[-1].kwargs["json"]["messages"][2]["content"], "not JSON")

    def test_direct_mode_option_is_explicit_and_recorded(self):
        args = SimpleNamespace(dataset=ROOT / "datasets/kaoyan/questions.jsonl", retries=1,
                               model="test", max_tokens=100, base_url="https://example.invalid/v1", timeout=1,
                               no_thinking=True)
        row = {"id": "q1", "question": {"text": "求值", "images": []}, "answer": {"solution": "计算"}}
        with patch.object(MOD.requests, "Session") as session:
            post = session.return_value.__enter__.return_value.post
            response = post.return_value
            response.status_code = 200
            response.json.return_value = {"choices": [{"message": {"content": __import__('json').dumps(envelope())}, "finish_reason": "stop"}]}
            result = MOD.generate(row, args, "dummy-key", "system", Event())
            self.assertIs(post.call_args.kwargs["json"]["enable_thinking"], False)
            self.assertIs(result["request_options"]["enable_thinking"], False)


if __name__ == "__main__":
    unittest.main()
