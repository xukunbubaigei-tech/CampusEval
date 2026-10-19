# CampusEval：多来源数学数据集与模型评测工程

本项目由高考数学 Benchmark 扩展而来，目前包含中文高考、Conic10K、考研数学一，以及英文 MIT、SOA 和 U-MATH 数据，用于题库读取、训练数据准备与模型能力评测。项目名称与目录统一为 `CampusEval`。

截至 **2026-10-19**，六份正式主数据文件共 **3,897 条记录**，ID 无重复；另保留固定客观题 70 题、主观题 50 题和 50 份 Rubric。两个 mini 是既有主库的子集，不能再次计入题目总量；ID 无重复也不代表所有来源间已完成语义去重。

## 当前数据

| 数据 | 数量 | 正式文件 | 内容与边界 |
|---|---:|---|---|
| 高考 Benchmark | 128 | [benchmark.jsonl](datasets/main/benchmark.jsonl) | 中文高考评测主集，全部有解析 |
| 既有训练集 | 1,000 | [training.jsonl](datasets/main/training.jsonl) | 566 条 GAOKAO-Bench、434 条 Conic10K；未逐题权威复核 |
| 考研数学一 | 805 | [questions.jsonl](datasets/kaoyan/questions.jsonl) | 1987—2023 年指定本地材料，47 条解析为空；不代表数学一、二、三全部收录 |
| MIT | 146 | [questions.jsonl](datasets/MIT/questions.jsonl) | MIT OCW 四门课程的英文考试与练习题，全部有配套解析 |
| SOA | 718 | [questions.jsonl](datasets/SOA/questions.jsonl) | 英文 Exam P 样题，每题 A—E 五个选项，全部有解析 |
| U-MATH | 1,100 | [questions.jsonl](datasets/U-MATH/questions.jsonl) | 当前导入版本；保留完整 `golden_answer` 为最终答案，全部 `solution` 为空，不能视为有独立推导过程 |
| 客观题 mini | 70 | [questions.jsonl](datasets/objective_70/questions.jsonl) | 固定高考子集：50 道选择题、20 道填空题；62 道无题图、8 道含题图 |
| 主观题 mini | 50 | [questions.jsonl](datasets/subjective_50/questions.jsonl) | 固定子集：36 道高考题、14 道 Conic10K；5 道含题图 |
| 主观题 Rubric | 50 | [rubrics.jsonl](datasets/subjective_50/rubrics.jsonl) | 纯文本评分标准与两种参考解法，统一实验性 20 分尺度，不是原卷官方分值 |

各来源整理方式和质量边界见[考研说明](datasets/kaoyan/README.md)、[MIT 说明](datasets/MIT/README.md)、[SOA 说明](datasets/SOA/README.md)。U-MATH 当前目录保存题目文件及原始许可文件。

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

只读取现成题库时，不需要运行构建脚本。例如从项目父目录执行：

```python
import json
from pathlib import Path

path = Path("CampusEval/datasets/SOA/questions.jsonl")
with path.open(encoding="utf-8") as stream:
    questions = [json.loads(line) for line in stream if line.strip()]
```

现有训练集与主观题 mini 有 **14 条相同 ID**。若使用该训练集训练模型，再用主观题 mini 测试，应先隔离重叠记录并检查同题异 ID 和近似题。新增大学题库尚未自动划分新的训练、验证与测试集，也未自动生成相应 Rubric；不要将全部题目默认视为相互独立的测试样本。

## 目录导航

```text
CampusEval/
├── datasets/       正式题库、固定 mini、Rubric、版本清单与来源说明
├── data/images/    题干及解析引用的规范图片
├── scripts/        按职责分类的运行入口与维护工具
│   ├── evaluation/   模型作答、评分、聚合和本地重评分
│   ├── maintenance/  数据导入、完整性检查和工作区清理
│   ├── construction/ 按来源组织的转换和构建工具
│   ├── checks/       来源专项检查和指定数学断言核验
│   ├── curation/     人工整理题答与纠错配置
│   └── archive/      历史迁移工具，保留用于回归测试与追溯
├── evaluation/     客观题答案匹配功能模块，供运行脚本调用
├── subjective/     主观题提示词、接口、校验及成绩聚合模块
├── schemas/        题目、Rubric 与评分结果的 JSON 格式规范
├── tests/          程序回归测试
├── configs/        评测配置
├── prompts/        评测提示模板
├── reports/        正式实验结果与历史阶段记录
│   └── stages/     按阶段编号归档的流程、协议和扩充方案
├── workspace/      原始输入、提取材料、人工审核及发布暂存区
└── tmp/            临时目录（如存在）
```

脚本逐项用途及迁移后的路径见 [scripts 导航](scripts/README.md)。`construction/` 和 `curation/` 用于重建维护，`evaluation/` 和 `subjective/` 是可复用功能模块，不能因为不是运行入口就当作临时文件删除。

## 环境与离线检查

以下 PowerShell 命令均从项目父目录 `D:\codex-project\高考数据集` 执行：

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r CampusEval\requirements.txt

# 检查正式数据、固定子集、Schema、哈希和图片引用；会更新校验报告
.venv\Scripts\python.exe CampusEval\scripts\maintenance\validate_clean_release.py

# 程序回归测试
.venv\Scripts\python.exe -m unittest discover -s CampusEval\tests
```

标准库 `json` 即可读取题库。现有评测与校验基础依赖为 `requests`、`jsonschema`、`sympy`，详见 [requirements.txt](requirements.txt)。来源构建工具还可能需要 PyMuPDF、Pillow、PyArrow、BeautifulSoup、pypdf 等额外依赖，基础依赖文件不覆盖所有重建工具。

[RELEASE_MANIFEST.json](datasets/RELEASE_MANIFEST.json) 记录正式文件数量、大小与哈希，[VALIDATION_REPORT.json](datasets/VALIDATION_REPORT.json) 保存最近一次完整性检查结果。结构、引用和局部数学计算检查通过，不等于所有题目都经过独立数学审校。

## 模型评测入口

既有完整评测流程主要服务于固定 mini。新增来源题库采用相同题目结构，但用于新实验时仍需明确题型、答案匹配规则、图像支持、数据划分，以及主观题 Rubric。

- **客观题**：`scripts/evaluation/evaluate_qwen_mini.py`；使用 `--dataset` 指定题库，默认读取 70 题 mini。`rescore_qwen_mini.py` 用于已有结果的本地重评分，其匹配规则与首次评分并不完全相同。
- **主观题**：先运行 `generate_subjective_answers.py`，再用 `evaluate_subjective_answers.py` 依据 Rubric 盲评，最后用 `aggregate_subjective_scores.py` 汇总分数与复核需求。默认配置及 Rubric 对应固定 50 题。
- 作答和 Judge 入口提供 `--dry-run` 与 `--execute`；API Key 通过运行时环境变量提供。客观题入口的参数和执行方式单独以 `--help` 为准。

查看当前参数：

```powershell
.venv\Scripts\python.exe CampusEval\scripts\evaluation\evaluate_qwen_mini.py --help
.venv\Scripts\python.exe CampusEval\scripts\evaluation\generate_subjective_answers.py --help
.venv\Scripts\python.exe CampusEval\scripts\evaluation\evaluate_subjective_answers.py --help
.venv\Scripts\python.exe CampusEval\scripts\evaluation\aggregate_subjective_scores.py --help
```

新实验建议明确输出到 `runs/`；主观题工具对正式数据和报告目录有输出保护。既有逐题结果位于 [reports/objective/](reports/objective/) 和 [reports/subjective/](reports/subjective/)，对应当时的数据与协议，不能当作新增四类题库已经完成评测的证据。

## PDF 转换与数据维护

今后 PDF 提取统一采用 **[MinerU 网页端](https://mineru.net/)精准解析 → 下载 JSON → 保存到 `workspace/` 下以解析内容命名的子文件夹 → 本地转换、题答配对与纠错 → 校验后保存正式题库**。不再使用轻量 API 提取方式，原 `tools/` 目录已删除。

标准步骤：打开上述网址并进入在线解析页面，登录后上传 PDF，使用网页端精准解析；完成后下载 **JSON 格式**的解析结果。在 `D:\codex-project\高考数据集\CampusEval\workspace` 下新建以解析内容命名的子文件夹，将 JSON 原文件保存到其中。例如题干存入 `workspace/考研数学一_1987-2023_题干/`，解析存入 `workspace/考研数学一_1987-2023_答案解析/`。完整步骤、分批命名规则和保留要求见 [workspace 标准流程](workspace/README.md#网页端精准解析标准步骤)。

此前的下载结果、页码映射和部分源文件仍保存在 `workspace/extracted/kaoyan/precise/`、`workspace/extracted/SOA/` 等旧位置，不因本次规范调整而移动。现有构建器仍可能读取这些固定路径，新批次需先适配输入路径与文件名，再执行转换。上述标准是后续操作规范，不表示历史网页参数与所有操作细节已完整留存。既有 MIT 采用本地 PDF 提取与整理，U-MATH 采用 Parquet 导入，不改写其历史处理方式。

新增规范 JSON/JSONL 可先预览导入计划，明确指定题目文件，避免将回执或 Rubric 当作题目一并扫描：

```powershell
.venv\Scripts\python.exe CampusEval\scripts\maintenance\import_dataset.py `
  --imports CampusEval\workspace\imports\batch\questions.jsonl `
  --target main --dry-run
```

上述路径是待准备的输入示例。通用导入器写入 `main` 或 `training`，不是向任意来源目录自动发布的统一入口；固定 mini 及其 Rubric 不随导入扩充。`--dry-run` 是初步检查，不等于完整暂存校验。实际发布涉及多个文件，不能视为带整体回滚的多文件事务。修改正式数据后还需同步版本清单并重新校验。

工作区中间材料不等于无价值文件。默认 `clean_workspace.py` 会清理 `staging/`、`extracted/` 和工作区 `reports/`，其中可能包含重建输入和迁移备份；日常清理应明确范围，并先用 `--dry-run` 预览。职责说明见 [workspace/README.md](workspace/README.md)。

## 来源、版权与阶段记录

- 各来源内容保留其自身版权和许可说明，不能统一视为项目原创或套用代码许可。
- MIT 的来源署名与许可说明见 [MIT README](datasets/MIT/README.md)。
- SOA 的版权原文见 [COPYRIGHT.txt](datasets/SOA/COPYRIGHT.txt)，说明见 [SOA README](datasets/SOA/README.md)。
- U-MATH 保留的原始许可文件见 [LICENSE](datasets/U-MATH/LICENSE)。
- 三份旧流程、评测协议与扩充方案已归档至 [reports/stages/](reports/stages/README.md)。其中的 5,000 题配额等为历史规划，不能当作当前成果；当前统计以本 README 及正式数据为准。

## 上传范围与本地材料

本项目建议以“数据集与维护评测工程”整体发布。当前 Git 忽略规则仅上传 `workspace/README.md`，工作区其他材料一律保留本地；原始 `workspace/imports/umath_download/test.parquet` 不上传。

| 内容 | 是否上传 | 原因 |
|---|---|---|
| `datasets/` | 必须 | 正式题目、固定子集、Rubric、版本清单、来源与版权说明 |
| `data/images/` | 必须 | 正式题干与解析引用的图片，需保持相对路径 |
| 根目录 `README.md`、`__init__.py`、`requirements.txt`、`.gitignore`、`.gitattributes` | 工程发布时上传 | 项目说明、包结构、运行环境及版本管理规则 |
| `schemas/` | 工程发布时上传 | 数据与评分结果的格式约束 |
| `scripts/`、`evaluation/`、`subjective/` | 工程发布时上传 | 运行入口、构建与纠错输入、客观及主观评分功能 |
| `configs/`、`prompts/` | 工程发布时上传 | 评测配置与提示模板，不包含运行时密钥 |
| `tests/` | 工程发布时上传 | 验证当前功能及后续改动；其中仍有测试依赖历史迁移工具 |
| `reports/` | 建议上传 | 项目已有正式评测成果与阶段记录；只分发题库时可省略 |
| `workspace/README.md` | 建议上传 | 网页精准解析标准步骤与本地材料保存规则 |
| `workspace/` 的其他内容 | 不上传 | 原 PDF、Parquet、网页 JSON、审核材料、暂存、失败记录、迁移备份只保留本地 |
| `runs/`、`tmp/`、缓存、日志 | 不上传 | 新实验运行产物或临时文件；正式成果经整理后保存到 `reports/` |
| `.venv/`、`node_modules/`、`.env*`、密钥文件 | 不上传 | 本地环境或敏感配置 |

`scripts/archive/` 已恢复并保留：其中轻量接口提取工具已停用，历史迁移脚本仍供回归测试与追溯使用。工程上传时不要只移除该目录而留下调用它的测试。

若只发布精简题库包，保留 `datasets/`、`data/images/` 和项目 README 即可；各来源的版权、许可与使用说明应随数据保留。Git 仓库上传与压缩包分发不同：手工打包整个目录不会自动遵守 `.gitignore`，也不应将 `.git/` 历史数据库打入分发包。
