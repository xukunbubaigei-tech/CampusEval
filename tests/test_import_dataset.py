"""Tests for the one-command import pipeline (P4).

Covers: deterministic auto-id, source inference, normalization rejection of
empty question/answer, dry-run writing nothing, a real end-to-end import on a
temporary project-root copy (auto id not used here; explicit id + rubric +
image + mini rebuild + manifest refresh + post-validation), and a failure
case that leaves the formal data untouched.
"""
import base64
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/import_dataset.py"

TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def _import_script():
    spec = importlib.util.spec_from_file_location("import_dataset", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, cwd=str(ROOT),
    )


def _last_json(text: str) -> dict:
    decoder = json.JSONDecoder()
    index = len(text)
    while True:
        index = text.rfind("{", 0, index)
        if index < 0:
            raise ValueError("no JSON object in output")
        try:
            value, _ = decoder.raw_decode(text[index:])
            return value
        except json.JSONDecodeError:
            continue


def _copy_project(temp: Path) -> None:
    for name in ("datasets", "schemas", "data"):
        shutil.copytree(ROOT / name, temp / name)


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class NormalizeUnitTests(unittest.TestCase):
    def test_auto_id_deterministic(self):
        mod = _import_script()
        record = {"question": {"text": "求 f(x)=x^2 的导数。", "images": []}, "metadata": {"year": 2026}}
        first = mod.auto_id("gaokao", record, 2026)
        second = mod.auto_id("gaokao", record, 2026)
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("gaokao_2026_"))
        self.assertEqual(len(first.split("_")[-1]), 8)

    def test_infer_source(self):
        mod = _import_script()
        self.assertEqual(mod.infer_source({"id": "gaokao_math_2020_x"}, None), "gaokao")
        self.assertEqual(mod.infer_source({"id": "train_conic10k_0001"}, None), "conic10k")
        self.assertEqual(mod.infer_source({}, "aime"), "aime")

    def test_normalize_rejects_empty_question(self):
        mod = _import_script()
        record, errors = mod.normalize(
            {"record": {"source": "gaokao", "answer": {"final_answer": "1"}}},
            ROOT, None, {},
        )
        self.assertIsNone(record)
        self.assertTrue(any("question text" in e for e in errors))


class DryRunTests(unittest.TestCase):
    def test_dry_run_auto_id_and_no_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            imp = Path(tmp) / "imp.jsonl"
            imp.write_text(json.dumps({
                "source": "aime",
                "question": {"text": "求 f(x)=x^2 在 x=1 处的导数。", "images": []},
                "answer": {"final_answer": "2", "solution": "f'(x)=2x，f'(1)=2。"},
                "metadata": {"year": 2025, "question_type": "填空题"},
            }, ensure_ascii=False) + "\n", encoding="utf-8")
            before = (ROOT / "datasets/main/benchmark.jsonl").read_bytes()
            proc = _run(["--imports", str(imp), "--target", "main", "--project-root", str(ROOT), "--dry-run"])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            plan = _last_json(proc.stdout)
            self.assertTrue(plan["dry_run"])
            self.assertEqual(len(plan["new_ids"]), 1)
            self.assertTrue(plan["new_ids"][0].startswith("aime_2025_"))
            self.assertEqual((ROOT / "datasets/main/benchmark.jsonl").read_bytes(), before)


class EndToEndTests(unittest.TestCase):
    NEW_ID = "gaokao_math_2026_import_test_001"

    def _prepare(self, tmp: Path, with_rubric: bool) -> Path:
        _copy_project(tmp)
        imp = tmp / "workspace/imports"
        imp.mkdir(parents=True)
        (imp / "fig.png").write_bytes(TINY_PNG)
        question = {
            "id": self.NEW_ID, "source": "gaokao",
            "question": {"text": "求 f(x)=x^2 的导数并计算 f'(2)。", "images": ["fig.png"], "options": []},
            "answer": {"final_answer": "4", "solution": "f'(x)=2x，f'(2)=4。"},
            "metadata": {"year": 2026, "province": "fixture", "paper_name": "fixture",
                         "subject_variant": "math", "question_type": "解答题"},
        }
        (imp / "q.jsonl").write_text(json.dumps(question, ensure_ascii=False) + "\n", encoding="utf-8")
        ids_path = tmp / "datasets/subjective_50/ids.json"
        ids = json.loads(ids_path.read_text(encoding="utf-8"))
        ids.append(self.NEW_ID)
        ids_path.write_text(json.dumps(ids, ensure_ascii=False, indent=2), encoding="utf-8")
        if with_rubric:
            rubric = {
                "question_id": self.NEW_ID,
                "rubric": "关键知识点：幂函数求导。评分要点（满分20分）：（10分）正确求导 f'(x)=2x；（10分）正确代入 x=2 得 4。评卷提示：按推理给分，等价解法同等认可。",
                "reference_solution_1": "f'(x)=2x，代入 x=2 得 4。",
                "reference_solution_2": "由导数定义求极限 (f(2+h)-f(2))/h=4+h→4。",
            }
            (imp / "rubric.jsonl").write_text(json.dumps(rubric, ensure_ascii=False) + "\n", encoding="utf-8")
        return imp

    def test_full_import_publishes_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            imp = self._prepare(tmp, with_rubric=True)
            proc = _run([
                "--imports", str(imp / "q.jsonl"), "--rubrics", str(imp / "rubric.jsonl"),
                "--target", "main", "--project-root", str(tmp),
            ])
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            reports = sorted((tmp / "workspace/reports").glob("import_report_*.json"))
            self.assertEqual(len(reports), 1)
            report = json.loads(reports[0].read_text(encoding="utf-8"))
            self.assertTrue(report["ok"])

            bench = _load_jsonl(tmp / "datasets/main/benchmark.jsonl")
            self.assertEqual(len(bench), 129)
            new_record = next(r for r in bench if r["id"] == self.NEW_ID)
            self.assertEqual(new_record["question"]["images"],
                             ["data/images/questions/gaokao/" + self.NEW_ID + "_0.png"])
            self.assertTrue((tmp / "data/images/questions/gaokao" / (self.NEW_ID + "_0.png")).is_file())

            subjective = _load_jsonl(tmp / "datasets/subjective_50/questions.jsonl")
            self.assertEqual(len(subjective), 51)
            self.assertIn(self.NEW_ID, {r["id"] for r in subjective})

            rubrics = _load_jsonl(tmp / "datasets/subjective_50/rubrics.jsonl")
            self.assertEqual(len(rubrics), 51)
            self.assertTrue(any(r["question_id"] == self.NEW_ID for r in rubrics))

            manifest = json.loads((tmp / "datasets/RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["counts"]["benchmark"], 129)
            self.assertEqual(manifest["counts"]["subjective_50"], 51)
            self.assertEqual(manifest["counts"]["approved_rubrics"], 51)
            self.assertEqual(manifest["counts"]["images"], 24)
            # post-publish validation report exists and is ok
            self.assertTrue((tmp / "datasets/VALIDATION_REPORT.json").exists())

    def test_missing_rubric_rejected_without_touching_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            imp = self._prepare(tmp, with_rubric=False)
            before = len(_load_jsonl(tmp / "datasets/main/benchmark.jsonl"))
            proc = _run(["--imports", str(imp / "q.jsonl"), "--target", "main", "--project-root", str(tmp)])
            self.assertEqual(proc.returncode, 1)
            after = len(_load_jsonl(tmp / "datasets/main/benchmark.jsonl"))
            self.assertEqual(before, after, "formal data must be untouched on failure")
            reports = list((tmp / "workspace/rejected").glob("import_failure_*.json"))
            self.assertEqual(len(reports), 1)
            report = json.loads(reports[0].read_text(encoding="utf-8"))
            self.assertTrue(any("missing_rubric" in r.get("error_type", "") for r in report["records"]))


if __name__ == "__main__":
    unittest.main()
