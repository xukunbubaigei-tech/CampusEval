import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
RUBRICS = ROOT / "datasets/subjective_50/rubrics.jsonl"
QUESTIONS = ROOT / "datasets/subjective_50/questions.jsonl"
SCHEMA = ROOT / "schemas/subjective_rubric.schema.json"


def _load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


class SubjectiveRubricTests(unittest.TestCase):
    def setUp(self):
        self.rubrics = _load(RUBRICS)
        self.questions = _load(QUESTIONS)
        self.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.validator = Draft202012Validator(self.schema)

    def test_count_and_ids_match(self):
        self.assertEqual(len(self.rubrics), 50)
        sub_ids = {r["id"] for r in self.questions}
        rubric_ids = {r["question_id"] for r in self.rubrics}
        self.assertEqual(sub_ids, rubric_ids)
        self.assertEqual(len(rubric_ids), 50)

    def test_schema_valid(self):
        for r in self.rubrics:
            errs = list(self.validator.iter_errors(r))
            self.assertEqual(
                errs,
                [],
                f"schema errors for {r.get('question_id')}: {[e.message for e in errs]}",
            )

    def test_fields_present(self):
        for r in self.rubrics:
            self.assertTrue(r["question_id"])
            self.assertTrue(r["rubric"])
            self.assertTrue(r["reference_solution_1"])
            s2 = r.get("reference_solution_2")
            self.assertTrue(s2 is None or s2.strip(), f"empty solution2 for {r['question_id']}")

    def test_no_old_fields(self):
        banned = {
            "scoring_items",
            "knowledge_points",
            "generator_model",
            "max_score",
            "review_status",
            "prompt_version",
            "rubric_version",
            "source_hash",
            "created_at",
        }
        for r in self.rubrics:
            for bad in banned:
                self.assertNotIn(bad, r, f"{r['question_id']} still has {bad}")

    def test_solutions_distinct(self):
        identical = [
            r["question_id"]
            for r in self.rubrics
            if r.get("reference_solution_2") is not None
            and r["reference_solution_2"] == r["reference_solution_1"]
        ]
        self.assertEqual(identical, [], f"identical solutions: {identical}")

    def test_unified_20_point_scale(self):
        for r in self.rubrics:
            self.assertIn("满分20分", r["rubric"], f"{r['question_id']} rubric missing 满分20分")


if __name__ == "__main__":
    unittest.main()
