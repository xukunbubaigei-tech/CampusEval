# workspace/ — 数据流水线工作区（P5）

本目录用于新增数据的处理与暂存，**不属于正式发布数据**。正式数据一律在
`datasets/`、`data/images/`；正式模型报告在 `reports/`。

## 目录职责

| 目录 | 用途 | Git 跟踪 |
|---|---|---|
| `imports/` | 用户新提供的原始输入（JSON / JSONL / PDF / 图片 / MinerU 提取结果） | ✅ 保留（当前项目要求原始 PDF 可保留） |
| `review/` | 待人工审核内容（如缺 Rubric 的候选） | ✅ 保留 |
| `rejected/` | 导入失败报告与退回内容（审计用） | ❌ gitignore，按需 `--scope rejected` 清理 |
| `staging/` | 导入流水线原子发布的临时目录 | ❌ gitignore |
| `reports/` | 导入成功报告等派生产物 | ❌ gitignore |
| `extracted/` | OCR / MinerU 解析中间输出 | ❌ gitignore |

## 净室原则

- 中间文件（OCR 裁剪图、临时 JSON、请求回执、staging）**绝不提交**、不混入
  `datasets/` 与 `reports/`。
- 正式数据只引用 `data/images/` 中的规范图片；`workspace/extracted/` 的裁剪图
  不得被正式数据引用。
- 清理命令只作用于本工作区，见下；**永远不触碰** `datasets/`、`data/`、
  `reports/` 与 `workspace/imports/`、`workspace/review/`。

## 清理

```powershell
.venv\Scripts\python scripts\clean_workspace.py --dry-run   # 先看将删除什么
.venv\Scripts\python scripts\clean_workspace.py             # 清理 staging/extracted/reports
.venv\Scripts\python scripts\clean_workspace.py --scope rejected   # 显式清理失败报告
```
