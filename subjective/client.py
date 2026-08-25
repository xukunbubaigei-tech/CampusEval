from __future__ import annotations

import json
import time

import requests


class SwitchableModelError(RuntimeError):
    pass


def chat_completion(session: requests.Session, base_url: str, api_key: str, model: str,
                    prompt: str | list[dict], timeout: float = 180, max_tokens: int = 8192,
                    enable_thinking: bool | None = None,
                    thinking_budget: int | None = None,
                    reasoning_effort: str | None = None) -> tuple[str, dict, float]:
    started = time.perf_counter()
    request_payload = {"model": model, "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0, "max_tokens": max_tokens,
                       "response_format": {"type": "json_object"}}
    if enable_thinking is not None:
        request_payload["enable_thinking"] = enable_thinking
    if thinking_budget is not None:
        request_payload["thinking_budget"] = thinking_budget
    if reasoning_effort is not None:
        request_payload["reasoning_effort"] = reasoning_effort
    response = session.post(
        base_url.rstrip("/") + "/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=request_payload,
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    return payload["choices"][0]["message"]["content"], payload.get("usage", {}), round(time.perf_counter() - started, 3)


def is_switchable_error(exc: Exception, config: dict) -> bool:
    status = getattr(getattr(exc, "response", None), "status_code", None)
    if status in config.get("switchable_http_statuses", []):
        return True
    text = str(exc).lower()
    return any(marker.lower() in text for marker in config.get("switchable_error_markers", []))
