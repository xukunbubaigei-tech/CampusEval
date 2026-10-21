"""Regression checks for source boundaries and ambiguous OCR numbering."""
import importlib.util
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[3] / "scripts/construction/kaoyan/build_kaoyan_dataset.py"
SPEC = importlib.util.spec_from_file_location("kaoyan_builder", PATH)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class KaoyanSourceIntegrationTests(unittest.TestCase):
    def test_2021_three_answer_cycle_is_aligned_by_content(self):
        if not (MOD.WORK / "answers_2021.pages.json").exists():
            self.skipTest("Local precise extraction is not distributed with code")
        answers = MOD.make_answers(2021)
        self.assertIn("级数", answers[(2021, 3, 18)]["text"])
        self.assertIn("曲线", answers[(2021, 3, 19)]["text"])
        self.assertIn("I", answers[(2021, 3, 20)]["text"])
        self.assertEqual({u['page'] for u in answers[(2021, 3, 18)]['items']}, {13, 14})
        self.assertEqual({u['page'] for u in answers[(2021, 3, 19)]['items']}, {11, 12})
        self.assertEqual({u['page'] for u in answers[(2021, 3, 20)]['items']}, {12, 13})


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
