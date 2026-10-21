# CampusEval: Multi-Source Mathematics Datasets and Model Evaluation

English | [简体中文](README.zh-CN.md)

CampusEval grew out of a Gaokao mathematics benchmark and now includes Chinese Gaokao, Conic10K, and postgraduate entrance Mathematics I problems, together with English MIT, SOA, and U-MATH data. It supports dataset access, training data preparation, and model evaluation. The project and repository directory are named `CampusEval`.

As of **2026-10-21**, the six primary data files contain **3,896 records** with unique IDs. The repository also retains fixed subsets of 70 objective and 50 subjective questions with 50 corresponding rubrics, plus **958 new rubrics** for the Kaoyan and main datasets. The mini subsets belong to the primary datasets and must not be counted again; different rubric files may cover the same question. Unique IDs do not establish semantic deduplication across sources.

## Current Data

| Dataset | Records | Published file | Coverage and limitations |
|---|---:|---|---|
| Gaokao Benchmark | 128 | [benchmark.jsonl](datasets/main/benchmark.jsonl) | Chinese Gaokao evaluation set; all records have worked solutions |
| Existing training set | 1,000 | [training.jsonl](datasets/main/training.jsonl) | 566 GAOKAO-Bench and 434 Conic10K records; no authoritative review of every question |
| Kaoyan Mathematics I | 805 | [questions.jsonl](datasets/kaoyan/questions.jsonl) | Selected local materials from 1987–2023; 47 empty solutions; incomplete coverage of Mathematics I, II, and III papers |
| MIT | 146 | [questions.jsonl](datasets/MIT/questions.jsonl) | English examinations and exercises from four MIT OCW courses; all have worked solutions |
| SOA | 718 | [questions.jsonl](datasets/SOA/questions.jsonl) | English Exam P sample questions with five options, A–E; all have solutions |
| U-MATH | 1,099 | [questions.jsonl](datasets/U-MATH/questions.jsonl) | 19 records corrected and one missing-table problem removed; final answers come from `golden_answer`; all `solution` fields are empty and do not provide independent derivations |
| Objective mini | 70 | [questions.jsonl](datasets/objective_70/questions.jsonl) | Fixed Gaokao subset: 50 choice questions, including multiple-choice, and 20 fill-in questions; 62 without question images and 8 with images |
| Subjective mini | 50 | [questions.jsonl](datasets/subjective_50/questions.jsonl) | Fixed subset: 36 Gaokao and 14 Conic10K questions; 5 include question images |
| Fixed subjective rubrics | 50 | [rubrics.jsonl](datasets/subjective_50/rubrics.jsonl) | Plain-text scoring criteria and two reference solutions on an experimental 20-point scale, not official examination point allocations |
| Kaoyan rubrics | 322 | [rubrics.jsonl](datasets/kaoyan/rubrics.jsonl) | Written-response and proof questions with source solutions |
| Benchmark rubrics | 36 | [benchmark.rubrics.jsonl](datasets/main/benchmark.rubrics.jsonl) | All written-response and proof questions in the benchmark |
| Training rubrics | 600 | [training.rubrics.jsonl](datasets/main/training.rubrics.jsonl) | All written-response questions in the training set |

New rubrics use a common experimental **20-point scale** and contain plain-text scoring criteria and reference solutions. `kaoyan_math1_2022_03_19` was skipped because its source solution is empty; MIT and U-MATH do not yet have accompanying rubric files. The 958 new rubrics have passed structural checks, with only a sample reviewed for content. The [data maintenance summary](datasets/MAINTENANCE.md) records 2 known mathematical or scoring issues, 8 incomplete second solutions, and pending dataset answer updates; these remain unresolved. Generation or structural validation does not establish mathematical correctness.

See the [Kaoyan](datasets/kaoyan/README.md), [MIT](datasets/MIT/README.md), and [SOA](datasets/SOA/README.md) notes for preparation methods and quality limitations. See the [U-MATH notes](datasets/U-MATH/README.md) for corrections and usage limitations; its original license is retained.

There are **311 image files**, all under `data/images/`: 23 for Gaokao, 71 for Kaoyan, 17 for MIT, and 200 for U-MATH. These include both question and solution figures; SOA currently has no image references. Paths are relative to the project root. Retain the referenced images and directory structure when copying datasets.

## Using the Data

Question files use UTF-8 JSONL, with one JSON object per line and five top-level fields:

| Field | Description |
|---|---|
| `id` | Question identifier linking model answers, rubrics, and grading results |
| `source` | Currently `gaokao`, `conic10k`, `university_exam`, `soa`, or `umath`; Kaoyan and MIT share `university_exam` and must be distinguished by directory, ID, and paper name |
| `question` | Question `text`, an `images` path array, and an `options` array |
| `answer` | `final_answer` and worked `solution`; empty solutions in Kaoyan and U-MATH are retained as provided |
| `metadata` | `paper_name` for the material or examination and `question_type` |

Rubrics link to questions through `question_id`; their remaining fields are `rubric`, `reference_solution_1`, and `reference_solution_2`. The second solution may be `null`.

Reading existing datasets does not require running construction scripts. For example, from the repository's parent directory:

```python
import json
from pathlib import Path

path = Path("CampusEval/datasets/SOA/questions.jsonl")
with path.open(encoding="utf-8") as stream:
    questions = [json.loads(line) for line in stream if line.strip()]
```

The existing training set and subjective mini share **14 question IDs**. Before evaluating a model trained on this training set, exclude overlapping records and check for identical or similar problems with different IDs. The six primary datasets have not been repartitioned into a unified training, validation, and test split; do not assume that every question is an independent test sample.

## Repository Layout

```text
CampusEval/
├── README.md       English overview (default GitHub landing page)
├── README.zh-CN.md Chinese overview with matching sections
├── datasets/       Published datasets, fixed mini subsets, rubrics, inventory, and source notes
├── data/images/    Images referenced by questions and solutions
├── scripts/        Entry points and maintenance tools organized by responsibility
│   ├── evaluation/   Model answers, rubric generation, grading, aggregation, and local rescoring
│   ├── maintenance/  Imports, inventory updates, integrity checks, and workspace cleanup
│   ├── construction/ Source-specific conversion and construction tools
│   ├── checks/       Kaoyan and SOA source-specific validation
│   ├── tests/        Regression tests and optional source integration checks
│   ├── curation/     Curated questions, answers, and correction configurations
│   └── archive/      Historical migration tools retained for traceability
├── evaluation/     Reusable objective answer-matching module
├── subjective/     Subjective prompts, APIs, validation, and score aggregation
├── schemas/        JSON schemas for questions, rubrics, and grading results
├── configs/        Evaluation configurations
├── prompts/        Evaluation and rubric-generation prompt templates
├── reports/        Per-question model results, grades, and summary reports
├── docs/history/   Historical workflows, protocols, and expansion plans
├── workspace/      Original sources, extracted materials, human review, and publication staging
└── tmp/            Temporary directory, when present
```

See the [scripts guide](scripts/README.md) for individual tools and their current paths. `construction/` and `curation/` support reconstruction and maintenance; `evaluation/` and `subjective/` are reusable modules and should not be treated as temporary files simply because they are not entry points.

## Setup and Offline Checks

Run the following PowerShell commands from the parent directory containing `CampusEval/`; the virtual environment is also created in that parent directory:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r CampusEval\requirements.txt

# Check published data, fixed subsets, schemas, and image references; save reports locally
.venv\Scripts\python.exe CampusEval\scripts\maintenance\validate_clean_release.py

# Regression tests
.venv\Scripts\python.exe -m unittest discover -s CampusEval\scripts\tests
```

The latest run passed all **64 default tests** and **3 optional local checks**. Default tests cover current functionality and release integrity, using mocked responses or dry-run mode without calling live model APIs. Kaoyan checks requiring local source materials run separately and are skipped if those materials are unavailable; see the [test guide](scripts/tests/README.md).

Reading datasets requires only the standard-library `json` module. Core evaluation and validation dependencies include `requests`, `jsonschema`, and `sympy`; see [requirements.txt](requirements.txt). Source construction tools may additionally require PyMuPDF, Pillow, PyArrow, BeautifulSoup, or pypdf; the base requirements do not cover every reconstruction tool.

The [dataset README](datasets/README.md) lists published file paths, record counts, byte sizes, and SHA-256 hashes. The general release validator checks question structure, IDs, fixed subsets, the original 50 rubrics, and image references; it does not provide a full mathematical review of the 958 new rubrics. The previous JSON release manifest has been removed. Validation output is stored locally in `workspace/reports/`. Passing structural, reference, or selected mathematical checks does not establish an independent mathematical review of every question.

Completed corrections, rubric review coverage, and outstanding issues are recorded in the [data maintenance summary](datasets/MAINTENANCE.md).

## Model Evaluation and Rubric Generation

The existing complete evaluation workflow primarily serves the fixed mini subsets. Additional source datasets use the same question structure, but new experiments still need explicit question types, answer-matching rules, image support, data splits, and subjective rubrics.

- **Objective questions**: `scripts/evaluation/evaluate_qwen_mini.py` accepts `--dataset` and defaults to the 70-question mini. `rescore_qwen_mini.py` locally rescores saved results using matching rules that differ from initial scoring.
- **Subjective questions**: run `generate_subjective_answers.py`, then `evaluate_subjective_answers.py` for blind rubric-based grading, followed by `aggregate_subjective_scores.py` for scores and review requirements. Default configurations and rubrics target the fixed 50 questions.
- **Rubric generation**: `generate_subjective_rubrics.py` produces review drafts for written-response and proof questions with source solutions, using [subjective_rubric_generator_zh_v1.txt](prompts/subjective_rubric_generator_zh_v1.txt) with resumable generation. Specify the model, endpoint, and output directory explicitly; see the [evaluation tools guide](scripts/evaluation/README.md).
- Subjective answer generation, judging, and rubric generation provide `--dry-run` and `--execute`. Supply API keys through runtime environment variables or supported hidden input. Consult the objective entry point's own `--help` for its execution options.

Inspect current options:

```powershell
.venv\Scripts\python.exe CampusEval\scripts\evaluation\evaluate_qwen_mini.py --help
.venv\Scripts\python.exe CampusEval\scripts\evaluation\generate_subjective_answers.py --help
.venv\Scripts\python.exe CampusEval\scripts\evaluation\evaluate_subjective_answers.py --help
.venv\Scripts\python.exe CampusEval\scripts\evaluation\aggregate_subjective_scores.py --help
.venv\Scripts\python.exe CampusEval\scripts\evaluation\generate_subjective_rubrics.py --help
```

Explicitly direct new experiment output to `runs/`; retain rubric drafts, generation provenance, and recovery records in the local workspace. Subjective tools protect published data and report directories from output writes. Existing per-question results are in [reports/objective/](reports/objective/) and [reports/subjective/](reports/subjective/). They apply to their original data and protocols and do not establish evaluation coverage of the four additional source datasets.

## PDF Conversion and Data Maintenance

For future PDF extraction, use **[MinerU's website](https://mineru.net/) for precise parsing → download JSON → save it in a content-named subdirectory of `workspace/` → convert locally, pair questions and answers, and apply corrections → validate and publish the dataset**. Lightweight API extraction is no longer used, and the former `tools/` directory has been removed.

Procedure: open the website's online parsing page, sign in, upload a PDF, and use precise parsing. Download the result in **JSON format**, create a content-named subdirectory under the project's `workspace/`, and save the original JSON there. For example, store questions in `workspace/考研数学一_1987-2023_题干/` and solutions in `workspace/考研数学一_1987-2023_答案解析/`. See the [workspace procedure](workspace/README.md#网页端精准解析标准步骤) for full steps, batch naming, and retention rules.

Earlier downloads, page mappings, and some source files remain in historical locations such as `workspace/extracted/kaoyan/precise/` and `workspace/extracted/SOA/`; this convention change does not move them. Existing builders may still read these fixed paths, so adapt input paths and filenames before processing new batches. This is the procedure for future work, not a claim that every historical website setting or operation was recorded. Existing MIT processing used local PDF extraction and curation, while U-MATH used Parquet imports; their historical methods remain unchanged.

Preview imports of normalized JSON/JSONL by specifying the question file explicitly, so receipts or rubrics are not scanned as questions:

```powershell
.venv\Scripts\python.exe CampusEval\scripts\maintenance\import_dataset.py `
  --imports CampusEval\workspace\imports\batch\questions.jsonl `
  --target main --dry-run
```

The path is an example input to prepare first. The general importer writes to `main` or `training`, rather than publishing automatically to arbitrary source directories; imports do not expand the fixed mini subsets or their rubrics. `--dry-run` is a preliminary check, not full staging validation. Publication spans multiple files without transactional rollback. Refresh the dataset README inventory and validate after changing published data.

Intermediate workspace materials may still be valuable. `clean_workspace.py` cleans only `workspace/staging/` by default, preserving original parsed materials, maintenance records, and migration backups. Cleaning `extracted/`, workspace `reports/`, or `rejected/` requires the corresponding explicit `--scope`; preview with `--dry-run` first. See [workspace/README.md](workspace/README.md) for directory responsibilities.

## Sources, Copyright, and Historical Records

- Source materials retain their own copyrights and license terms; they are not all original project content or covered by a code license.
- See the [MIT README](datasets/MIT/README.md) for source attribution and licensing.
- SOA's copyright text is retained in [COPYRIGHT.txt](datasets/SOA/COPYRIGHT.txt), with notes in the [SOA README](datasets/SOA/README.md).
- U-MATH's original license is retained in [LICENSE](datasets/U-MATH/LICENSE).
- Three historical workflow, evaluation protocol, and expansion documents are archived in [docs/history/](docs/history/README.md). Figures such as the 5,000-question quota describe historical plans, not current results; use this README and the published data for current counts.

## Published and Local Files

GitHub displays the English `README.md` by default. `README.zh-CN.md` contains the Chinese version with the same structure. Other source and tool documentation is primarily in Chinese.

The project is published as a dataset plus maintenance and evaluation tools. Git ignore rules retain only `workspace/README.md` in version control; all other workspace materials remain local, including `workspace/imports/umath_download/test.parquet`.

| Content | Publication | Reason |
|---|---|---|
| `datasets/` | Required | Questions, fixed subsets, rubrics, inventory, source notes, and copyright notices |
| `data/images/` | Required | Images referenced by questions and solutions; preserve relative paths |
| Root `README.md`, `README.zh-CN.md`, `__init__.py`, `requirements.txt`, `.gitignore`, `.gitattributes` | Include with the tools | Project documentation, package structure, environment, and version-control rules |
| `schemas/` | Include with the tools | Format constraints for data and grading results |
| `scripts/`, `evaluation/`, `subjective/` | Include with the tools | Entry points, construction and correction inputs, and objective and subjective evaluation |
| `configs/`, `prompts/` | Include with the tools | Evaluation configurations and prompt templates without runtime keys |
| `scripts/tests/` | Include with the tools | Regression tests and release integrity checks; local source checks run as needed |
| `reports/` | Recommended | Model results, grades, and summaries; optional for a dataset-only package |
| `docs/` | Optional | Historical protocols and stage documents; not a substitute for current documentation |
| `workspace/README.md` | Recommended | Website precise-parsing procedure and local material retention rules |
| Other `workspace/` content | Exclude | Original PDFs, Parquet, website JSON, review materials, staging, failure records, and migration backups stay local |
| `runs/`, `tmp/`, caches, logs | Exclude | New experiment output and temporary files; curate final results into `reports/` |
| `.venv/`, `node_modules/`, `.env*`, key files | Exclude | Local environments or sensitive configuration |

`scripts/archive/` is retained for historical traceability; its lightweight extraction tools are no longer used. Current regression tests no longer depend on historical migration scripts.

For a minimal dataset package, retain `datasets/`, `data/images/`, and both project READMEs, together with each source's copyright, license, and usage notes. Git publication differs from archive distribution: manually packaging the entire directory does not automatically follow `.gitignore`, and the `.git/` history database should not be included in a distribution archive.
