# 中国高考数学 Benchmark

这是工程化重构后的唯一工作版本。旧版 JSONL、诊断请求、模型能力探测、失败分片、PaddleOCR、来源下载包和 OCR/MinerU 中间材料均已移除；只保留规范数据实际引用的图片。

## 数据集

| 数据 | 文件 | 数量 | 说明 |
|---|---|---:|---|
| Benchmark 主集 | `datasets/main/benchmark.jsonl` | 128 | 已移除10道缺答案、需审核记录及12道无选项选择题 |
| 训练集 | `datasets/main/training.jsonl` | 1000 | 566 道 GAOKAO-Bench + 434 道 Conic10K；未逐题权威复核 |
| 客观题 mini | `datasets/objective_70/questions.jsonl` | 70 | 由主集按 `ids.json` 自动重建 |
| 主观题 mini | `datasets/subjective_50/questions.jsonl` | 50 | 36 道高考题 + 14 道 Conic10K |
| Rubric | `datasets/subjective_50/rubrics.jsonl` | 50 | 新三字段纯文本格式（rubric + 两种参考解法），统一实验性满分20分 |

`datasets/RELEASE_MANIFEST.json` 记录规范文件的数量、大小和哈希（导入/重建时自动刷新）；`datasets/VALIDATION_REPORT.json` 是最近一次离线完整性检查。`data/images/` 只保存当前规范数据引用的 23 张数学题图片。

每条题目为五个顶层字段：`id`、`source`（gaokao/conic10k/aime/university_exam）、`question`、`answer` 和 `metadata`。ID 是唯一主键，Rubric / 模型答案 / 评测结果只通过题目 ID 关联。

## 评测

- 主观题（新协议 v2）：先用 `scripts/generate_subjective_answers.py`（或自行准备答案 JSONL），再用 `scripts/evaluate_subjective_answers.py` 盲评，最后用 `scripts/aggregate_subjective_scores.py` 聚合。
  - Judge 只看到：题目、纯文本 Rubric、两种参考解法、被测答案；不暴露被测模型身份、其他 Judge、Rubric 生成元数据或历史结果。
  - 输出：`score / max_score / reason / correct_parts / errors / evidence_quotes / confidence / needs_human_review`。
  - 默认三 Judge（配置化，单 Judge 也可用 `--judge-mode single`）；分歧超阈值 / 低置信度 / 任一 Judge 要求复核 → 人工复核队列。
  - `--dry-run` 零网络请求；`--execute` 才调用模型（需环境变量 API Key）。
- 客观题（旧入口，保留）：`scripts/evaluate_qwen_mini.py`，本地重评分 `scripts/rescore_qwen_mini.py`。
- 既有正式结果在 `reports/objective/` 和 `reports/subjective/`；它们是历史实测记录，不会被未来运行覆盖。
- 新运行统一写入 `runs/`（输出目录保护：拒绝写入 `datasets/` 与 `reports/`）。API Key 只能通过运行时环境变量提供，不得写入仓库。

## Python 环境

项目只直接依赖 `requests`、`jsonschema` 和 `sympy`；版本已锁定在 `requirements.txt`。远程 MinerU 不需要本地 OCR 或模型依赖。建议从项目父目录创建隔离环境：

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r gaokao_math_benchmark\requirements.txt
```

离线验证与测试（**必须从父目录运行**，因为 `gaokao_math_benchmark` 目录本身是包）：

```powershell
.venv\Scripts\python gaokao_math_benchmark\scripts\validate_clean_release.py
.venv\Scripts\python -m unittest gaokao_math_benchmark.tests.test_dataset_source `
  gaokao_math_benchmark.tests.test_subjective_rubric `
  gaokao_math_benchmark.tests.test_subjective_evaluation `
  gaokao_math_benchmark.tests.test_import_dataset `
  gaokao_math_benchmark.tests.test_workspace `
  gaokao_math_benchmark.tests.test_common
```

## 新增数据（一键导入流水线）

把新题放入 `workspace/imports/`（JSON / JSONL；PDF、图片、MinerU 提取结果请先经 `tools/mineru` 转成 JSONL），然后：

```powershell
.venv\Scripts\python gaokao_math_benchmark\scripts\import_dataset.py `
  --imports gaokao_math_benchmark\workspace\imports --dry-run     # 先看计划
.venv\Scripts\python gaokao_math_benchmark\scripts\import_dataset.py `
  --imports gaokao_math_benchmark\workspace\imports `
  --rubrics gaokao_math_benchmark\workspace\imports\rubrics.jsonl  # 主观题需要
```

流水线：识别来源 → 标准化（自动生成 ID、复制图片到 `data/images/`）→ 关联 Rubric → staging 全量校验 → 原子发布（失败不动正式数据）→ 按 `ids.json` 重建 mini → 刷新 Manifest → 校验报告。失败报告写入 `workspace/rejected/`。

手工增删数据后：

```powershell
.venv\Scripts\python gaokao_math_benchmark\scripts\rebuild_mini_datasets.py
.venv\Scripts\python gaokao_math_benchmark\scripts\validate_clean_release.py
```

`workspace/` 是数据流水线工作区（职责见 `workspace/README.md`）；`scripts/clean_workspace.py` 只清理临时区，不碰正式数据与报告。

## MinerU

远程 MinerU 轻量解析工具和边界说明位于 `tools/mineru/`。它会上传 PDF，不在本机下载模型；OCR 输出必须与原页逐题核对，不能直接视为数学真值。
