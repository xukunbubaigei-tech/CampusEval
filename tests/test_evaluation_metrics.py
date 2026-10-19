"""Tests for objective evaluation metrics (evaluation/metrics.py).

Covers symbolic equivalence and the format-aware matching that resolves the
12 fill-in-blank cases previously requiring manual review in the
qwen3.8-27b objective run (LaTeX variants, multi-answer separators, expanded
equations, item-number notations, float equivalence).
"""
import unittest

from CampusEval.evaluation.metrics import normalize, score_final

# (prediction, gold) pairs that are mathematically equivalent but differ in
# format; all were originally mis-scored as wrong by the naive matcher.
FORMAT_EQUIVALENT_CASES = [
    ("\\dfrac{3}{5}", "$3/5$"),
    ("\\frac{3}{10}", "$\\frac3{10}$"),
    ("\\left(\\frac{1}{e},1\\right)", "$(\\frac1e,1)$"),
    ("\\frac{9}{4}", "$\\frac94$"),
    ("\\frac{3}{2}", "$\\frac32$"),
    ("±2", "$\\pm2$"),
    ("61/25", "$\\frac{61}{25}$"),
    ("\\sqrt{\\frac{11}{6}}", "$\\frac{\\sqrt{66}}{6}$"),
    ("3\\pi/2, 1", "$\\frac{3\\pi}{2}$，$1$"),
    ("x^2+y^2-4x-6y=0", "$(x-2)^2+(y-3)^2=13$ 或 $(x-2)^2+(y-1)^2=5$"),
    ("1/2", "$\\frac12$"),
    ("③④", "图3，图4"),
    ("1/2", "0.5"),
    ("2/4", "1/2"),
]


class EvaluationMetricsTests(unittest.TestCase):
    def test_symbolic_equivalent_final_answer(self):
        self.assertTrue(score_final("2/4", "1/2"))

    def test_normalize_strips_noise(self):
        self.assertEqual(normalize("  x = 1 "), "X=1")

    def test_format_equivalent_cases(self):
        for pred, gold in FORMAT_EQUIVALENT_CASES:
            self.assertTrue(score_final(pred, gold), f"应为等价: {pred!r} vs {gold!r}")

    def test_genuinely_wrong_stays_wrong(self):
        self.assertFalse(score_final("C", "A"))  # 2025/874_06 case
        self.assertFalse(score_final("2", "1"))
        self.assertFalse(score_final("x=1", "x=2"))


if __name__ == "__main__":
    unittest.main()
