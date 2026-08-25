"""Shared evaluation helpers (P6).

Centralises capabilities that subjective answer generation, judging and
aggregation previously duplicated: environment-variable reading, image path
resolution and data-URL encoding, multimodal message building, request error
classification, usage/token/latency stats and output-directory protection
(never write into datasets/ or reports/).
"""
from __future__ import annotations

import base64
import mimetypes
import os
from pathlib import Path


def load_api_key(env_name: str, *, required: bool = True) -> str | None:
    key = os.getenv(env_name)
    if required and not key:
        raise SystemExit(f"missing environment variable {env_name}")
    return key


def resolve_image_path(ref: str, root: Path, dataset: Path) -> Path:
    path = Path(ref)
    for candidate in (path, Path.cwd() / path, root / path, dataset.parent / path, root / "data" / path):
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(ref)


def image_data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def multimodal_content(text: str, images: list[str], root: Path, dataset: Path) -> str | list[dict]:
    if not images:
        return text
    blocks: list[dict] = [{"type": "text", "text": text}]
    for ref in images:
        blocks.append({"type": "image_url", "image_url": {"url": image_data_url(resolve_image_path(ref, root, dataset))}})
    return blocks


def error_status(exc: Exception) -> int | None:
    return getattr(getattr(exc, "response", None), "status_code", None)


def classify_error(exc: Exception) -> str:
    body = getattr(getattr(exc, "response", None), "text", "") or ""
    return f"{type(exc).__name__}: {exc}; response={body[:1000]}"


def is_image_support_error(exc: Exception) -> bool:
    return error_status(exc) in (400, 415, 422)


def usage_summary(raw_rows: list[dict]) -> dict:
    return {
        "prompt_tokens": sum(int(r.get("usage", {}).get("prompt_tokens", 0) or 0) for r in raw_rows),
        "completion_tokens": sum(int(r.get("usage", {}).get("completion_tokens", 0) or 0) for r in raw_rows),
        "total_tokens": sum(int(r.get("usage", {}).get("total_tokens", 0) or 0) for r in raw_rows),
    }


def latency_total(raw_rows: list[dict]) -> float:
    return sum(float(r.get("latency_seconds", 0) or 0) for r in raw_rows)


def ensure_run_output_dir(path: Path, root: Path) -> Path:
    """Create and return the output dir, refusing paths inside formal dirs."""
    resolved = path.resolve()
    forbidden = [(root / "datasets").resolve(), (root / "reports").resolve()]
    if any(resolved.is_relative_to(f) or resolved == f for f in forbidden):
        raise SystemExit(f"output dir must not be inside datasets/ or reports/: {path}")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved
