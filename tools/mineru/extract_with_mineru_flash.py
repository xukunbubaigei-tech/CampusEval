from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path

import requests


BASE_URL = "https://mineru.net/api/v1/agent"


def json_request(url: str, *, method: str = "GET", payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def extract(pdf: Path, output_dir: Path, timeout: int, page_range: str | None) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    request_options = {
        "file_name": pdf.name,
        "language": "ch",
        "enable_table": True,
        "is_ocr": True,
        "enable_formula": True,
    }
    if page_range:
        request_options["page_range"] = page_range
    submission = json_request(
        f"{BASE_URL}/parse/file",
        method="POST",
        payload=request_options,
    )
    if submission.get("code") != 0:
        raise RuntimeError(f"MinerU submission failed: {submission}")
    task_id = submission["data"]["task_id"]
    file_url = submission["data"]["file_url"]
    with pdf.open("rb") as handle:
        upload = requests.put(file_url, data=handle, timeout=120)
    if upload.status_code not in (200, 201):
        raise RuntimeError(f"MinerU upload failed: HTTP {upload.status_code}: {upload.text[:500]}")

    started = time.monotonic()
    status = None
    while time.monotonic() - started < timeout:
        status = json_request(f"{BASE_URL}/parse/{task_id}")
        data = status.get("data", {})
        if data.get("state") == "done":
            markdown_url = data["markdown_url"]
            with urllib.request.urlopen(markdown_url, timeout=60) as response:
                markdown = response.read().decode("utf-8")
            (output_dir / f"{pdf.stem}.md").write_text(markdown, encoding="utf-8")
            break
        if data.get("state") == "failed":
            raise RuntimeError(f"MinerU parsing failed: {status}")
        time.sleep(3)
    else:
        raise TimeoutError(f"MinerU task timed out: {task_id}; last status={status}")

    receipt = {
        "source_file": str(pdf.resolve()),
        "service": "MinerU Agent lightweight parsing API",
        "endpoint": f"{BASE_URL}/parse/file",
        "task_id": task_id,
        "request_options": request_options,
        "final_status": status,
    }
    (output_dir / f"{pdf.stem}.receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"file": pdf.name, "task_id": task_id, "state": "done"}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload a PDF to MinerU's token-free remote Flash API")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--page-range", help="Optional MinerU page range, for example 10-20")
    args = parser.parse_args()
    extract(args.pdf, args.output_dir, args.timeout, args.page_range)


if __name__ == "__main__":
    main()
