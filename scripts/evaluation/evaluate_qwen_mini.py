from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

import requests

from CampusEval.evaluation.metrics import score_final


DEFAULT_DATASET = Path("CampusEval/datasets/objective_70/questions.jsonl")
DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        handle.flush()


def resolve_image(path_text: str, dataset: Path) -> Path:
    path = Path(path_text)
    candidates = [path, Path.cwd() / path, dataset.resolve().parent / path, dataset.resolve().parents[2] / path]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError(f"Image not found: {path_text}")


def data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def format_options(options: list) -> str:
    rendered = []
    for index, option in enumerate(options):
        if isinstance(option, dict):
            rendered.append(f"{option.get('label', chr(65 + index))}. {option.get('text', '')}")
        else:
            rendered.append(f"{chr(65 + index)}. {option}")
    return "\n".join(rendered)


def choice_mode(row: dict) -> str | None:
    if row.get("metadata", {}).get("question_type") != "选择题":
        return None
    gold = str(row.get("answer", {}).get("final_answer", "")).strip().upper()
    return "multiple" if re.fullmatch(r"[A-D]{2,4}", gold) else "single"


def build_prompt(row: dict) -> str:
    question = row["question"]
    qtype = row["metadata"]["question_type"]
    option_text = format_options(question.get("options", [])) if qtype == "选择题" else ""
    mode = choice_mode(row)
    if mode == "multiple":
        answer_rule = "本题为多选题，输出所有正确选项字母，按字母顺序排列且不加空格，例如AC。"
    elif mode == "single":
        answer_rule = "本题为单选题，只输出一个选项字母（A/B/C/D）。"
    else:
        answer_rule = "本题为填空题，只输出最终答案。"
    instruction = (
        "你正在参加中国高考数学测试。请独立解题。" + answer_rule
        + "不要在答案标签中写推理过程。最终回复必须严格使用 <answer>最终答案</answer>。"
    )
    return f"{instruction}\n\n题型：{qtype}\n题目：\n{question['text']}\n{option_text}".strip()


def build_content(row: dict, dataset: Path, use_images: bool) -> str | list[dict]:
    prompt = build_prompt(row)
    images = row.get("question", {}).get("images", []) if use_images else []
    if not images:
        return prompt
    content: list[dict] = [{"type": "text", "text": prompt}]
    for image_path in images:
        resolved = resolve_image(image_path, dataset)
        content.append({"type": "image_url", "image_url": {"url": data_url(resolved)}})
    return content


def extract_answer(response: str, qtype: str, mode: str | None = None) -> str:
    tagged = re.search(r"<answer>\s*(.*?)\s*</answer>", response, re.I | re.S)
    value = tagged.group(1).strip() if tagged else response.strip()
    if qtype == "选择题":
        if mode == "multiple":
            letters = re.findall(r"[A-D]", value.upper())
            return "".join(sorted(set(letters))) if letters else value
        match = re.search(r"(?:^|[^A-Z])([A-D])(?:[^A-Z]|$)", value.upper())
        return match.group(1) if match else value
    boxed = re.search(r"\\boxed\{(.+?)\}", value, re.S)
    return boxed.group(1).strip() if boxed else value


def year_from_id(record_id: str) -> str:
    match = re.search(r"(\d{4})", str(record_id))
    return match.group(1) if match else "?"


def call_chat_completions(
    session: requests.Session,
    base_url: str,
    api_key: str,
    model: str,
    content: str | list[dict],
    timeout: float,
    max_tokens: int,
    stream: bool,
    request_deadline: float | None,
    reasoning_effort: str | None,
    thinking_mode: str | None,
    temperature: float,
) -> tuple[str, dict]:
    url = base_url.rstrip("/") + "/chat/completions"
    request_payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是严谨的高考数学解题模型。"},
            {"role": "user", "content": content},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream,
    }
    if stream:
        request_payload["stream_options"] = {"include_usage": True}
    elif not thinking_mode:
        request_payload["enable_thinking"] = False
    if reasoning_effort:
        request_payload["reasoning_effort"] = reasoning_effort
    if thinking_mode:
        request_payload["thinking"] = {"type": thinking_mode}
    response = session.post(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=request_payload,
        stream=stream,
        timeout=timeout,
    )
    response.raise_for_status()
    if stream:
        parts: list[str] = []
        usage: dict = {}
        stream_started = time.monotonic()
        for raw_line in response.iter_lines(decode_unicode=True):
            if request_deadline is not None and time.monotonic() - stream_started > request_deadline:
                response.close()
                raise requests.Timeout(f"stream exceeded total deadline of {request_deadline:g}s")
            if not raw_line or not raw_line.startswith("data:"):
                continue
            data = raw_line[5:].strip()
            if data == "[DONE]":
                break
            event = json.loads(data)
            if event.get("usage"):
                usage = event["usage"]
            choices = event.get("choices") or []
            if choices:
                delta_text = choices[0].get("delta", {}).get("content")
                if delta_text:
                    parts.append(delta_text)
        return "".join(parts), usage
    payload = response.json()
    return payload["choices"][0]["message"]["content"], payload.get("usage", {})


def aggregate(rows: list[dict]) -> dict:
    valid = [row for row in rows if row.get("status") == "ok"]
    correct = sum(bool(row["correct"]) for row in valid)
    by_type: defaultdict[str, Counter] = defaultdict(Counter)
    by_year: defaultdict[str, Counter] = defaultdict(Counter)
    by_modality: defaultdict[str, Counter] = defaultdict(Counter)
    for row in valid:
        for group, key in (
            (by_type, row["question_type"]),
            (by_year, str(row["year"])),
            (by_modality, "with_image" if row["has_image"] else "text_only"),
        ):
            group[key]["count"] += 1
            group[key]["correct"] += int(row["correct"])

    def finish(group: dict[str, Counter]) -> dict:
        return {
            key: {"count": value["count"], "correct": value["correct"], "accuracy": value["correct"] / value["count"]}
            for key, value in sorted(group.items())
        }

    usage_totals: Counter[str] = Counter()
    for row in valid:
        for key, value in row.get("usage", {}).items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                usage_totals[key] += value
    return {
        "requested": len(rows),
        "completed": len(valid),
        "failed": len(rows) - len(valid),
        "correct": correct,
        "accuracy": correct / len(valid) if valid else 0,
        "by_question_type": finish(by_type),
        "by_year": finish(by_year),
        "by_modality": finish(by_modality),
        "total_latency_seconds": round(sum(row.get("latency_seconds", 0) for row in valid), 3),
        "usage": dict(usage_totals),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a Qwen/OpenAI-compatible model on the 70-question mini dataset.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=Path("CampusEval/runs/objective/qwen3.6-27b"))
    parser.add_argument("--model", default=os.getenv("QWEN_MODEL", "qwen3.6-27b"))
    parser.add_argument("--base-url", default=os.getenv("QWEN_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--api-key-env", default="DASHSCOPE_API_KEY")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--temperature", type=float, default=0)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--skip-existing-errors", action="store_true", help="Do not retry IDs already recorded as errors when resuming.")
    parser.add_argument(
        "--retry-empty-answers",
        action="store_true",
        help="When resuming, retry successful rows whose extracted prediction is empty.",
    )
    parser.add_argument("--retry-delay", type=float, default=2)
    parser.add_argument("--stream", action="store_true", help="Use streaming responses; required for Qwen3 thinking mode.")
    parser.add_argument("--request-deadline", type=float, help="Hard total time limit in seconds for one streamed request.")
    parser.add_argument(
        "--reasoning-effort",
        choices=["none", "low", "medium", "high", "xhigh", "max"],
        help="Reasoning strength for models that support the OpenAI reasoning_effort parameter.",
    )
    parser.add_argument(
        "--thinking-mode",
        choices=["enabled", "disabled"],
        help="DeepSeek official thinking toggle, sent as thinking.type.",
    )
    parser.add_argument("--no-images", action="store_true")
    parser.add_argument(
        "--text-only",
        action="store_true",
        help="Exclude every record that references an image; intended for text-only models.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rows = read_jsonl(args.dataset)
    excluded_image_ids: list[str] = []
    if args.text_only:
        excluded_image_ids = [row["id"] for row in rows if row.get("question", {}).get("images")]
        rows = [row for row in rows if not row.get("question", {}).get("images")]
    if args.limit is not None:
        rows = rows[: args.limit]
    if args.dry_run:
        sample = rows[0]
        print(json.dumps({
            "model": args.model,
            "base_url": args.base_url,
            "count": len(rows),
            "text_only": args.text_only,
            "excluded_image_count": len(excluded_image_ids),
            "excluded_image_ids": excluded_image_ids,
            "use_images": not args.no_images and not args.text_only,
            "sample_id": sample["id"],
            "sample_prompt": build_prompt(sample),
        }, ensure_ascii=False, indent=2))
        return

    api_key = os.getenv(args.api_key_env)
    if not api_key:
        raise SystemExit(f"Missing API key environment variable: {args.api_key_env}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = args.output_dir / "predictions.jsonl"
    results_path = args.output_dir / "results.jsonl"
    summary_path = args.output_dir / "summary.json"
    existing_results = read_jsonl(results_path) if results_path.exists() else []
    latest_results = {row["id"]: row for row in existing_results}
    completed_ids = {
        row_id for row_id, row in latest_results.items()
        if (
            row.get("status") == "ok"
            and not (args.retry_empty_answers and not str(row.get("prediction", "")).strip())
        ) or (args.skip_existing_errors and row.get("status") == "error")
    }
    session = requests.Session()
    all_results = list(latest_results.values())

    for index, row in enumerate(rows, 1):
        if row["id"] in completed_ids:
            continue
        started = time.perf_counter()
        raw_response = ""
        usage: dict = {}
        error = None
        for attempt in range(1, args.retries + 1):
            try:
                raw_response, usage = call_chat_completions(
                    session=session,
                    base_url=args.base_url,
                    api_key=api_key,
                    model=args.model,
                    content=build_content(row, args.dataset, not args.no_images and not args.text_only),
                    timeout=args.timeout,
                    max_tokens=args.max_tokens,
                    stream=args.stream,
                    request_deadline=args.request_deadline,
                    reasoning_effort=args.reasoning_effort,
                    thinking_mode=args.thinking_mode,
                    temperature=args.temperature,
                )
                error = None
                break
            except (requests.RequestException, KeyError, ValueError) as exc:
                response_body = ""
                response_obj = getattr(exc, "response", None)
                if response_obj is not None:
                    response_body = (response_obj.text or "")[:2000]
                error = f"{type(exc).__name__}: {exc}" + (f"; response={response_body}" if response_body else "")
                if attempt < args.retries:
                    time.sleep(args.retry_delay * attempt)
        latency = round(time.perf_counter() - started, 3)
        if error is not None:
            result = {"id": row["id"], "status": "error", "error": error, "latency_seconds": latency}
        else:
            mode = choice_mode(row)
            answer = extract_answer(raw_response, row["metadata"]["question_type"], mode)
            prediction = {
                "id": row["id"],
                "answer": answer,
                "raw_response": raw_response,
                "model": args.model,
                "usage": usage,
                "choice_mode": mode,
                "evaluation_protocol": "choice_aware_v2",
            }
            append_jsonl(predictions_path, prediction)
            result = {
                "id": row["id"],
                "status": "ok",
                "question_type": row["metadata"]["question_type"],
                "year": year_from_id(row["id"]),
                "has_image": bool(row["question"].get("images")),
                "prediction": answer,
                "gold": row["answer"]["final_answer"],
                "correct": score_final(answer, row["answer"]["final_answer"]),
                "latency_seconds": latency,
                "usage": usage,
                "choice_mode": mode,
                "evaluation_protocol": "choice_aware_v2",
            }
        append_jsonl(results_path, result)
        all_results = [item for item in all_results if item["id"] != result["id"]]
        all_results.append(result)
        summary = {
            "model": args.model,
            "base_url": args.base_url,
            "evaluation_scope": "text_only" if args.text_only else "all_records",
            "excluded_image_count": len(excluded_image_ids),
            "excluded_image_ids": excluded_image_ids,
            **aggregate(all_results),
        }
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[{index}/{len(rows)}] {row['id']}: {result['status']}" + (f", correct={result['correct']}" if result["status"] == "ok" else ""), flush=True)

    print(json.dumps({
        "model": args.model,
        "base_url": args.base_url,
        "evaluation_scope": "text_only" if args.text_only else "all_records",
        "excluded_image_count": len(excluded_image_ids),
        "excluded_image_ids": excluded_image_ids,
        **aggregate(all_results),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
