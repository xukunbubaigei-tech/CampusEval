# 数据集说明与文件清单

清单更新日期：2026-10-21。以下数量、字节数和 SHA-256 按当前实际文件统计。

六份主数据当前合计 **3,896 条记录**，规范图片 **311 个文件**。固定 mini 是主库子集，不重复计入主记录总量；ID 唯一不代表已完成语义去重。

## 文件导航

| 数据 | 文件 | 类型 | 记录数 | 字节数 |
|---|---|---|---:|---:|
| 高考 Benchmark | [main/benchmark.jsonl](main/benchmark.jsonl) | 题目 | 128 | 132282 |
| 训练集 | [main/training.jsonl](main/training.jsonl) | 题目 | 1000 | 1046885 |
| 考研数学一 | [kaoyan/questions.jsonl](kaoyan/questions.jsonl) | 题目 | 805 | 1905374 |
| MIT | [MIT/questions.jsonl](MIT/questions.jsonl) | 题目 | 146 | 133860 |
| SOA | [SOA/questions.jsonl](SOA/questions.jsonl) | 题目 | 718 | 902441 |
| U-MATH | [U-MATH/questions.jsonl](U-MATH/questions.jsonl) | 题目 | 1099 | 580635 |
| 客观题 mini | [objective_70/questions.jsonl](objective_70/questions.jsonl) | 固定子集 | 70 | 57339 |
| 主观题 mini | [subjective_50/questions.jsonl](subjective_50/questions.jsonl) | 固定子集 | 50 | 72133 |
| 固定主观题 Rubric | [subjective_50/rubrics.jsonl](subjective_50/rubrics.jsonl) | Rubric | 50 | 189541 |
| 考研 Rubric | [kaoyan/rubrics.jsonl](kaoyan/rubrics.jsonl) | Rubric | 322 | 1898514 |
| Benchmark Rubric | [main/benchmark.rubrics.jsonl](main/benchmark.rubrics.jsonl) | Rubric | 36 | 96034 |
| 训练集 Rubric | [main/training.rubrics.jsonl](main/training.rubrics.jsonl) | Rubric | 600 | 773287 |

来源、许可和各库使用边界见各子目录 README；已完成修订与待处理问题见 [数据维护摘要](MAINTENANCE.md)。模型测试结果单独保存在 [reports/](../reports/README.md)。

## 数据格式与使用边界

- 文件为 UTF-8 JSONL，每行一个对象。题目包含 `id`、`source`、`question`、`answer`、`metadata`；Rubric 通过 `question_id` 对应题目，包含 `rubric`、`reference_solution_1`、`reference_solution_2`。
- 图片路径相对项目根目录，统一位于 `data/images/`。复制数据时需同时保留引用图片。
- 主观题 Rubric 使用实验性统一 20 分尺度，生成完成与结构校验通过均不代表逐题数学复核通过。
- U-MATH 原始数据没有独立解析，`solution` 留空；考研有 47 条空解析，其中 `kaoyan_math1_2022_03_19` 未生成 Rubric。
- 主观题 mini 有 14 条与训练集同 ID，训练后评测需隔离重叠记录，并进一步检查同题异 ID 和近似题。

## 文件版本指纹

SHA-256 用于人工核对文件是否与此清单记录的版本相同，不证明数学内容正确。题库改变后应重新生成本清单；离线结构校验直接检查现有文件，不再依赖 JSON 发布清单。

| 文件 | SHA-256 |
|---|---|
| `main/benchmark.jsonl` | `a564fbde449ae6c3caa31cc91b9bb41c2d2a6cc28409bbda1d87d2efad4745be` |
| `main/training.jsonl` | `b06fdb563d96d65bd944974e195d1564f541abc44fec096a902a21fe2467409f` |
| `kaoyan/questions.jsonl` | `12829c192f355fa5ce6980284acd8d45b27c1f966d47ab593eadc6074948c17b` |
| `MIT/questions.jsonl` | `11bc43fbe124e2474bb858e0bc0494f8f92fc45c20160f1ed5102eab5cb4bd64` |
| `SOA/questions.jsonl` | `8e4095cb3e0aa2a49195402494584f31c5c0247bd397c5e95af61097732e768f` |
| `U-MATH/questions.jsonl` | `f2f57f62f7e14f2158ac97ed964b5338c6938e1a0b6c82a9980a032bbc97b02c` |
| `objective_70/questions.jsonl` | `7cc3611accca345784f70d3ba93eb25e6c22c50761507653995e99495e4dca40` |
| `subjective_50/questions.jsonl` | `e9d07b25a778df543ad77368c1a25bbd66e44973ac640b4924a3c636b95967a9` |
| `subjective_50/rubrics.jsonl` | `801280665b00411f062c3f10aa2b52e1d9c507f0b78c5ff427c9113fcd5c4429` |
| `kaoyan/rubrics.jsonl` | `dae2c4e4f539081f343c20368580783cb716cb4e33692feeae2fb1b9b32caeaf` |
| `main/benchmark.rubrics.jsonl` | `4fc114ef58edf059a2d509e8b7dd783e159a05690e71ffb2eb21edc0ecc98b8c` |
| `main/training.rubrics.jsonl` | `78ac786b03ddd8b96c6594b9ae4c07b8949104cf2c50aa807245ecb365328d27` |

## 维护方式

从项目父目录执行：

```powershell
.venv\Scripts\python.exe CampusEval\scripts\maintenance\update_dataset_readme.py
.venv\Scripts\python.exe CampusEval\scripts\maintenance\validate_clean_release.py
```

第一条命令更新本说明中的清单；导入脚本发布新数据后也会自动更新。第二条检查结构、ID、固定子集、原有 50 份 Rubric 及图片引用，结果写入本地 `workspace/reports/dataset_validation.json`。考研专项校验结果写入本地 `workspace/reports/kaoyan_validation.json`。这些检查不提供全库数学正确性认证；新增 Rubric 的既有验证范围见数据维护摘要。
