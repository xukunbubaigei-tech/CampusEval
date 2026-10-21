"""Tests for the shared evaluation helpers (P6)."""
import base64
import os
import tempfile
import unittest
from pathlib import Path

from CampusEval.subjective.common import (ensure_run_output_dir, image_data_url,
                                                     latency_total, load_api_key, multimodal_content,
                                                     resolve_image_path, usage_summary)

ROOT = Path(__file__).resolve().parents[2]
TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


class CommonHelperTests(unittest.TestCase):
    def test_load_api_key(self):
        os.environ["TEST_GK_KEY"] = "k"
        self.assertEqual(load_api_key("TEST_GK_KEY"), "k")
        os.environ.pop("TEST_GK_KEY", None)
        with self.assertRaises(SystemExit):
            load_api_key("TEST_GK_KEY_MISSING")

    def test_resolve_and_encode_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "data").mkdir(parents=True)
            img = tmp / "data/fig.png"
            img.write_bytes(TINY_PNG)
            resolved = resolve_image_path("data/fig.png", tmp, tmp / "datasets/q.jsonl")
            self.assertEqual(resolved, img.resolve())
            url = image_data_url(resolved)
            self.assertTrue(url.startswith("data:image/png;base64,"))
            self.assertEqual(base64.b64decode(url.split(",", 1)[1]), TINY_PNG)

    def test_multimodal_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "data").mkdir(parents=True)
            (tmp / "data/fig.png").write_bytes(TINY_PNG)
            plain = multimodal_content("题目", [], tmp, tmp / "datasets/q.jsonl")
            self.assertIsInstance(plain, str)
            blocks = multimodal_content("题目", ["data/fig.png"], tmp, tmp / "datasets/q.jsonl")
            self.assertIsInstance(blocks, list)
            self.assertEqual(blocks[0]["type"], "text")
            self.assertTrue(blocks[1]["image_url"]["url"].startswith("data:image/png;base64,"))

    def test_stats(self):
        raw = [
            {"usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}, "latency_seconds": 1.5},
            {"usage": {"prompt_tokens": 20, "completion_tokens": 5, "total_tokens": 25}, "latency_seconds": 2.5},
        ]
        usage = usage_summary(raw)
        self.assertEqual(usage["total_tokens"], 40)
        self.assertEqual(latency_total(raw), 4.0)

    def test_output_dir_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            ok = ensure_run_output_dir(tmp / "runs/x", tmp)
            self.assertTrue(ok.is_dir())
            with self.assertRaises(SystemExit):
                ensure_run_output_dir(tmp / "reports/x", tmp)
            with self.assertRaises(SystemExit):
                ensure_run_output_dir(tmp / "datasets/x", tmp)


if __name__ == "__main__":
    unittest.main()
