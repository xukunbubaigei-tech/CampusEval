"""Generate resumable, source-bound rubric drafts; never mark them approved."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from threading import Event
import time

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT.parent))
from CampusEval.subjective.common import ensure_run_output_dir, multimodal_content, resolve_image_path
from CampusEval.subjective.io_utils import append_jsonl, canonical_hash, extract_json_object, read_jsonl, write_json
from CampusEval.subjective.validation import validate_rubric

HEADINGS = ["【关键知识点】", "【评分要点（满分20分）】", "【等价解法认可】",
            "【常见错误与不完全作答】", "【评卷提示】"]


def content_errors(envelope: dict, question_id: str) -> list[str]:
    if set(envelope) != {"rubric_record", "needs_review", "source_issues", "review_notes"}:
        return ["incorrect envelope fields"]
    rubric = envelope.get("rubric_record")
    if not isinstance(rubric, dict):
        return ["rubric_record must be object"]
    errors = validate_rubric(rubric)
    if rubric.get("question_id") != question_id:
        errors.append("question_id mismatch")
    text = rubric.get("rubric", "")
    if not isinstance(text, str):
        return errors + ["rubric must be text"]
    positions = [text.find(heading) for heading in HEADINGS]
    if any(p < 0 for p in positions) or positions != sorted(positions):
        errors.append("missing or unordered rubric sections")
    else:
        scoring = text[positions[1] + len(HEADINGS[1]):positions[2]]
        lines = [line.strip() for line in scoring.splitlines() if line.strip()]
        points = []
        for line in lines:
            # Permit small-question allocation summaries and wrapped prose.
            # Every actual score bullet still needs an explicit positive cap.
            if not line.startswith("-") and not re.match(r"^[（(]\d+分[）)]", line):
                continue
            match = re.match(r"^-\s*[（(]([1-9]\d*)分[）)]\s*\S", line)
            if not match:
                errors.append("scoring line must start with - （N分）")
            else:
                points.append(Decimal(match.group(1)))
        if sum(points) != 20:
            errors.append(f"scoring sum must be 20, got {sum(points)}")
    for key in ("reference_solution_1", "reference_solution_2"):
        value = rubric.get(key)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            errors.append(f"{key} must not be blank")
    first, second = rubric.get("reference_solution_1"), rubric.get("reference_solution_2")
    if isinstance(first, str) and isinstance(second, str):
        if re.sub(r"\s", "", first) == re.sub(r"\s", "", second):
            errors.append("reference solutions identical")
    if not isinstance(envelope.get("needs_review"), bool):
        errors.append("needs_review must be boolean")
    for key in ("source_issues", "review_notes"):
        if not isinstance(envelope.get(key), list) or not all(
                isinstance(item, str) for item in envelope[key]):
            errors.append(f"{key} must be array of strings")
    if envelope.get("source_issues") and not envelope.get("needs_review"):
        errors.append("source issues require needs_review=true")
    return errors


def image_refs(row: dict) -> list[str]:
    refs = list(row["question"].get("images", []))
    for field in (row["question"]["text"], row["answer"]["solution"]):
        refs.extend(re.findall(r"!\[[^\]]*\]\(([^\s)]+)\)", field))
    return list(dict.fromkeys(refs))


def normalize_review_metadata(result: dict) -> list[str]:
    """Preserve notes while conservatively flagging all source corrections."""
    changes = []
    # Move unambiguously misnested solutions without changing their contents.
    record = result.get("rubric_record")
    if isinstance(record, dict):
        for field in ("reference_solution_1", "reference_solution_2"):
            if field in result and (field not in record or record[field] == result[field]):
                record[field] = result.pop(field)
                changes.append(f"moved {field} into rubric_record; text unchanged")
        if changes:
            absent = {"needs_review", "source_issues", "review_notes"} - set(result)
            if absent:
                result.setdefault("source_issues", [])
                result.setdefault("review_notes", [])
                result["needs_review"] = True
                if isinstance(result["review_notes"], list):
                    result["review_notes"].append("原始返回缺少部分复核元数据，已保守标记待复核；参考解法文本未修改。")
                changes.append("filled absent review metadata conservatively")
    for field in ("source_issues", "review_notes"):
        items = result.get(field)
        if isinstance(items, list) and any(isinstance(item, dict) for item in items):
            result[field] = [json.dumps(item, ensure_ascii=False) if isinstance(item, dict) else item for item in items]
            changes.append(f"serialized structured {field} without dropping content")
    if result.get("source_issues") and result.get("needs_review") is False:
        result["needs_review"] = True
        changes.append("flagged source issues for review")
    return changes


def generate(row: dict, args: argparse.Namespace, key: str, system: str, stop: Event) -> dict:
    question_id = row["id"]
    input_text = json.dumps(row, ensure_ascii=False)
    refs = image_refs(row)
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": multimodal_content(input_text, refs, ROOT, args.dataset)},
    ]
    started = time.monotonic()
    usage = {}
    attempts = []
    rejected = []
    token_limit = args.max_tokens
    with requests.Session() as session:
        for attempt in range(1, args.retries + 1):
            if stop.is_set():
                attempts.append({"attempt": attempt, "error": "endpoint_blocked; no further request"})
                break
            payload = {"model": args.model, "messages": messages,
                       "max_tokens": token_limit, "temperature": 0}
            if getattr(args, "no_thinking", False):
                payload["enable_thinking"] = False
            try:
                response = session.post(args.base_url.rstrip("/") + "/chat/completions",
                                        headers={"Authorization": "Bearer " + key},
                                        json=payload, timeout=(30, args.timeout))
                # Never log response bodies or exception strings: they may contain secrets.
                if response.status_code >= 400:
                    status = response.status_code
                    code = None
                    try:
                        candidate = response.json().get("error", {}).get("code")
                        if candidate in ("insufficient_quota", "access_denied", "invalid_api_key"):
                            code = candidate
                    except (ValueError, AttributeError):
                        pass
                    attempts.append({"attempt": attempt, "error": f"HTTP {status}", "code": code})
                    if status in (401, 403):
                        stop.set()
                    if status not in (408, 429, 500, 502, 503, 504):
                        break
                    time.sleep(min(2 ** attempt, 12))
                    continue
                data = response.json()
                attempt_usage = data.get("usage", {})
                for metric in ("prompt_tokens", "completion_tokens", "total_tokens"):
                    usage[metric] = usage.get(metric, 0) + int(attempt_usage.get(metric, 0) or 0)
                choice = data["choices"][0]
                content = choice["message"].get("content")
                if not isinstance(content, str):
                    raise ValueError("missing text content")
                if choice.get("finish_reason") == "length":
                    rejected.append({"attempt": attempt, "raw_content": content,
                                     "errors": ["truncated completion"], "max_tokens": token_limit})
                    attempts.append({"attempt": attempt, "error": "truncated completion", "max_tokens": token_limit})
                    token_limit = min(token_limit * 2, 65536)
                    continue
                try:
                    result = extract_json_object(content)
                except ValueError:
                    rejected.append({"attempt": attempt, "raw_content": content, "errors": ["invalid JSON"]})
                    attempts.append({"attempt": attempt, "error": "invalid JSON"})
                    messages.extend([
                        {"role": "assistant", "content": content},
                        {"role": "user", "content": "上次输出不能解析为JSON。请修复语法、引号和LaTeX反斜杠转义，重新输出完整的要求结构，不修改数学内容。"},
                    ])
                    continue
                changes = normalize_review_metadata(result)
                errors = content_errors(result, question_id)
                if errors:
                    rejected.append({"attempt": attempt, "result": result, "raw_content": content, "errors": errors})
                    attempts.append({"attempt": attempt, "error": "validation", "details": errors})
                    messages.extend([
                        {"role": "assistant", "content": content},
                        {"role": "user", "content": "请修复以下格式问题，重新输出完整JSON，不省略数学内容：" +
                         json.dumps(errors, ensure_ascii=False)},
                    ])
                    continue
                return {"question_id": question_id, "result": result, "usage": usage,
                        "response_model": data.get("model"), "attempts": attempts,
                        "request_options": {"enable_thinking": payload.get("enable_thinking"), "max_tokens": token_limit},
                        "local_metadata_normalization": changes, "rejected_attempts": rejected,
                        "latency_seconds": round(time.monotonic() - started, 3)}
            except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
                attempts.append({"attempt": attempt, "error": type(exc).__name__})
                if attempt < args.retries:
                    time.sleep(min(2 ** attempt, 12))
    return {"question_id": question_id, "failed": True, "attempts": attempts, "usage": usage,
            "rejected_attempts": rejected}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "datasets/kaoyan/questions.jsonl")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--api-key-env", default="RUBRIC_API_KEY")
    parser.add_argument("--api-key-stdin", action="store_true")
    parser.add_argument("--no-thinking", action="store_true", help="Disable optional thinking on supported providers")
    parser.add_argument("--resume-from", type=Path, help="Import completed records from a matching run on another endpoint")
    parser.add_argument("--allow-model-change-on-resume", action="store_true",
                        help="Preserve completed records when deliberately switching generation models")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-tokens", type=int, default=16000)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--limit", type=int)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.workers < 1 or args.retries < 1 or (args.limit is not None and args.limit < 1):
        parser.error("workers, retries and limit must be positive")
    if args.execute and not args.base_url.startswith("https://"):
        parser.error("API base URL must use HTTPS")
    args.dataset = args.dataset.resolve()
    args.output_dir = ensure_run_output_dir(args.output_dir, ROOT)
    system_path = ROOT / "prompts/subjective_rubric_generator_zh_v1.txt"
    system = system_path.read_text(encoding="utf-8")
    rows = read_jsonl(args.dataset)
    selected = [r for r in rows if r["metadata"]["question_type"] in ("解答题", "证明题")]
    if len({r["id"] for r in rows}) != len(rows):
        raise SystemExit("duplicate source IDs")
    skipped = [{"question_id": r["id"], "reason": "missing_source_solution"}
               for r in selected if not r["answer"]["solution"].strip()]
    eligible = [r for r in selected if r["answer"]["solution"].strip()]
    fingerprints = {}
    for row in eligible:
        images = {ref: hashlib.sha256(resolve_image_path(ref, ROOT, args.dataset).read_bytes()).hexdigest()
                  for ref in image_refs(row)}
        fingerprints[row["id"]] = canonical_hash({"row": row, "images": images})
    manifest = {"model": args.model, "base_url": args.base_url.rstrip("/"),
                "dataset": str(args.dataset), "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
                "prompt_sha256": hashlib.sha256(system.encode()).hexdigest(),
                "source_fingerprints": fingerprints, "max_tokens": args.max_tokens,
                "selected": len(selected), "eligible": len(eligible), "skipped": skipped}
    manifest_path = args.output_dir / "generation_manifest.json"
    if args.no_thinking:
        manifest["enable_thinking"] = False
    if manifest_path.exists() and json.loads(manifest_path.read_text(encoding="utf-8")) != manifest:
        raise SystemExit("input/configuration changed; use a new output directory")
    write_json(manifest_path, manifest)
    journal_path = args.output_dir / "generation_journal.jsonl"
    if args.resume_from and not journal_path.exists():
        previous = args.resume_from.resolve()
        old_manifest = json.loads((previous / "generation_manifest.json").read_text(encoding="utf-8"))
        fields = ["dataset_sha256", "prompt_sha256", "source_fingerprints"]
        if not args.allow_model_change_on_resume:
            fields.append("model")
        for field in fields:
            if old_manifest[field] != manifest[field]:
                raise SystemExit(f"cannot resume: {field} differs")
        imported = {r["question_id"]: r for r in read_jsonl(previous / "generation_journal.jsonl") if not r.get("failed")}
        for row in eligible:
            if row["id"] in imported:
                record = dict(imported[row["id"]])
                record.setdefault("origin_base_url", old_manifest["base_url"])
                append_jsonl(journal_path, record)
        write_json(args.output_dir / "resume_origin.json", {"folder": str(previous), "imported": len(imported),
                   "origin_base_url": old_manifest["base_url"], "origin_model": old_manifest["model"],
                   "model_change_authorized": args.allow_model_change_on_resume})
    existing = read_jsonl(journal_path) if journal_path.exists() else []
    completed = {r["question_id"]: r for r in existing if not r.get("failed")}
    pending = [r for r in eligible if r["id"] not in completed]
    planned = pending[:args.limit] if args.limit else pending
    write_json(args.output_dir / "preflight_report.json", {
        "selected": len(selected), "eligible": len(eligible), "skipped": skipped,
        "already_completed": len(completed), "planned": len(planned),
        "with_images": sum(bool(image_refs(r)) for r in eligible),
        "network_requests": 0 if args.dry_run else None, "workers": args.workers})
    if args.dry_run:
        print(json.dumps({"eligible": len(eligible), "planned": len(planned), "skipped": skipped}, ensure_ascii=False))
        return
    key = getpass.getpass("API key (hidden): ").strip() if args.api_key_stdin else os.getenv(args.api_key_env, "").strip()
    if not key:
        raise SystemExit("API key required via environment or stdin")
    failures = []
    stop = Event()
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(generate, row, args, key, system, stop): row["id"] for row in planned}
        for future in as_completed(futures):
            result = future.result()
            append_jsonl(journal_path, result)
            question_id = result["question_id"]
            if result.get("failed"):
                failures.append(question_id)
                print(json.dumps({"question_id": question_id, "status": "failed", "attempts": result["attempts"]}), flush=True)
            else:
                completed[question_id] = result
                print(json.dumps({"question_id": question_id, "status": "draft",
                                  "completed": len(completed), "needs_review": result["result"]["needs_review"]}), flush=True)
    drafts = [completed[r["id"]]["result"]["rubric_record"] for r in eligible if r["id"] in completed]
    target = args.output_dir / "rubrics.draft.jsonl"
    target.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in drafts), encoding="utf-8")
    reviews = [{"question_id": r["id"], **{k: v for k, v in completed[r["id"]]["result"].items()
                                                if k != "rubric_record"}}
               for r in eligible if r["id"] in completed]
    write_json(args.output_dir / "content_review_flags.json", reviews)
    write_json(args.output_dir / "generation_report.json", {
        "status": "drafts_pending_content_review", "selected": len(selected),
        "eligible": len(eligible), "generated": len(drafts), "skipped": skipped,
        "pending_ids": [r["id"] for r in eligible if r["id"] not in completed],
        "failed_this_run": failures, "flagged_for_review": [r["question_id"] for r in reviews if r["needs_review"]],
        "without_second_solution": sum(r.get("reference_solution_2") is None for r in drafts),
        "usage_all_attempts": {k: sum(r.get("usage", {}).get(k, 0) for r in (read_jsonl(journal_path) if journal_path.exists() else []))
                               for k in ("prompt_tokens", "completion_tokens", "total_tokens")},
        "note": "Structure and score totals checked automatically; mathematical correctness requires content review."})
    print(json.dumps({"generated": len(drafts), "eligible": len(eligible), "failed_this_run": len(failures)}), flush=True)


if __name__ == "__main__":
    main()
