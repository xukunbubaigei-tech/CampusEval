"""Tests for the one-command import pipeline (P4).

Covers: deterministic auto-id, source inference, normalization rejection of
empty question/answer, dry-run writing nothing, a real end-to-end import on a
temporary project-root copy (auto id not used here; explicit id + rubric +
image + fixed-mini preservation + README refresh + post-validation), and a failure
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

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/maintenance/import_dataset.py"

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
    def test_choice_import_normalizes_string_options(self):
        mod = _import_script()
        raw = {"id": "gaokao_math_fixture", "source": "gaokao",
               "question": {"text": "选择所有正确选项。", "options": ["甲", "乙", "丙", "丁"]},
               "answer": {"final_answer": "AC", "solution": "甲和丙正确。"},
               "metadata": {"question_type": "多选题", "paper_name": "fixture"}}
        record, errors = mod.normalize({"record": raw}, ROOT, None, {})
        self.assertEqual(errors, [])
        self.assertEqual(record["question"]["options"], [
            {"label": k, "text": v} for k, v in zip("ABCD", ["甲", "乙", "丙", "丁"])])
        validator, _ = mod.schema_validators(ROOT)
        self.assertEqual(list(validator.iter_errors(record)), [])

    def test_umath_preserves_reference_answer_without_inventing_solution(self):
        mod = _import_script()
        raw = {"id": "umath_1",
               "question": {"text": "Evaluate the integral."},
               "answer": {"final_answer": "$1/2$", "solution": ""},
               "metadata": {"question_type": "解答题"}}
        record, errors = mod.normalize({"record": raw}, ROOT, None, {})
        self.assertEqual(errors, [])
        self.assertEqual(record["source"], "umath")
        self.assertEqual(record["metadata"]["paper_name"], "umath")
        self.assertEqual(record["answer"], raw["answer"])
        validator, _ = mod.schema_validators(ROOT)
        self.assertEqual(list(validator.iter_errors(record)), [])

    def test_university_exam_allows_missing_solution_and_falls_back_to_source(self):
        mod = _import_script()
        record, errors = mod.normalize(
            {"record": {"id": "university_kaoyan_1987_math1_01", "source": "university_exam",
                        "question": {"text": "求导数。"},
                        "answer": {"final_answer": "1", "solution": ""},
                        "metadata": {"paper_name": "  ", "question_type": "解答题"}}},
            ROOT, None, {},
        )
        self.assertEqual(errors, [])
        self.assertEqual(record["metadata"]["paper_name"], "university_exam")
        self.assertEqual(record["answer"]["solution"], "")
        validator, _ = mod.schema_validators(ROOT)
        self.assertEqual(list(validator.iter_errors(record)), [])

    def test_existing_sources_still_require_solution(self):
        mod = _import_script()
        record, errors = mod.normalize(
            {"record": {"source": "gaokao", "question": {"text": "求导数。"},
                        "answer": {"final_answer": "1", "solution": ""},
                        "metadata": {"question_type": "解答题"}}}, ROOT, None, {},
        )
        self.assertIsNone(record)
        self.assertTrue(any("requires answer.solution" in e for e in errors))

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
            expected_benchmark_count = len(_load_jsonl(tmp / "datasets/main/benchmark.jsonl")) + 1
            fixed_paths = [tmp / "datasets" / name / "questions.jsonl" for name in ("objective_70", "subjective_50")]
            fixed_paths.append(tmp / "datasets/subjective_50/rubrics.jsonl")
            before = {path: path.read_bytes() for path in fixed_paths}
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
            self.assertEqual(len(bench), expected_benchmark_count)
            new_record = next(r for r in bench if r["id"] == self.NEW_ID)
            self.assertEqual(new_record["question"]["images"],
                             ["data/images/gaokao/" + self.NEW_ID + "_0.png"])
            self.assertTrue((tmp / "data/images/gaokao" / (self.NEW_ID + "_0.png")).is_file())

            subjective = _load_jsonl(tmp / "datasets/subjective_50/questions.jsonl")
            self.assertEqual(len(subjective), 50)
            self.assertNotIn(self.NEW_ID, {r["id"] for r in subjective})

            rubrics = _load_jsonl(tmp / "datasets/subjective_50/rubrics.jsonl")
            self.assertEqual(len(rubrics), 50)
            self.assertFalse(any(r["question_id"] == self.NEW_ID for r in rubrics))
            self.assertEqual(report["imported_rubrics"][0]["question_id"], self.NEW_ID)
            for path, content in before.items():
                self.assertEqual(path.read_bytes(), content)

            readme = (tmp / "datasets/README.md").read_text(encoding="utf-8")
            self.assertIn(f"[main/benchmark.jsonl](main/benchmark.jsonl) | 题目 | {expected_benchmark_count} |", readme)
            self.assertIn("[subjective_50/rubrics.jsonl](subjective_50/rubrics.jsonl) | Rubric | 50 |", readme)
            image_count = sum(p.is_file() for p in (ROOT / "data/images").rglob("*")) + 1
            self.assertIn(f"规范图片 **{image_count} 个文件**", readme)
            self.assertFalse((tmp / "datasets/RELEASE_MANIFEST.json").exists())
            self.assertFalse((tmp / "datasets/VALIDATION_REPORT.json").exists())
            validation = json.loads((tmp / "workspace/reports/dataset_validation.json").read_text(encoding="utf-8"))
            self.assertTrue(validation["ok"])

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
