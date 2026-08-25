"""Tests for the workspace isolation rules (P5)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/clean_workspace.py"

TRANSIENT = ("staging", "extracted", "reports", "rejected")
KEEP = ("imports", "review")


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, cwd=str(ROOT),
    )


def _make(tmp: Path) -> None:
    for name in TRANSIENT + KEEP:
        (tmp / "workspace" / name).mkdir(parents=True, exist_ok=True)
    (tmp / "datasets").mkdir(parents=True, exist_ok=True)
    (tmp / "reports").mkdir(parents=True, exist_ok=True)
    (tmp / "workspace/staging/a.json").write_text("{}", encoding="utf-8")
    (tmp / "workspace/extracted/b.md").write_text("x", encoding="utf-8")
    (tmp / "workspace/reports/c.json").write_text("{}", encoding="utf-8")
    (tmp / "workspace/rejected/d.json").write_text("{}", encoding="utf-8")
    (tmp / "workspace/imports/keep.json").write_text("{}", encoding="utf-8")
    (tmp / "workspace/review/e.md").write_text("x", encoding="utf-8")
    (tmp / "datasets/benchmark.jsonl").write_text("line\n", encoding="utf-8")
    (tmp / "reports/formal.md").write_text("keep", encoding="utf-8")


class CleanWorkspaceTests(unittest.TestCase):
    def test_dry_run_lists_but_keeps_everything(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            _make(tmp)
            proc = _run(["--project-root", str(tmp), "--dry-run"])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            report = json.loads(proc.stdout)
            self.assertTrue(report["dry_run"])
            self.assertEqual(len(report["deleted_files"]), 3)  # default: staging/extracted/reports
            self.assertTrue((tmp / "workspace/staging/a.json").exists())
            self.assertTrue((tmp / "workspace/extracted/b.md").exists())
            self.assertTrue((tmp / "workspace/reports/c.json").exists())
            self.assertTrue((tmp / "workspace/rejected/d.json").exists(), "rejected not in default scope")

    def test_default_clean_keeps_rejected_imports_review_and_formal(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            _make(tmp)
            proc = _run(["--project-root", str(tmp)])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            for name in ("staging", "extracted", "reports"):
                self.assertFalse((tmp / "workspace" / name).exists(), f"{name} should be cleaned")
            self.assertTrue((tmp / "workspace/rejected/d.json").exists(), "rejected kept by default")
            self.assertTrue((tmp / "workspace/imports/keep.json").exists())
            self.assertTrue((tmp / "workspace/review/e.md").exists())
            self.assertEqual((tmp / "datasets/benchmark.jsonl").read_text(encoding="utf-8"), "line\n")
            self.assertEqual((tmp / "reports/formal.md").read_text(encoding="utf-8"), "keep")

    def test_explicit_scope_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            _make(tmp)
            proc = _run(["--project-root", str(tmp), "--scope", "rejected"])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertFalse((tmp / "workspace/rejected").exists())
            self.assertTrue((tmp / "workspace/staging/a.json").exists(), "staging untouched")


if __name__ == "__main__":
    unittest.main()
