"""Multi-choice prompts, extraction and rescoring retain full-set semantics."""
import unittest

from CampusEval.scripts.evaluation.evaluate_qwen_mini import build_prompt, choice_mode, extract_answer
from CampusEval.scripts.evaluation.rescore_qwen_mini import equivalent


class BenchmarkChoiceTypeTests(unittest.TestCase):
    def test_explicit_multiple_choice_does_not_need_gold_to_set_prompt(self):
        row = {"metadata": {"question_type": "多选题"},
               "question": {"text": "请选择所有正确选项。", "options": [
                   {"label": key, "text": f"选项{key}"} for key in "ABCD"]}}
        self.assertEqual(choice_mode(row), "multiple")
        prompt = build_prompt(row)
        self.assertIn("本题为多选题", prompt)
        self.assertIn("D. 选项D", prompt)
        self.assertNotIn("本题为填空题", prompt)

    def test_explicit_multiple_choice_extracts_all_letters(self):
        self.assertEqual(extract_answer("<answer>D,A,B</answer>", "多选题"), "ABD")
        self.assertEqual(extract_answer("<answer>B</answer>", "选择题", "single"), "B")

    def test_rescoring_requires_complete_choice_set(self):
        self.assertTrue(equivalent("BDA", "ABD")[0])
        self.assertFalse(equivalent("AB", "ABD")[0])
        self.assertFalse(equivalent("ABCD", "ABD")[0])


if __name__ == "__main__":
    unittest.main()
