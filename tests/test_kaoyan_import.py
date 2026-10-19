"""Regression checks for source boundaries and ambiguous OCR numbering."""
import importlib.util
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "scripts/construction/kaoyan/build_kaoyan_dataset.py"
SPEC = importlib.util.spec_from_file_location("kaoyan_builder", PATH)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class KaoyanImportTests(unittest.TestCase):
    def test_user_fixed_2022_question_2_survives_rebuild(self):
        correction = MOD.CORRECTIONS[(2022, 1, 2)]
        self.assertEqual(correction["final_answer"], "B")
        self.assertEqual(len({o["text"] for o in correction["options"]}), 4)
        self.assertEqual(correction["options"][3]["text"], r"$f(1)=0,\ f'(1)=1$")

    def test_event_names_are_not_mcq_option_labels(self):
        text, options, error = MOD.split_options(
            "设事件A,B。(A) $P(A)>P(B)$ (B) $P(A)=P(B)$ (C) $P(A)<P(B)$ (D) 均不成立")
        self.assertIsNone(error)
        self.assertEqual([o["label"] for o in options], list("ABCD"))
        self.assertEqual(options[0]["text"], "$P(A)>P(B)$")

    def test_unfilled_answer_label_does_not_become_an_answer(self):
        final, solution, method = MOD.response_parts(
            {"kind": "选择题"}, {"text": "题干与选项\n\n【答案】\n【解析】"})
        self.assertEqual(final, "")
        self.assertEqual(method, "missing_final_answer")

    def test_source_groups_exclude_early_paper_ii(self):
        if not (MOD.WORK / "questions_all.pages.json").exists():
            self.skipTest("Local precise extraction is not distributed with code")
        groups, exclusions = MOD.question_groups()
        self.assertEqual(set(groups), set(range(1987, 2024)))
        self.assertTrue(any(x.get("year") == 1987 for x in exclusions))
        self.assertFalse(any("试卷II" in u["text"] for u in groups[1987]))

    def test_misplaced_2010_page_is_not_assigned_to_2019(self):
        if not (MOD.WORK / "questions_all.pages.json").exists():
            self.skipTest("Local precise extraction is not distributed with code")
        groups, _ = MOD.question_groups()
        self.assertTrue(any(u["page"] == 111 for u in groups[2010]))
        self.assertFalse(any(u["page"] == 111 for u in groups[2019]))


if __name__ == "__main__":
    unittest.main()
