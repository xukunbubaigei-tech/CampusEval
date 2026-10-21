# CampusEval：多来源数学数据集与模型评测工程

[English](README.md) | 简体中文

本项目由高考数学 Benchmark 扩展而来，目前包含中文高考、Conic10K、考研数学一，以及英文 MIT、SOA 和 U-MATH 数据，用于题库读取、训练数据准备与模型能力评测。项目名称与目录统一为 `CampusEval`。

截至 **2026-10-21**，六份正式主数据文件共 **3,896 条记录**，ID 无重复；另保留固定客观题 70 题、主观题 50 题和对应的 50 份 Rubric，新增考研及主库 Rubric 共 **958 份**。两个 mini 是主库子集，不能再次计入题目总量；各 Rubric 文件之间可能覆盖同一道题。ID 无重复也不代表所有来源间已完成语义去重。

## 当前数据

| 数据 | 数量 | 正式文件 | 内容与边界 |
|---|---:|---|---|
| 高考 Benchmark | 128 | [benchmark.jsonl](datasets/main/benchmark.jsonl) | 中文高考评测主集，全部有解析 |
| 既有训练集 | 1,000 | [training.jsonl](datasets/main/training.jsonl) | 566 条 GAOKAO-Bench、434 条 Conic10K；未逐题权威复核 |
| 考研数学一 | 805 | [questions.jsonl](datasets/kaoyan/questions.jsonl) | 1987—2023 年指定本地材料，47 条解析为空；不代表数学一、二、三全部收录 |
| MIT | 146 | [questions.jsonl](datasets/MIT/questions.jsonl) | MIT OCW 四门课程的英文考试与练习题，全部有配套解析 |
| SOA | 718 | [questions.jsonl](datasets/SOA/questions.jsonl) | 英文 Exam P 样题，每题 A—E 五个选项，全部有解析 |
| U-MATH | 1,099 | [questions.jsonl](datasets/U-MATH/questions.jsonl) | 已核实修正 19 条并删除 1 条缺表题；最终答案基于 `golden_answer`，全部 `solution` 为空，不能视为有独立推导过程 |
| 客观题 mini | 70 | [questions.jsonl](datasets/objective_70/questions.jsonl) | 固定高考子集：50 道选择类题（含多选）、20 道填空题；62 道无题图、8 道含题图 |
| 主观题 mini | 50 | [questions.jsonl](datasets/subjective_50/questions.jsonl) | 固定子集：36 道高考题、14 道 Conic10K；5 道含题图 |
| 固定主观题 Rubric | 50 | [rubrics.jsonl](datasets/subjective_50/rubrics.jsonl) | 纯文本评分标准与两种参考解法，统一实验性 20 分尺度，不是原卷官方分值 |
| 考研 Rubric | 322 | [rubrics.jsonl](datasets/kaoyan/rubrics.jsonl) | 有原解析的解答题、证明题 |
| Benchmark Rubric | 36 | [benchmark.rubrics.jsonl](datasets/main/benchmark.rubrics.jsonl) | 主集中的全部解答题、证明题 |
| 训练集 Rubric | 600 | [training.rubrics.jsonl](datasets/main/training.rubrics.jsonl) | 训练集中的全部解答题 |

新增 Rubric 使用统一的实验性 **20 分尺度**，包含纯文本评分标准和参考解法。考研 `kaoyan_math1_2022_03_19` 因原解析为空未生成；MIT 和 U-MATH 尚无配套 Rubric 文件。新增 958 份已完成结构检查，内容仅经抽查；已知的 2 项数学或评分问题、8 份不完整第二解法和题库待同步项见 [数据维护摘要](datasets/MAINTENANCE.md)，尚未修正。生成完成或结构检查通过不代表数学内容全部正确。

各来源整理方式和质量边界见[考研说明](datasets/kaoyan/README.md)、[MIT 说明](datasets/MIT/README.md)、[SOA 说明](datasets/SOA/README.md)。U-MATH 的修正及使用边界见[说明](datasets/U-MATH/README.md)，原始许可文件保留。

规范图片共 **311 个文件**，统一位于 `data/images/`：高考 23、考研 71、MIT 17、U-MATH 200。图片包含题干图与解析图；SOA 当前无图片引用。路径相对项目根目录，复制题库时应同时保留引用的图片和目录关系。

## 如何使用数据

正式数据为 UTF-8 JSONL，每行一个 JSON 对象，包含五个顶层字段：

| 字段 | 内容 |
|---|---|
| `id` | 题目主键；模型答案、Rubric、评测结果通过 ID 关联 |
| `source` | 当前实际来源为 `gaokao`、`conic10k`、`university_exam`、`soa`、`umath`；考研与 MIT 共享 `university_exam`，需结合目录、ID 和卷名区分 |
| `question` | `text` 题干、`images` 图片路径数组、`options` 选项数组 |
| `answer` | `final_answer` 最终答案、`solution` 解析；考研及 U-MATH 的空解析应按实际保留 |
| `metadata` | `paper_name` 材料或试卷名称、`question_type` 题型 |

Rubric 通过 `question_id` 对应题目，其余字段为 `rubric`、`reference_solution_1` 和 `reference_solution_2`；第二解法可为 `null`。

只读取现成题库时，不需要运行构建脚本。例如从项目父目录执行：

```python
import json
from pathlib import Path

path = Path("CampusEval/datasets/SOA/questions.jsonl")
with path.open(encoding="utf-8") as stream:
    questions = [json.loads(line) for line in stream if line.strip()]
```

现有训练集与主观题 mini 有 **14 条相同 ID**。若使用该训练集训练模型，再用主观题 mini 测试，应先隔离重叠记录并检查同题异 ID 和近似题。六份主数据尚未统一重新划分训练、验证与测试集；不要将全部题目默认视为相互独立的测试样本。

## 目录导航

```text
CampusEval/
├── README.md       英文项目说明（GitHub 默认首页）
├── README.zh-CN.md 中文项目说明，与英文版逐节对应
├── datasets/       正式题库、固定 mini、Rubric、版本清单与来源说明
├── data/images/    题干及解析引用的规范图片
├── scripts/        按职责分类的运行入口与维护工具
│   ├── evaluation/   模型作答、Rubric 生成、评分、聚合和本地重评分
│   ├── maintenance/  数据导入、清单更新、完整性检查和工作区清理
│   ├── construction/ 按来源组织的转换和构建工具
│   ├── checks/       考研、SOA 来源专项校验
│   ├── tests/        程序回归测试与可选来源集成检查
│   ├── curation/     人工整理题答与纠错配置
│   └── archive/      历史迁移工具，保留用于追溯
├── evaluation/     客观题答案匹配功能模块，供运行脚本调用
├── subjective/     主观题提示词、接口、校验及成绩聚合模块
├── schemas/        题目、Rubric 与评分结果的 JSON 格式规范
├── configs/        评测配置
├── prompts/        评测及 Rubric 生成提示模板
├── reports/        模型测试逐题结果、评分及汇总报告
├── docs/history/   历史流程、协议和扩充方案
├── workspace/      原始输入、提取材料、人工审核及发布暂存区
└── tmp/            临时目录（如存在）
```

脚本逐项用途及迁移后的路径见 [scripts 导航](scripts/README.md)。`construction/` 和 `curation/` 用于重建维护，`evaluation/` 和 `subjective/` 是可复用功能模块，不能因为不是运行入口就当作临时文件删除。

## 环境与离线检查

以下 PowerShell 命令均从包含 `CampusEval/` 的父目录执行，虚拟环境也创建在该父目录下：

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r CampusEval\requirements.txt

# 检查正式数据、固定子集、Schema 和图片引用；报告写入本地 workspace/reports
.venv\Scripts\python.exe CampusEval\scripts\maintenance\validate_clean_release.py

# 程序回归测试
.venv\Scripts\python.exe -m unittest discover -s CampusEval\scripts\tests
```

最近一次默认 **64 项测试**和可选本地 **3 项检查**均通过。默认测试覆盖当前程序功能和发布完整性，使用模拟响应或预览模式，不调用真实模型 API；依赖本地来源材料的考研检查单独运行，缺少材料时跳过，见 [测试说明](scripts/tests/README.md)。

标准库 `json` 即可读取题库。现有评测与校验基础依赖为 `requests`、`jsonschema`、`sympy`，详见 [requirements.txt](requirements.txt)。来源构建工具还可能需要 PyMuPDF、Pillow、PyArrow、BeautifulSoup、pypdf 等额外依赖，基础依赖文件不覆盖所有重建工具。

[数据集 README](datasets/README.md) 集中列出正式文件的路径、数量、大小和 SHA-256。通用发布校验检查题目结构、ID、固定子集、原有 50 份 Rubric 和图片引用，不覆盖新增 958 份 Rubric 的完整数学复核。旧 JSON 发布清单已删除。校验结果保存在本地 `workspace/reports/`。结构、引用和局部数学计算检查通过，不等于所有题目都经过独立数学审校。

已完成的数据修订、Rubric 验证范围和待处理问题集中见 [数据维护摘要](datasets/MAINTENANCE.md)。

## 模型评测与 Rubric 生成

既有完整评测流程主要服务于固定 mini。新增来源题库采用相同题目结构，但用于新实验时仍需明确题型、答案匹配规则、图像支持、数据划分，以及主观题 Rubric。

- **客观题**：`scripts/evaluation/evaluate_qwen_mini.py`；使用 `--dataset` 指定题库，默认读取 70 题 mini。`rescore_qwen_mini.py` 用于已有结果的本地重评分，其匹配规则与首次评分并不完全相同。
- **主观题**：先运行 `generate_subjective_answers.py`，再用 `evaluate_subjective_answers.py` 依据 Rubric 盲评，最后用 `aggregate_subjective_scores.py` 汇总分数与复核需求。默认配置及 Rubric 对应固定 50 题。
- **Rubric 生成**：`generate_subjective_rubrics.py` 为有原解析的解答题和证明题生成待审核稿，使用 [subjective_rubric_generator_zh_v1.txt](prompts/subjective_rubric_generator_zh_v1.txt)，支持断点续跑。必须显式指定模型、接口和输出目录，详见 [评测工具说明](scripts/evaluation/README.md)。
- 主观题作答、Judge 和 Rubric 生成入口提供 `--dry-run` 与 `--execute`；API Key 通过运行时环境变量或支持的隐藏输入提供。客观题入口的参数和执行方式单独以 `--help` 为准。

查看当前参数：

```powershell
.venv\Scripts\python.exe CampusEval\scripts\evaluation\evaluate_qwen_mini.py --help
.venv\Scripts\python.exe CampusEval\scripts\evaluation\generate_subjective_answers.py --help
.venv\Scripts\python.exe CampusEval\scripts\evaluation\evaluate_subjective_answers.py --help
.venv\Scripts\python.exe CampusEval\scripts\evaluation\aggregate_subjective_scores.py --help
.venv\Scripts\python.exe CampusEval\scripts\evaluation\generate_subjective_rubrics.py --help
```

新实验建议明确输出到 `runs/`；Rubric 草稿、生成来源和恢复记录保存在本地工作区。主观题工具对正式数据和报告目录有输出保护。既有逐题结果位于 [reports/objective/](reports/objective/) 和 [reports/subjective/](reports/subjective/)，对应当时的数据与协议，不能当作新增四类题库已经完成评测的证据。

## PDF 转换与数据维护

今后 PDF 提取统一采用 **[MinerU 网页端](https://mineru.net/)精准解析 → 下载 JSON → 保存到 `workspace/` 下以解析内容命名的子文件夹 → 本地转换、题答配对与纠错 → 校验后保存正式题库**。不再使用轻量 API 提取方式，原 `tools/` 目录已删除。

标准步骤：打开上述网址并进入在线解析页面，登录后上传 PDF，使用网页端精准解析；完成后下载 **JSON 格式**的解析结果。在项目的 `workspace/` 下新建以解析内容命名的子文件夹，将 JSON 原文件保存到其中。例如题干存入 `workspace/考研数学一_1987-2023_题干/`，解析存入 `workspace/考研数学一_1987-2023_答案解析/`。完整步骤、分批命名规则和保留要求见 [workspace 标准流程](workspace/README.md#网页端精准解析标准步骤)。

此前的下载结果、页码映射和部分源文件仍保存在 `workspace/extracted/kaoyan/precise/`、`workspace/extracted/SOA/` 等旧位置，不因本次规范调整而移动。现有构建器仍可能读取这些固定路径，新批次需先适配输入路径与文件名，再执行转换。上述标准是后续操作规范，不表示历史网页参数与所有操作细节已完整留存。既有 MIT 采用本地 PDF 提取与整理，U-MATH 采用 Parquet 导入，不改写其历史处理方式。

新增规范 JSON/JSONL 可先预览导入计划，明确指定题目文件，避免将回执或 Rubric 当作题目一并扫描：

```powershell
.venv\Scripts\python.exe CampusEval\scripts\maintenance\import_dataset.py `
  --imports CampusEval\workspace\imports\batch\questions.jsonl `
  --target main --dry-run
```

上述路径是待准备的输入示例。通用导入器写入 `main` 或 `training`，不是向任意来源目录自动发布的统一入口；固定 mini 及其 Rubric 不随导入扩充。`--dry-run` 是初步检查，不等于完整暂存校验。实际发布涉及多个文件，不能视为带整体回滚的多文件事务。修改正式数据后还需更新数据集 README 清单并重新校验。

工作区中间材料不等于无价值文件。`clean_workspace.py` 默认只清理 `workspace/staging/`，保留原始解析、维护记录与迁移备份。`extracted/`、工作区 `reports/` 和 `rejected/` 仅在显式指定对应 `--scope` 时清理；执行前先用 `--dry-run` 预览。职责说明见 [workspace/README.md](workspace/README.md)。

## 来源、版权与阶段记录

- 各来源内容保留其自身版权和许可说明，不能统一视为项目原创或套用代码许可。
- MIT 的来源署名与许可说明见 [MIT README](datasets/MIT/README.md)。
- SOA 的版权原文见 [COPYRIGHT.txt](datasets/SOA/COPYRIGHT.txt)，说明见 [SOA README](datasets/SOA/README.md)。
- U-MATH 保留的原始许可文件见 [LICENSE](datasets/U-MATH/LICENSE)。
- 三份旧流程、评测协议与扩充方案已归档至 [docs/history/](docs/history/README.md)。其中的 5,000 题配额等为历史规划，不能当作当前成果；当前统计以本 README 及正式数据为准。

## 上传范围与本地材料

GitHub 默认展示英文 `README.md`，中文说明保存在 `README.zh-CN.md`，两版按相同结构维护。其他来源与工具文档主要为中文。

本项目以“数据集与维护评测工程”整体发布。当前 Git 忽略规则仅上传 `workspace/README.md`，工作区其他材料一律保留本地；原始 `workspace/imports/umath_download/test.parquet` 不上传。

| 内容 | 是否上传 | 原因 |
|---|---|---|
| `datasets/` | 必须 | 正式题目、固定子集、Rubric、版本清单、来源与版权说明 |
| `data/images/` | 必须 | 正式题干与解析引用的图片，需保持相对路径 |
| 根目录 `README.md`、`README.zh-CN.md`、`__init__.py`、`requirements.txt`、`.gitignore`、`.gitattributes` | 工程发布时上传 | 项目说明、包结构、运行环境及版本管理规则 |
| `schemas/` | 工程发布时上传 | 数据与评分结果的格式约束 |
| `scripts/`、`evaluation/`、`subjective/` | 工程发布时上传 | 运行入口、构建与纠错输入、客观及主观评分功能 |
| `configs/`、`prompts/` | 工程发布时上传 | 评测配置与提示模板，不包含运行时密钥 |
| `scripts/tests/` | 工程发布时上传 | 当前功能回归与发布完整性；本地来源集成检查按需运行 |
| `reports/` | 建议上传 | 模型测试逐题结果、评分及汇总；只分发题库时可省略 |
| `docs/` | 按需上传 | 历史协议与阶段文档，不能替代当前说明 |
| `workspace/README.md` | 建议上传 | 网页精准解析标准步骤与本地材料保存规则 |
| `workspace/` 的其他内容 | 不上传 | 原 PDF、Parquet、网页 JSON、审核材料、暂存、失败记录、迁移备份只保留本地 |
| `runs/`、`tmp/`、缓存、日志 | 不上传 | 新实验运行产物或临时文件；正式成果经整理后保存到 `reports/` |
| `.venv/`、`node_modules/`、`.env*`、密钥文件 | 不上传 | 本地环境或敏感配置 |

`scripts/archive/` 保留用于历史追溯，其中轻量接口提取工具已停用。当前回归测试已移除对历史迁移脚本的依赖。

若只发布精简题库包，保留 `datasets/`、`data/images/` 和两版项目 README 即可；各来源的版权、许可与使用说明应随数据保留。Git 仓库上传与压缩包分发不同：手工打包整个目录不会自动遵守 `.gitignore`，也不应将 `.git/` 历史数据库打入分发包。
