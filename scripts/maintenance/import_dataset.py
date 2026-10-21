"""One-command import pipeline for new questions (P4).

Ingests JSON / JSONL records (or a directory under ``workspace/imports``),
normalizes them into the canonical four-field shape (+ ``source``), auto-
generates ids when missing, copies image files into ``data/images``, attaches
rubrics for subjective questions, validates everything against a staging copy,
and only then publishes to main/training, preserves the fixed mini datasets
and their rubrics, refreshes ``datasets/README.md`` and runs the
offline release validation.

Atomicity: all new files are written under ``workspace/staging`` first; if any
check fails the formal data is untouched and a failure report is written to
``workspace/rejected``. ``--dry-run`` prints the plan and writes nothing.

PDF extraction uses the MinerU website (https://mineru.net/), precise parsing,
and JSON download into a content-named subdirectory directly under workspace/.
Convert and review those raw results into canonical question JSON/JSONL first;
this importer does not directly ingest MinerU layout JSON. See workspace/README.md.

Run::

    .venv/Scripts/python scripts/maintenance/import_dataset.py --imports workspace/imports/2026.jsonl
    .venv/Scripts/python scripts/maintenance/import_dataset.py --imports workspace/imports --dry-run
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

from jsonschema import Draft202012Validator  # noqa: E402
from CampusEval.scripts.maintenance.update_dataset_readme import write_dataset_readme  # noqa: E402

KNOWN_SOURCES = {"gaokao", "conic10k", "aime", "university_exam", "umath", "soa"}
SUBJECTIVE_TYPES = {"解答题", "证明题", "综合题", "压轴题"}
MINI_NAMES = ("objective_70", "subjective_50")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def load_input_entries(paths: list[Path]) -> list[dict]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(sorted(p for p in path.rglob("*") if p.suffix in (".json", ".jsonl") and not p.name.startswith(".")))
        elif path.is_file():
            files.append(path)
        else:
            raise SystemExit(f"input not found: {path}")
    if not files:
        raise SystemExit("no JSON/JSONL input files found")
    entries: list[dict] = []
    for file in files:
        if file.suffix == ".jsonl":
            rows = [json.loads(line) for line in file.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
        else:
            data = json.loads(file.read_text(encoding="utf-8-sig"))
            rows = data.get("questions", data) if isinstance(data, dict) else data
            if isinstance(rows, dict):
                rows = [rows]
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise SystemExit(f"{file}: record {index} is not a JSON object")
            entries.append({"input_file": str(file), "index": index, "record": row})
    return entries


def infer_source(record: dict, source_hint: str | None) -> str | None:
    rid = record.get("id", "")
    for prefix, source in (("gaokao_math_", "gaokao"), ("train_conic10k_", "conic10k"),
                           ("conic10k_", "conic10k"), ("train_", "gaokao"),
                           ("aime_", "aime"), ("university_", "university_exam"),
                           ("umath_", "umath"), ("soa_p_", "soa")):
        if rid.startswith(prefix):
            return source
    return source_hint


def auto_id(source: str, record: dict, year: int | None) -> str:
    question = record.get("question", {})
    text = question.get("text", "") if isinstance(question, dict) else str(question)
    slug = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
    return f"{source}_{year or 'undated'}_{slug}"


def image_plan(ref: str, record_id: str, index: int, input_file: str, root: Path) -> tuple[Path | None, str | None]:
    if ref.startswith(("http://", "https://")):
        return None, f"{record_id}: external URL images are not allowed: {ref}"
    candidate = Path(ref)
    if candidate.is_absolute():
        return (candidate, None) if candidate.is_file() else (None, f"{record_id}: image file not found: {ref}")
    bases = [root, Path(input_file).parent, root / "workspace/imports"]
    for base in bases:
        resolved = (base / ref).resolve()
        if resolved.is_file():
            return resolved, None
    return None, f"{record_id}: image file not found: {ref}"


def normalize(entry: dict, root: Path, source_hint: str | None,
              image_files: dict[str, Path]) -> tuple[dict | None, list[str]]:
    """Return (canonical_record, failures). Copies are planned into image_files
    mapping target repo-relative path -> source file, without writing yet."""
    raw = dict(entry["record"])
    input_file = entry.get("input_file", "?")
    index = entry.get("index", "?")
    fails: list[str] = []
    source = raw.get("source") or infer_source(raw, source_hint)
    if not source or source not in KNOWN_SOURCES:
        return None, [f"{input_file}#{index}: invalid or missing source"]

    question_raw = raw.get("question", {})
    if not isinstance(question_raw, dict) or not question_raw.get("text", "").strip():
        return None, [f"{input_file}#{index}: question text is empty"]
    answer_raw = raw.get("answer", {})
    if not isinstance(answer_raw, dict) or not answer_raw.get("final_answer", "").strip():
        return None, [f"{input_file}#{index}: answer.final_answer is empty"]

    metadata_raw = raw.get("metadata", {})
    year = metadata_raw.get("year") if isinstance(metadata_raw, dict) else None
    record_id = raw.get("id") or auto_id(source, raw, year)
    if not isinstance(record_id, str) or not record_id.strip():
        return None, [f"{input_file}#{index}: failed to build id"]

    question_type = (metadata_raw.get("question_type") if isinstance(metadata_raw, dict)
                     else "解答题") or "解答题"
    solution = answer_raw.get("solution", "").strip()
    if question_type in SUBJECTIVE_TYPES and not solution and source not in {"university_exam", "umath"}:
        return None, [f"{record_id}: subjective question requires answer.solution"]

    images: list[str] = []
    for index, ref in enumerate(question_raw.get("images") or []):
        if not isinstance(ref, str) or not ref.strip():
            continue
        src, error = image_plan(ref, record_id, index, input_file, root)
        if error:
            fails.append(error)
            continue
        suffix = Path(ref).suffix or ".png"
        target_rel = f"data/images/{source}/{record_id}_{index}{suffix}"
        existing = image_files.get(target_rel)
        if existing is not None and existing.read_bytes() != src.read_bytes():
            digest = hashlib.sha256(src.read_bytes()).hexdigest()[:8]
            target_rel = f"data/images/{source}/{record_id}_{index}_{digest}{suffix}"
        image_files[target_rel] = src
        images.append(target_rel)
    if fails:
        return None, fails

    record = {
        "id": record_id,
        "source": source,
        "question": {
            "text": question_raw["text"].strip(),
            "images": images,
            "options": [{"label": chr(65+i), "text": option} if isinstance(option, str) else option
                        for i, option in enumerate(question_raw.get("options") or [])],
        },
        "answer": {
            "final_answer": answer_raw["final_answer"].strip(),
            "solution": solution,
        },
        "metadata": {
            "paper_name": ((metadata_raw.get("paper_name") or "").strip()
                           if isinstance(metadata_raw, dict) else "") or source,
            "question_type": question_type,
        },
    }
    return record, []


def schema_validators(root: Path) -> tuple[Draft202012Validator, Draft202012Validator]:
    dataset = json.loads((root / "schemas/dataset.schema.json").read_text(encoding="utf-8"))
    rubric = json.loads((root / "schemas/subjective_rubric.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(dataset), Draft202012Validator(rubric)


def staged_errors(root: Path, main_records: list[dict], training_records: list[dict],
                  rubrics: list[dict], image_files: dict[str, Path]) -> list[str]:
    dataset_validator, rubric_validator = schema_validators(root)
    errors: list[str] = []
    all_records = main_records + training_records
    seen: dict[str, str] = {}
    for record in all_records:
        first = next(dataset_validator.iter_errors(record), None)
        if first is not None:
            errors.append(f"schema error for {record.get('id')}: {first.message}")
        if record["id"] in seen:
            errors.append(f"duplicate id across datasets: {record['id']}")
        seen[record["id"]] = record["id"]
        serialized = json.dumps(record, ensure_ascii=False).lower()
        if "http://" in serialized or "https://" in serialized:
            errors.append(f"external URL found in {record.get('id')}")

    for rubric in rubrics:
        first = next(rubric_validator.iter_errors(rubric), None)
        if first is not None:
            errors.append(f"rubric schema error for {rubric.get('question_id')}: {first.message}")
        if not rubric.get("rubric") or not rubric.get("reference_solution_1"):
            errors.append(f"rubric incomplete for {rubric.get('question_id')}")

    all_by_id = {r["id"]: r for r in all_records}
    for name in MINI_NAMES:
        path = root / "datasets" / name / "questions.jsonl"
        if not path.exists():
            continue
        for record in read_jsonl(path):
            if all_by_id.get(record["id"]) != record:
                errors.append(f"{name}: fixed record differs from main: {record['id']}")

    sub_path = root / "datasets/subjective_50/questions.jsonl"
    if sub_path.exists():
        sub_ids = {r["id"] for r in read_jsonl(sub_path)}
        rubric_ids = {r["question_id"] for r in rubrics}
        if sub_ids != rubric_ids or len(rubric_ids) != len(rubrics):
            errors.append("subjective_50 question IDs / rubric IDs mismatch or duplicate rubrics")

    refs = {img for record in all_records for img in (record.get("question", {}).get("images") or [])}
    missing_images = sorted(img for img in refs if img not in image_files)
    errors.extend(f"missing image: {img}" for img in missing_images)
    return errors


def write_failure_report(root: Path, stage: str, failures: list[dict]) -> Path:
    report_dir = root / "workspace/rejected"
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"import_failure_{time.strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps({"stage": stage, "records": failures}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--imports", nargs="+", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--target", choices=["main", "training"], default="main")
    parser.add_argument("--source", default=None, help="source hint when records carry none")
    parser.add_argument("--rubrics", type=Path, default=None, help="JSONL of new rubric records (question_id/rubric/solutions)")
    parser.add_argument("--keep-staging", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = args.project_root.resolve()
    main_path = root / "datasets/main/benchmark.jsonl"
    training_path = root / "datasets/main/training.jsonl"
    rubrics_path = root / "datasets/subjective_50/rubrics.jsonl"

    existing_main = read_jsonl(main_path)
    existing_training = read_jsonl(training_path)
    existing_rubrics = read_jsonl(rubrics_path)
    existing_ids = {r["id"] for r in existing_main + existing_training}

    entries = load_input_entries(args.imports)
    image_files: dict[str, Path] = {}
    new_records: list[dict] = []
    failures: list[dict] = []
    for entry in entries:
        record, errors = normalize(entry, root, args.source, image_files)
        if errors:
            failures.extend({"stage": "normalize", "question_id": entry["record"].get("id"),
                             "input_file": entry["input_file"], "error_type": "normalize",
                             "message": error, "action_required": "fix input record and re-run"}
                            for error in errors)
            continue
        if record["id"] in existing_ids:
            failures.append({"stage": "normalize", "question_id": record["id"],
                             "input_file": entry["input_file"], "error_type": "duplicate_id",
                             "message": f"id already exists in formal data: {record['id']}",
                             "action_required": "provide a different id or remove the existing record"})
            continue
        existing_ids.add(record["id"])
        new_records.append(record)

    new_rubrics: list[dict] = []
    if args.rubrics is not None:
        for rubric in read_jsonl(args.rubrics):
            new_rubrics.append(rubric)
    new_main = existing_main + new_records if args.target == "main" else existing_main
    new_training = existing_training + new_records if args.target == "training" else existing_training
    staged_rubrics = existing_rubrics  # Fixed subjective subset is never expanded by import.
    _, rubric_validator = schema_validators(root)
    for rubric in new_rubrics:
        for error in rubric_validator.iter_errors(rubric):
            failures.append({"stage": "validate", "question_id": rubric.get("question_id"),
                             "input_file": "rubrics", "error_type": "rubric_schema",
                             "message": error.message, "action_required": "fix rubric input"})

    subjective_new = [r for r in new_records if r["metadata"]["question_type"] in SUBJECTIVE_TYPES]
    new_rubric_ids = {r["question_id"] for r in new_rubrics}
    for record in subjective_new:
        if record["id"] not in new_rubric_ids:
            failures.append({"stage": "validate", "question_id": record["id"],
                             "input_file": "rubrics", "error_type": "missing_rubric",
                             "message": f"subjective question lacks a rubric: {record['id']}",
                             "action_required": "provide a rubric record via --rubrics"})

    plan = {
        "project_root": str(root), "target": args.target,
        "input_files": sorted({e["input_file"] for e in entries}),
        "new_records": len(new_records),
        "new_ids": [r["id"] for r in new_records],
        "images_to_copy": len(image_files),
        "new_rubrics": len(new_rubrics),
        "planned_target_count": len(new_main) if args.target == "main" else len(new_training),
        "dry_run": args.dry_run,
        "failures": failures,
    }
    print(json.dumps(plan, ensure_ascii=False, indent=2))

    if failures:
        if not args.dry_run:
            path = write_failure_report(root, "normalize", failures)
            print(f"[FAIL] {len(failures)} failure(s); formal data untouched. report: {path}")
        else:
            print(f"[FAIL] {len(failures)} failure(s); dry-run, nothing written")
        return 1
    if args.dry_run:
        print("[DRY-RUN] no files written")
        return 0

    staging = root / "workspace/staging" / time.strftime("%Y%m%d_%H%M%S")
    try:
        write_jsonl(staging / "datasets/main/benchmark.jsonl", new_main)
        write_jsonl(staging / "datasets/main/training.jsonl", new_training)
        for rel, src in image_files.items():
            target = staging / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
        staged_image_files = {rel: staging / rel for rel in image_files}
        existing_image_files = {p.relative_to(root).as_posix(): p
                                for p in (root / "data/images").rglob("*") if p.is_file()}
        staged_image_files.update(existing_image_files)

        errors = staged_errors(root, new_main, new_training, staged_rubrics, staged_image_files)
        if errors:
            failure_records = [{"stage": "validate", "question_id": None, "input_file": "staging",
                                "error_type": "staged_validation", "message": error,
                                "action_required": "fix the reported problem and re-run"} for error in errors]
            path = write_failure_report(root, "validate", failure_records)
            print(f"[FAIL] staged validation: {len(errors)} error(s); formal data untouched. report: {path}")
            for error in errors:
                print("  -", error)
            return 1

        # publish images
        for rel, src in image_files.items():
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
        # atomic jsonl replacement
        os.replace(staging / "datasets/main/benchmark.jsonl", main_path)
        os.replace(staging / "datasets/main/training.jsonl", training_path)
        write_dataset_readme(root)

        final = subprocess.run(
            [sys.executable, str(ROOT / "scripts/maintenance/validate_clean_release.py"), "--project-root", str(root)],
            capture_output=True, text=True,
        )
        report_dir = root / "workspace/reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report = {
            "stage": "publish",
            "ok": final.returncode == 0,
            "new_records": len(new_records),
            "new_ids": [r["id"] for r in new_records],
            "images_copied": len(image_files),
            "imported_rubrics": new_rubrics,  # Retain inputs outside the fixed 50-rubric set.
            "target_count": len(new_main) if args.target == "main" else len(new_training),
            "post_validation_exit": final.returncode,
            "post_validation": json.loads(final.stdout or "{}"),
        }
        report_path = report_dir / f"import_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if final.returncode != 0:
            print("[WARN] post-publish validation reported problems:", final.stdout[-2000:])
            return 2
        print(f"[OK] imported {len(new_records)} record(s); report: {report_path}")
        return 0
    finally:
        if not args.keep_staging and staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
