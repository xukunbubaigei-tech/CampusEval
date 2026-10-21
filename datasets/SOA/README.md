# SOA Exam P 概率题库

本目录收录 Society of Actuaries（SOA，美国精算师协会）Exam P Sample Questions 的结构化整理版本，用于概率题目的读取、模型作答与评测。题干、选项和解析为英文，数学表达保留 LaTeX 格式。

截至 2026-10-19，当前 `questions.jsonl` 共 **718 道选择题**，每题包含 A—E 五个选项、一个答案字母及非空文字解析；当前没有外部图片引用。该数量描述本地整理版本，不代表 SOA 所有题目或历年正式试题全集。

## 文件说明

| 文件 | 用途 |
|---|---|
| [questions.jsonl](questions.jsonl) | UTF-8 编码，每行一道完整题目，包含题干、选项、答案、解析及元数据 |
| [COPYRIGHT.txt](COPYRIGHT.txt) | 保留原始材料的版权声明 |
| README.md | 数据介绍、字段说明与版权说明 |

直接读取题库只需解析 `questions.jsonl`，无需运行构建、OCR 或裁图脚本。

## 数据结构

每条记录包含五个顶层字段：

| 字段 | 内容 |
|---|---|
| `id` | 本项目题目 ID，当前为 `soa_p_1` 至 `soa_p_718` |
| `source` | 固定为 `soa` |
| `question` | `text` 为题干；`images` 当前为空数组；`options` 为包含 `label` 和 `text` 的选项数组 |
| `answer` | `final_answer` 为 A—E 中的答案字母；`solution` 为文字及公式解析 |
| `metadata` | `paper_name` 为 `SOA Exam P Sample Questions`；`question_type` 为 `选择题` |

ID 是整理后连续编号，**不应直接当作原 PDF 题号**。构建程序按原材料中的有效题号顺序收录，并跳过预设排除题号，因此后续编号可能与原题号不同。

## 整理方式与质量边界

题目与解析来自本地保存的 `exam_p_questions.pdf` 和 `exam_p_solutions.pdf`，经过 MinerU 提取、题答配对、选项拆分、公式整理及针对性纠错后转换为统一 JSONL 格式。原始材料与解析中间文件位于项目的 `workspace/extracted/SOA/`，不包含在本目录的精简数据文件中。

相关维护工具为项目 `scripts/` 下的 `scripts/construction/soa/prepare_soa_segments.py`、`scripts/construction/soa/build_soa_dataset.py`、`scripts/checks/validate_soa_dataset.py`，纠错配置为 `scripts/curation/soa/soa_corrections.json`。这些文件用于重新整理或复核数据，日常读取题库不依赖它们。

本次 README 编写时已直接核对：共 718 条记录、718 个唯一 ID、每题五个选项、解析均非空且图片数组均为空。项目另有校验脚本，可检查 Schema、顺序编号、原 PDF 答案匹配及部分文本与公式格式；这些检查不等于对所有题干与数学推理的独立逐题证明。使用中发现疑似提取错误时，应回查原题与原解析。

## 版权与使用说明

本目录保留的 [COPYRIGHT.txt](COPYRIGHT.txt) 原文为：

> Copyright 2026 by the Society of Actuaries.

相关原始题目与解析的版权归 Society of Actuaries 所有。本目录是对原材料的结构化整理，不是 SOA 官方发布的 JSONL 数据集。

`COPYRIGHT.txt` 仅记录版权归属，没有列出开放许可或具体使用授权。本 README 也不新增训练、商业使用、修改或再分发授权；项目代码的许可不能作为这些第三方题目内容的授权依据。需要相关用途的授权信息时，应查阅 SOA 原始材料及其适用条款，必要时向权利方确认。

保留或传递本整理版本时，请同时保留版权声明、来源说明及本 README，不应将内容标为本项目原创或已获 SOA 背书。

## 后续 PDF 提取规范

后续统一通过 [MinerU 网页端](https://mineru.net/)精准解析并下载 JSON，在项目 `workspace/` 下直接建立以解析内容命名的子文件夹，将 JSON 原文件存入其中。题干与答案解析分开保存。详细步骤见 [workspace 标准流程](../../workspace/README.md#网页端精准解析标准步骤)。当前旧批次下载结果保留原位置，不因规范调整而移动；不再使用轻量 API 提取。

## 核验修订

2026-10-20 定向修复了损坏选项、12条题干中的选项残片、公式错序、解析算术错误及上下标 HTML 残留。`soa_p_670` 恢复原卷五个带分数/整数选项，其答案字母仍为 A；`soa_p_634` 的 A 选项恢复为12/27。`soa_p_678` 原解析的0.541校正为约0.0541。`soa_p_464` 原卷选项 B 印为1600，本轮保持原样；解析中的15.29校正为15.39。718条记录、全部答案字母及用户对第3题的手工修正保持不变。定向计算与格式检查不等于全部718题均完成独立数学证明。
