"""Regression checks for source boundaries and ambiguous OCR numbering."""
import importlib.util
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[2] / "scripts/construction/kaoyan/build_kaoyan_dataset.py"
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


if __name__ == "__main__":
    unittest.main()
