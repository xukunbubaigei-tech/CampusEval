import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ROOT / "datasets"

FILES = {
    "benchmark": DATASETS / "main/benchmark.jsonl",
    "training": DATASETS / "main/training.jsonl",
    "objective_70": DATASETS / "objective_70/questions.jsonl",
    "subjective_50": DATASETS / "subjective_50/questions.jsonl",
}
EXPECTED = {"benchmark": 128, "training": 1000, "objective_70": 70, "subjective_50": 50}
KNOWN_SOURCES = {"gaokao", "conic10k", "aime", "university_exam", "umath", "soa"}
BANNED_TOP_LEVEL = {
    "schema_version",
    "dataset_scope",
    "source_class",
    "is_official_gaokao",
    "quality",
    "provenance",
    "rights",
}


def _load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def _source_of_from_script():
    spec = importlib.util.spec_from_file_location(
        "migrate_add_source", ROOT / "scripts/archive/migrate_add_source.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.source_of


class DatasetStructureTests(unittest.TestCase):
    def setUp(self):
        self.records = {label: _load(path) for label, path in FILES.items()}

    def test_counts(self):
        for label, count in EXPECTED.items():
            self.assertEqual(len(self.records[label]), count, label)

    def test_unique_ids(self):
        for label, recs in self.records.items():
            ids = [r["id"] for r in recs]
            self.assertEqual(len(ids), len(set(ids)), f"{label} has duplicate ids")

    def test_source_present_and_valid(self):
        for label, recs in self.records.items():
            for r in recs:
                self.assertIn("source", r, f"{label} {r.get('id')} missing source")
                self.assertIn(
                    r["source"],
                    KNOWN_SOURCES,
                    f"{label} {r.get('id')} bad source {r.get('source')}",
                )

    def test_no_banned_fields(self):
        for label, recs in self.records.items():
            for r in recs:
                for bad in BANNED_TOP_LEVEL:
                    self.assertNotIn(bad, r, f"{label} {r.get('id')} contains banned field {bad}")

    def test_images_relative_and_exist(self):
        refs: set[str] = set()
        for recs in self.records.values():
            for r in recs:
                for img in (r.get("question", {}).get("images") or []):
                    refs.add(img)
        for img in refs:
            self.assertFalse(
                img.startswith("http://") or img.startswith("https://"),
                f"external image reference: {img}",
            )
            self.assertTrue((ROOT / img).is_file(), f"missing image file: {img}")

    def test_migration_idempotent(self):
        source_of = _source_of_from_script()
        for recs in self.records.values():
            for r in recs:
                self.assertEqual(
                    source_of(r["id"]),
                    r["source"],
                    f"source mismatch for {r['id']}",
                )


if __name__ == "__main__":
    unittest.main()
