"""Locally rescore mini-dataset predictions without making API calls."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


def _frac(text: str) -> str:
    old = None
    while old != text:
        old = text
        text = re.sub(r"\\(?:d?frac)\{([^{}]+)\}\{([^{}]+)\}", r"(\1)/(\2)", text)
        text = re.sub(r"\\(?:d?frac)\{([^{}]+)\}([A-Za-z0-9.]+)", r"(\1)/(\2)", text)
        text = re.sub(r"\\(?:d?frac)([A-Za-z0-9.]+)\{([^{}]+)\}", r"(\1)/(\2)", text)
        text = re.sub(r"\\(?:d?frac)([A-Za-z0-9.])([A-Za-z0-9.])", r"(\1)/(\2)", text)
    return text


def normalize(text: object) -> str:
    s = str(text or "").strip()
    s = s.replace("$", "").replace("\\(", "").replace("\\)", "")
    s = s.replace("\\left", "").replace("\\right", "").replace("\\pm", "±")
    s = s.replace("\\ln", "ln")
    s = s.replace("，", ",").replace("。", "").replace(" ", "")
    for number, circled in zip("123456789", "①②③④⑤⑥⑦⑧⑨"):
        s = s.replace(f"图{number}", circled)
    s = s.replace(",", "")
    s = _frac(s)
    s = re.sub(r"\\sqrt\{([^{}]+)\}", r"sqrt(\1)", s)
    s = s.replace("{", "(").replace("}", ")")
    # Parentheses around atomic fraction terms are formatting-only.
    s = re.sub(r"\(([A-Za-z0-9.]+)\)/\(([A-Za-z0-9.]+)\)", r"\1/\2", s)
    return s.lower()


def equivalent(prediction: object, gold: object) -> tuple[bool, str]:
    pred = normalize(prediction)
    alternatives = re.split(r"\s*或\s*", str(gold or ""))
    for answer in alternatives:
        target = normalize(answer)
        if pred == target:
            return True, "normalized_exact"
        if pred.strip("()") == target.strip("()"):
            return True, "normalized_exact"
        try:
            from fractions import Fraction
            if Fraction(pred) == Fraction(target):
                return True, "numeric_equivalent"
        except (ValueError, ZeroDivisionError):
            pass
    return False, "normalized_mismatch"


def load_corrections(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("corrections", {})


def aggregate(rows: list[dict]) -> dict:
    groups: dict[str, dict[str, list[dict]]] = {
        "by_question_type": defaultdict(list),
        "by_year": defaultdict(list),
        "by_modality": defaultdict(list),
    }
    for row in rows:
        groups["by_question_type"][row["question_type"]].append(row)
        groups["by_year"][str(row["year"])].append(row)
        groups["by_modality"]["with_image" if row["has_image"] else "text_only"].append(row)
    result = {}
    for group_name, values in groups.items():
        result[group_name] = {}
        for key, items in sorted(values.items()):
            correct = sum(bool(x["rescored_correct"]) for x in items)
            result[group_name][key] = {
                "count": len(items), "correct": correct,
                "accuracy": correct / len(items) if items else None,
            }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="gaokao_math_benchmark/datasets/objective_70/questions.jsonl")
    parser.add_argument("--results", default="gaokao_math_benchmark/runs/objective/qwen3.6-35b-a3b/results.jsonl")
    parser.add_argument("--corrections", default="gaokao_math_benchmark/data/corrections/answer_corrections.json")
    parser.add_argument(
        "--gold-from-dataset",
        action="store_true",
        help="Use the current dataset answer instead of the historical gold embedded in results.jsonl.",
    )
    args = parser.parse_args()
    dataset_path, results_path = Path(args.dataset), Path(args.results)
    dataset = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    raw = [json.loads(line) for line in results_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    latest = {row["id"]: row for row in raw}  # later retry supersedes earlier attempt
    dataset_by_id = {row["id"]: row for row in dataset}
    corrections = load_corrections(Path(args.corrections))
    rescored = []
    excluded = []
    api_error_ids = [qid for qid, row in latest.items() if row.get("status") != "ok"]
    for qid, row in latest.items():
        if row.get("status") != "ok":
            continue
        item = dataset_by_id[qid]
        dataset_gold = item.get("answer", {}).get("final_answer", item.get("final_answer", ""))
        gold = dataset_gold if args.gold_from_dataset else row.get("gold", dataset_gold)
        is_multiselect = bool(re.fullmatch(r"[A-D]{2,4}", normalize(gold).upper()))
        protocol_mismatch = is_multiselect and not (
            row.get("evaluation_protocol") == "choice_aware_v2"
            and row.get("choice_mode") == "multiple"
        )
        accepted = corrections.get(qid, {}).get("accepted_answers", [gold])
        matches = [equivalent(row.get("prediction"), candidate) for candidate in accepted]
        correct = any(match[0] for match in matches)
        method = "accepted_answers" if correct and len(accepted) > 1 else matches[0][1]
        out = {**row,
               "historical_gold": row.get("gold") if args.gold_from_dataset else None,
               "gold": gold,
               "gold_source": "current_dataset" if args.gold_from_dataset else "historical_result_or_dataset_fallback",
               "question_type": item.get("metadata", {}).get("question_type", item.get("question_type", row.get("question_type"))),
               "rescored_correct": correct, "score_method": method,
               "accepted_answers": accepted,
               "evaluation_status": "excluded_multi_choice_prompt_mismatch" if protocol_mismatch else "included"}
        rescored.append(out)
        if protocol_mismatch:
            excluded.append(qid)
    included = [row for row in rescored if row["evaluation_status"] == "included"]
    correct = sum(bool(row["rescored_correct"]) for row in included)
    missing = [row["id"] for row in dataset if row["id"] not in latest]
    changed = [row["id"] for row in rescored if bool(row.get("correct")) != bool(row["rescored_correct"])]
    source_summary_path = results_path.parent / "summary.json"
    source_summary = json.loads(source_summary_path.read_text(encoding="utf-8")) if source_summary_path.exists() else {}
    summary = {
        "model": source_summary.get("model", "unknown"),
        "evaluation_scope": source_summary.get("evaluation_scope", "all_records"),
        "dataset_records": len(dataset), "raw_result_rows": len(raw),
        "unique_completed": len(latest), "duplicate_result_rows": len(raw) - len(latest),
        "missing_ids": missing, "excluded_ids": excluded,
        "api_error_ids": api_error_ids,
        "api_completed": len(rescored),
        "api_failed": len(api_error_ids),
        "primary": {"count": len(included), "correct": correct,
                    "accuracy": correct / len(included) if included else None},
        "raw_unique_rescored": {"count": len(rescored),
            "correct": sum(bool(row["rescored_correct"]) for row in rescored),
            "accuracy": sum(bool(row["rescored_correct"]) for row in rescored) / len(rescored)},
        "score_changed_ids": changed,
        **aggregate(included),
    }
    out_dir = results_path.parent
    (out_dir / "rescored_results.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rescored), encoding="utf-8")
    (out_dir / "rescored_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
