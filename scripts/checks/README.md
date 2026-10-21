# 来源专项校验

本目录仅保留仍用于检查现有题库的两个专项入口。

| 文件 | 用途 |
|---|---|
| [validate_kaoyan_dataset.py](validate_kaoyan_dataset.py) | 考研题库的结构、选项答案、图片及部分公式格式检查 |
| [validate_soa_dataset.py](validate_soa_dataset.py) | SOA 格式检查，并与本地原 PDF 答案表逐项对照 |

从项目父目录 `D:\codex-project\高考数据集` 执行：

```powershell
.venv\Scripts\python.exe CampusEval\scripts\checks\validate_kaoyan_dataset.py
.venv\Scripts\python.exe CampusEval\scripts\checks\validate_soa_dataset.py
```

考研检查结果写入本地 `workspace/reports/kaoyan_validation.json`；SOA 检查需要本地 `workspace/extracted/SOA/exam_p_solutions.pdf`，不会修改正式题库。

通用 Schema、ID、固定子集、原有50份 Rubric 和图片引用检查使用 [validate_clean_release.py](../maintenance/validate_clean_release.py)。程序回归测试保存在 [tests/](../tests/)。这些检查不代表全库数学内容已经逐题复核。

2026-10-21 删除53个一次性脚本，包括抽样与导出、修订前后对比、临时审计统计、固定问题明细生成、启发式筛查和历史批次公式试算；仅供它们使用的转换辅助模块一并删除。已知待处理问题继续记录在 [数据维护摘要](../../datasets/MAINTENANCE.md)。
