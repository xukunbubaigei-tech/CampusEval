# scripts 分类导航

更新日期：2026-10-19。脚本按职责分类，子目录的 `__init__.py` 用于支持包导入。历史 `archive/` 目录已恢复，保留迁移工具供回归测试与追溯；轻量 API 提取不再使用，网页端精准解析标准步骤见文末。

## 目录结构

```text
scripts/
├── evaluation/       模型作答、评分、聚合与重评分（5 个业务文件）
├── maintenance/      导入、发布检查、报告检查与工作区清理（4 个）
├── construction/     按来源组织的数据加工工具（11 个）
│   ├── kaoyan/       考研：准备批次、精准转换、构建、裁图、报告
│   ├── mit/          MIT：收集来源、首批构建、第二批扩充
│   ├── soa/          SOA：定位题答边界、转换暂存题库
│   └── umath/        U-MATH：转换 Parquet 和图片
├── checks/           专项校验与数学复核（5 个）
├── curation/         人工题答和纠错资产（8 个）
│   ├── kaoyan/       考研纠错及依据
│   ├── mit/          首批、第二批题答整理稿
│   └── soa/          SOA 纠错配置
└── archive/          历史迁移与早期提取实现（3 个业务文件）
```

## 审阅入口

| 目录 | 适用场景 |
|---|---|
| [evaluation](evaluation/README.md) | 运行模型评测实验 |
| [maintenance](maintenance/README.md) | 导入新题与检查项目完整性 |
| [construction](construction/README.md) | 查看各来源如何加工成题库 |
| [checks](checks/README.md) | 查看专项检查和指定数学断言 |
| [curation](curation/README.md) | 审阅人工整理的题答及纠错依据 |
| [archive](archive/README.md) | 历史迁移、回归测试与追溯；轻量提取已停用 |

只读取现成 JSONL 或使用自己的训练程序，不需要运行构建工具。日常实验优先查看 `evaluation/`；数据维护优先查看 `maintenance/`。

## 常用命令

从项目父目录 `D:\codex-project\高考数据集` 执行：

```powershell
# 离线发布检查（会写入校验报告）
.venv\Scripts\python.exe CampusEval\scripts\maintenance\validate_clean_release.py

# 查看导入器参数
.venv\Scripts\python.exe CampusEval\scripts\maintenance\import_dataset.py --help

# 查看主观题作答、评分、聚合参数
.venv\Scripts\python.exe CampusEval\scripts\evaluation\generate_subjective_answers.py --help
.venv\Scripts\python.exe CampusEval\scripts\evaluation\evaluate_subjective_answers.py --help
.venv\Scripts\python.exe CampusEval\scripts\evaluation\aggregate_subjective_scores.py --help
```

旧的平铺路径已迁移，未保留同名入口副本。项目代码、测试与当前操作文档中的路径已同步更新；历史报告原文中的旧命令仅作历史记录。外部保存的命令也需替换为新路径，下表提供逐文件对应。

## 依赖与精简说明

- `curation/` 承载实际内容，构建器依赖它，不能按临时脚本处理。
- MIT 首批与第二批构建器读取不同题答文件；第二批构建器还加载首批构建模块。首批数学复核也读取首批构建器中的 ID 函数。
- SOA 专项校验读取 `construction/soa/prepare_soa_segments.py` 中的排除题号；SOA 构建器读取 `curation/soa/soa_corrections.json`。
- 通用发布检查与专项检查覆盖不同要求，保留两层。
- 客观题重评分与 `evaluation/metrics.py` 有部分重复逻辑，但规则不同；未来整合需先比对结果。
- 历史归档目录已恢复，其中迁移工具仍供回归测试使用；缓存 `__pycache__/` 可按需清理。
- `build_soa_dataset.py` 写入暂存区，不直接发布正式 SOA 题库。当前 `import_dataset.py` 保留固定 mini 并检查一致性，不自动重建 mini；当前项目没有 `rebuild_mini_datasets.py`。

## 原文件与新位置

| 原文件名 | 新位置 |
|---|---|
| `aggregate_subjective_scores.py` | [evaluation/aggregate_subjective_scores.py](evaluation/aggregate_subjective_scores.py) |
| `build_kaoyan_dataset.py` | [construction/kaoyan/build_kaoyan_dataset.py](construction/kaoyan/build_kaoyan_dataset.py) |
| `build_mit_dataset.py` | [construction/mit/build_mit_dataset.py](construction/mit/build_mit_dataset.py) |
| `build_soa_dataset.py` | [construction/soa/build_soa_dataset.py](construction/soa/build_soa_dataset.py) |
| `build_umath_dataset.py` | [construction/umath/build_umath_dataset.py](construction/umath/build_umath_dataset.py) |
| `clean_workspace.py` | [maintenance/clean_workspace.py](maintenance/clean_workspace.py) |
| `collect_mit_sources.py` | [construction/mit/collect_mit_sources.py](construction/mit/collect_mit_sources.py) |
| `convert_kaoyan_precise.py` | [construction/kaoyan/convert_kaoyan_precise.py](construction/kaoyan/convert_kaoyan_precise.py) |
| `crop_kaoyan_figures.py` | [construction/kaoyan/crop_kaoyan_figures.py](construction/kaoyan/crop_kaoyan_figures.py) |
| `evaluate_qwen_mini.py` | [evaluation/evaluate_qwen_mini.py](evaluation/evaluate_qwen_mini.py) |
| `evaluate_subjective_answers.py` | [evaluation/evaluate_subjective_answers.py](evaluation/evaluate_subjective_answers.py) |
| `extend_mit_dataset.py` | [construction/mit/extend_mit_dataset.py](construction/mit/extend_mit_dataset.py) |
| `generate_subjective_answers.py` | [evaluation/generate_subjective_answers.py](evaluation/generate_subjective_answers.py) |
| `import_dataset.py` | [maintenance/import_dataset.py](maintenance/import_dataset.py) |
| `kaoyan_corrections.py` | [curation/kaoyan/kaoyan_corrections.py](curation/kaoyan/kaoyan_corrections.py) |
| `mit_batch2_calculus_algebra.py` | [curation/mit/mit_batch2_calculus_algebra.py](curation/mit/mit_batch2_calculus_algebra.py) |
| `mit_batch2_final_statistics.py` | [curation/mit/mit_batch2_final_statistics.py](curation/mit/mit_batch2_final_statistics.py) |
| `mit_batch2_probability.py` | [curation/mit/mit_batch2_probability.py](curation/mit/mit_batch2_probability.py) |
| `mit_batch2_statistics.py` | [curation/mit/mit_batch2_statistics.py](curation/mit/mit_batch2_statistics.py) |
| `mit_curated_algebra_stats.py` | [curation/mit/mit_curated_algebra_stats.py](curation/mit/mit_curated_algebra_stats.py) |
| `mit_curated_calculus.py` | [curation/mit/mit_curated_calculus.py](curation/mit/mit_curated_calculus.py) |
| `prepare_kaoyan_answer_batches.py` | [construction/kaoyan/prepare_kaoyan_answer_batches.py](construction/kaoyan/prepare_kaoyan_answer_batches.py) |
| `prepare_soa_segments.py` | [construction/soa/prepare_soa_segments.py](construction/soa/prepare_soa_segments.py) |
| `rescore_qwen_mini.py` | [evaluation/rescore_qwen_mini.py](evaluation/rescore_qwen_mini.py) |
| `soa_corrections.json` | [curation/soa/soa_corrections.json](curation/soa/soa_corrections.json) |
| `validate_clean_release.py` | [maintenance/validate_clean_release.py](maintenance/validate_clean_release.py) |
| `validate_kaoyan_dataset.py` | [checks/validate_kaoyan_dataset.py](checks/validate_kaoyan_dataset.py) |
| `validate_reports.py` | [maintenance/validate_reports.py](maintenance/validate_reports.py) |
| `validate_soa_dataset.py` | [checks/validate_soa_dataset.py](checks/validate_soa_dataset.py) |
| `verify_kaoyan_corrections.py` | [checks/verify_kaoyan_corrections.py](checks/verify_kaoyan_corrections.py) |
| `verify_mit_batch2.py` | [checks/verify_mit_batch2.py](checks/verify_mit_batch2.py) |
| `verify_mit_mathematics.py` | [checks/verify_mit_mathematics.py](checks/verify_mit_mathematics.py) |
| `write_kaoyan_report.py` | [construction/kaoyan/write_kaoyan_report.py](construction/kaoyan/write_kaoyan_report.py) |

## 当前 PDF 提取入口

后续不再使用轻量 API。通过 [MinerU 网页端](https://mineru.net/)精准解析后下载 JSON，保存到 `workspace/` 下以解析内容命名的直接子文件夹，详见 [标准步骤](../workspace/README.md#网页端精准解析标准步骤)。原 `tools/` 目录已移除，`archive/` 中的轻量接口代码仅作历史留存。
