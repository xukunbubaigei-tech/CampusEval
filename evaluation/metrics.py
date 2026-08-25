"""Scoring and measurement helpers for objective evaluation.

- ``normalize``: quick text cleanup for direct comparison.
- ``score_final``: final-answer scoring. First tries string equality, then
  symbolic equivalence via sympy, then a format-aware pipeline that recognises
  LaTeX variants (\\dfrac / \\frac without braces / \\left..\\right / \\pm /
  \\sqrt / \\pi), multi-answer separators (comma / ； / 或 / 和), equation
  expanded forms (e.g. circle equations) and item-number notations
  (③④ vs 图3，图4).
- ``aggregate``: accuracy summary over scored rows.
"""
from __future__ import annotations

import re

import sympy as sp


def normalize(value: str) -> str:
    return re.sub(r"[\s$。.]", "", str(value)).replace("，", ",").upper()


# ---------------- format-aware matching (2026-08) ----------------

_CIRCLED = {"①": "1", "②": "2", "③": "3", "④": "4", "⑤": "5", "⑥": "6",
            "⑦": "7", "⑧": "8", "⑨": "9", "⑩": "10"}
_SEPARATORS = ",，;；|或和"


def normalize_latex(text: str) -> str:
    """Turn LaTeX-ish answer text into a sympy-parseable compact form."""
    s = str(text)
    s = re.sub(r"\\,", "", s)                       # thin space
    s = s.replace("$", "").replace(" ", "").replace("~", "")
    s = s.replace("\\dfrac", "\\frac")
    s = s.replace("\\left", "").replace("\\right", "")
    for _ in range(4):                              # nested \frac / \sqrt
        s = re.sub(r"\\sqrt\{([^{}]*)\}", r"sqrt(\1)", s)
        s = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)", s)
        s = re.sub(r"\\frac(\d)\{([^{}]*)\}", r"(\1)/(\2)", s)   # \frac3{10}
        s = re.sub(r"\\frac\{([^{}]*)\}(\d)", r"(\1)/(\2)", s)   # \frac{3}10
        s = re.sub(r"\\frac(\d)(\d)", r"(\1)/(\2)", s)           # \frac32
        s = re.sub(r"\\frac(\d)([a-zA-Z])", r"(\1)/(\2)", s)     # \frac1e
    s = re.sub(r"\\text\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\^\{([^{}]*)\}", r"**(\1)", s)     # ^{x} -> **(x)
    s = re.sub(r"\^(\d)", r"**\1", s)               # ^2 -> **2
    s = s.replace("\\pm", "±").replace("\\pi", "pi").replace("π", "pi")
    s = s.replace("\\circ", "").replace("\\cdot", "*")
    s = s.replace("{", "").replace("}", "").replace("\\", "")
    s = s.replace("（", "(").replace("）", ")").replace("。", "").replace("，", ",")
    return s


def _digits_of(text: str) -> str:
    s = "".join(_CIRCLED.get(ch, ch) for ch in str(text))
    return re.sub(r"[^\d]", "", s)


def _is_item_notation(text: str) -> bool:
    return bool(re.fullmatch(r"[\d①-⑩,，、;；\s图]*", str(text)))


def _implicit_mul(expr: str) -> str:
    """Insert * for implicit multiplication (4x -> 4*x, 3pi -> 3*pi)."""
    return re.sub(r"(?<=[\d)])(?=[A-Za-z(])", "*", expr)


def _to_diff(expr: str) -> str:
    if "=" in expr:
        left, right = expr.split("=", 1)
        return f"({left})-({right})"
    return expr


def _sympy_equal(a: str, b: str) -> bool:
    try:
        sa = sp.sympify(_implicit_mul(_to_diff(a).replace("^", "**")))
        sb = sp.sympify(_implicit_mul(_to_diff(b).replace("^", "**")))
        diff = sp.simplify(sa - sb)
        if diff == 0:
            return True
        if diff.is_number:
            return abs(float(sp.N(diff))) < 1e-9
        return False
    except Exception:
        return False


def answer_matches(prediction: str, gold: str) -> bool:
    pred, gold = str(prediction), str(gold)
    if normalize(pred) == normalize(gold):
        return True

    # item-number notation: ③④ vs 图3，图4 vs 3,4
    if _is_item_notation(pred) and _is_item_notation(gold):
        pd, gd = _digits_of(pred), _digits_of(gold)
        if pd and gd and sorted(pd) == sorted(gd):
            return True

    np_, ng = normalize_latex(pred), normalize_latex(gold)
    if np_ == ng:
        return True
    if _sympy_equal(np_, ng):
        return True

    # multi-answer: any part of the prediction matching any part of the gold
    def parts(expr: str):
        return [p for p in re.split(f"[{re.escape(_SEPARATORS)}]", expr) if p]

    for p in parts(np_):
        for g in parts(ng):
            if _sympy_equal(p, g):
                return True
    return False


def score_final(prediction: str, gold: str) -> bool:
    return answer_matches(prediction, gold)


def aggregate(rows):
    n = len(rows)
    return {"count": n,
            "accuracy": sum(r["correct"] for r in rows) / n if n else 0,
            "pass_at_1": sum(r["correct"] for r in rows) / n if n else 0,
            "final_answer_accuracy": sum(r["correct"] for r in rows) / n if n else 0}
