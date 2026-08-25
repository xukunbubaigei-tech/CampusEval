from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_few_shots(path: Path | None, limit: int = 3) -> str:
    if path is None or not path.exists():
        return "（无）"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return json.dumps(rows[:limit], ensure_ascii=False, indent=2)


def render_template(path: Path, values: dict[str, object]) -> str:
    text = path.read_text(encoding="utf-8")
    expected = [piece.split("}}", 1)[0] for piece in text.split("{{")[1:] if "}}" in piece]
    missing = [key for key in expected if key not in values]
    if missing:
        raise ValueError(f"missing prompt values: {missing}")
    for key, value in values.items():
        rendered = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)
        text = text.replace("{{" + key + "}}", rendered)
    return text


def judge_prompt(question: str, rubric: dict, candidate_answer: str, few_shots: str) -> str:
    return render_template(ROOT / "prompts" / "subjective_judge_blind_zh_v1.txt", {
        "question": question,
        "rubric": rubric.get("rubric", ""),
        "reference_solution_1": rubric.get("reference_solution_1", ""),
        "reference_solution_2": rubric.get("reference_solution_2", ""),
        "candidate_answer": candidate_answer,
        "few_shots": few_shots,
    })
