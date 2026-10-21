"""Export and verify generated drafts without changing their approval status."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT.parent))
from CampusEval.subjective.io_utils import append_jsonl, canonical_hash, read_jsonl, write_json

SPEC = importlib.util.spec_from_file_location("rubric_generator", ROOT / "scripts/evaluation/generate_subjective_rubrics.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
DOUBLED_DELIMITER = re.compile(r"(?<!\\)\\\\(?:[()\]]|\[(?!\s*[-+]?(?:\d+(?:\.\d*)?|\.\d+)\s*(?:pt|mm|cm|em|ex|in)\s*\]))")


def normalize_latex(text: str) -> str:
    """Undo uniform extra JSON escaping, preserving ordinary matrix row breaks.

    Only act when a doubled math delimiter proves the extra escaping, and no
    correctly escaped command/delimiter exists in the same field. Mixed cases
    are retained for review rather than guessing.
    """
    doubled_delimiter = DOUBLED_DELIMITER.search(text)
    single_command = re.search(r"(?<!\\)\\(?:[A-Za-z]+|[()\[\]])", text)
    return text.replace("\\\\", "\\") if doubled_delimiter and not single_command else text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--recover-valid-rejections", action="store_true",
                        help="Revalidate saved rejected objects with current checks; no model calls or mathematical edits")
    args = parser.parse_args()
    folder = args.output_dir.resolve()
    corrections_path = folder / "review_corrections.json"
    corrections = json.loads(corrections_path.read_text(encoding="utf-8")) if corrections_path.exists() else {}
    manifest = json.loads((folder / "generation_manifest.json").read_text(encoding="utf-8"))
    source = Path(manifest["dataset"])
    if hashlib.sha256(source.read_bytes()).hexdigest() != manifest["dataset_sha256"]:
        raise SystemExit("dataset changed since generation")
    journal = read_jsonl(folder / "generation_journal.jsonl")
    completed = {r["question_id"]: r for r in journal if not r.get("failed")}
    if args.recover_valid_rejections:
        for attempt in journal:
            question_id = attempt["question_id"]
            if question_id in completed:
                continue
            for rejected in reversed(attempt.get("rejected_attempts", [])):
                candidate = rejected.get("result")
                if not isinstance(candidate, dict) or "truncated completion" in rejected.get("errors", []):
                    continue
                candidate = json.loads(json.dumps(candidate, ensure_ascii=False))
                metadata_changes = GEN.normalize_review_metadata(candidate)
                if GEN.content_errors(candidate, question_id):
                    continue
                recovered = {"question_id": question_id, "result": candidate, "usage": {},
                             "response_model": manifest["model"], "attempts": [],
                             "response_model_source": "requested model in original run configuration",
                             "local_metadata_normalization": metadata_changes,
                             "local_recovery": "Revalidated complete saved object; mathematical content unchanged",
                             "recovered_from_attempt": rejected["attempt"]}
                append_jsonl(folder / "generation_journal.jsonl", recovered)
                completed[question_id] = recovered
                break
        journal = read_jsonl(folder / "generation_journal.jsonl")
    rows = read_jsonl(source)
    eligible = [r for r in rows if r["metadata"]["question_type"] in ("解答题", "证明题")
                and r["answer"]["solution"].strip()]
    if set(completed) - {r["id"] for r in eligible}:
        raise SystemExit("journal has IDs outside eligible source set")
    exported, normalization, reviews, errors, suspicious = [], [], [], {}, []
    for row in eligible:
        question_id = row["id"]
        if question_id not in completed:
            continue
        envelope = completed[question_id]["result"]
        record = dict(envelope["rubric_record"])
        correction = corrections.get(question_id)
        if correction:
            if canonical_hash(record) != correction["expected_record_hash"]:
                raise SystemExit(f"correction source changed: {question_id}")
            if set(correction["field_replacements"]) - {"rubric", "reference_solution_1", "reference_solution_2"}:
                raise SystemExit(f"invalid correction fields: {question_id}")
            record.update(correction["field_replacements"])
        changed = []
        for field in ("rubric", "reference_solution_1", "reference_solution_2"):
            if isinstance(record.get(field), str):
                original = record[field]
                record[field] = normalize_latex(original)
                if original != record[field]:
                    changed.append(field)
                if DOUBLED_DELIMITER.search(record[field]):
                    suspicious.append({"question_id": question_id, "field": field,
                                       "reason": "mixed_or_remaining_doubled_math_delimiter"})
        if changed:
            normalization.append({"question_id": question_id, "fields": changed,
                                  "reason": "removed_uniform_extra_JSON_escape_layer"})
        issues = GEN.content_errors({**envelope, "rubric_record": record}, question_id)
        if issues:
            errors[question_id] = issues
        exported.append(record)
        reviews.append({"question_id": question_id, "needs_review": envelope["needs_review"] or bool(correction),
                        "source_issues": envelope["source_issues"],
                        "review_notes": envelope["review_notes"] + (correction.get("review_notes", []) if correction else [])})
    if errors:
        write_json(folder / "export_errors.json", errors)
        raise SystemExit(f"validation failed for {len(errors)} drafts")
    target = folder / "rubrics.draft.jsonl"
    target.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in exported), encoding="utf-8")
    provenance = [{"question_id": row["id"], "response_model": completed[row["id"]].get("response_model"),
                   "base_url": completed[row["id"]].get("origin_base_url", manifest["base_url"]),
                   "request_options": completed[row["id"]].get("request_options", {}),
                   "local_content_correction": row["id"] in corrections,
                   "source_fingerprint": manifest["source_fingerprints"][row["id"]],
                   "prompt_sha256": manifest["prompt_sha256"]}
                  for row in eligible if row["id"] in completed]
    (folder / "generation_provenance.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in provenance), encoding="utf-8")
    write_json(folder / "latex_normalization_report.json", {"normalized": normalization, "remaining_flags": suspicious})
    write_json(folder / "content_review_flags.json", reviews)
    report = {
        "status": "drafts_pending_content_review", "selected": manifest["selected"],
        "eligible": len(eligible), "generated": len(exported), "skipped": manifest["skipped"],
        "missing_ids": [r["id"] for r in eligible if r["id"] not in completed],
        "flagged_for_review": [r["question_id"] for r in reviews if r["needs_review"]],
        "content_review_flag_count": sum(r["needs_review"] for r in reviews),
        "without_second_solution": sum(r.get("reference_solution_2") is None for r in exported),
        "schema_and_score_total_errors": errors,
        "latex_normalized_records": len(normalization), "latex_remaining_flags": suspicious,
        "local_content_corrections": list(corrections),
        "question_types": {kind: sum(r["metadata"]["question_type"] == kind and r["id"] in completed for r in eligible)
                           for kind in ("解答题", "证明题")},
        "response_models": sorted({str(r.get("response_model")) for r in completed.values()}),
        "model_counts": dict(Counter(str(r.get("response_model")) for r in completed.values())),
        "usage_all_attempts": {key: sum(r.get("usage", {}).get(key, 0) for r in journal)
                               for key in ("prompt_tokens", "completion_tokens", "total_tokens")},
        "usage_scope": "This journal includes imported successful records and this run's attempts; earlier failed-call usage remains in original run journals.",
        "output_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "note": "Automatically checked structure, IDs, score totals and uniform LaTeX escaping; no mathematical approval implied."}
    write_json(folder / "draft_validation_report.json", report)
    lines = ["# 考研解答题与证明题 Rubric 生成记录", "",
             f"- 本轮指定模型：`{manifest['model']}`；已完成题目可来自此前模型，详见下列分布及逐题生成记录。",
             f"- 实际模型分布：{json.dumps(report['model_counts'], ensure_ascii=False)}",
             f"- 原题文件：`{source}`",
             f"- 筛选题数：{manifest['selected']}；有解析可生成：{len(eligible)}；已生成：{len(exported)}。",
             "- 每题统一满分 20 分；格式与现有 subjective_rubric.schema.json 一致。",
             "- 输出：`rubrics.draft.jsonl`。结果为模型生成的待审核稿，尚未进行逐题独立数学审核。",
             "- `generation_journal.jsonl` 保留原始模型结果、用量和失败记录；不保存密钥。",
             "- `generation_provenance.jsonl` 逐题记录实际返回模型、接口地址、题目指纹和提示哈希。",
             "- `draft_validation_report.json` 记录 ID、Schema、分值合计、覆盖率与输出哈希。",
             "- `content_review_flags.json` 与本文件下方列出模型报告的原材料疑点。",
             "- 如存在 `review_corrections.json`，其中保留本地复核修订、原稿指纹与修改理由；导出时检查指纹后应用，原始模型日志不改写。",
             "- 原 questions.jsonl 与原 answer.solution 未改写。", "", "## 跳过题目", ""]
    lines.extend(f"- `{r['question_id']}`：缺少原解析。" for r in manifest["skipped"])
    lines.extend(["", "## 模型提示的复核事项", "",
                  "以下是生成模型的报告，可能包含误报或仅涉及表述精度的问题，不代表已经确认原题有错。", ""])
    for review in reviews:
        if review["needs_review"]:
            lines.extend([f"### {review['question_id']}", ""])
            lines.extend(f"- {issue}" for issue in review["source_issues"])
            lines.extend(f"- 复核说明：{note}" for note in review["review_notes"])
            lines.append("")
    (folder / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("generated", "eligible", "without_second_solution",
                                                  "content_review_flag_count", "latex_normalized_records", "model_counts")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
