"""Reviewed U-MATH corrections; IDs remain tied to original Parquet row numbers."""
from __future__ import annotations

EXCLUDED_IDS = {"umath_416"}  # Required lookup table is absent from the upstream row.
CONTROL_IDS = {"umath_159", "umath_231", "umath_535", "umath_569", "umath_603", "umath_902"}
CURRENCY = {
    "umath_242": ("71.5", "118.1"),
    "umath_659": ("72.00",),
    "umath_874": ("28,112.5", "20", "22.5", "29"),
    "umath_876": ("3", "2", "17"),
    "umath_941": ("10,000",),
}


def curate(record: dict) -> dict | None:
    """Apply only reviewed changes to an original, uncorrected input record."""
    rid = record["id"]
    if rid in EXCLUDED_IDS:
        return None
    if rid in CONTROL_IDS:
        for obj, key in ((record["question"], "text"), (record["answer"], "final_answer")):
            for bad, good in (("\x0crac", r"\frac"), ("\theta", r"\theta"),
                              ("\tan", r"\tan"), ("\right", r"\right")):
                obj[key] = obj[key].replace(bad, good)
    for amount in CURRENCY.get(rid, ()):
        record["question"]["text"] = record["question"]["text"].replace("$" + amount, r"\$" + amount)
    if rid in {"umath_724", "umath_912"}:
        record["answer"]["final_answer"] = record["answer"]["final_answer"].replace("$ $583.75$", r"$\$583.75$")
    if rid in {"umath_114", "umath_238", "umath_1017"}:
        record["answer"]["final_answer"] = record["answer"]["final_answer"].replace(r"$q(x) = $\int", r"$q(x) = \int", 1)
    if rid == "umath_569":
        record["question"]["text"] = record["question"]["text"].replace(
            "the angle", "the acute (positive, undirected) angle", 1)
    if rid == "umath_335":
        record["answer"]["final_answer"] = r"$\frac{1}{3\cos^3 x}-\frac{2}{\cos x}-\cos x+C$, on any interval where $\cos x\ne 0$."
    if rid == "umath_534":
        record["answer"]["final_answer"] = r"$\frac{\sqrt{25x^2+10x+6}}{25}+\frac{9}{25}\ln\left(5x+1+\sqrt{25x^2+10x+6}\right)+C$."
    if rid == "umath_921":
        record["answer"]["final_answer"] = (
            r"For $x<2-\sqrt{2}$: $2\ln\left|x-2+\sqrt{x^2-4x+2}\right|"
            r"+3\arcsin\left(\frac{x}{(x-1)\sqrt{2}}\right)+C_1$."
            "\n\n"
            r"For $x>2+\sqrt{2}$: $2\ln\left|x-2+\sqrt{x^2-4x+2}\right|"
            r"-3\arcsin\left(\frac{x}{(x-1)\sqrt{2}}\right)+C_2$."
            " The constants are independent on the two intervals.")
    return record
