# 通用维护

新增数据导入、发布完整性检查、报告检查及工作区清理。

| 文件 | 用途 |
|---|---|
| [import_dataset.py](import_dataset.py) | 规范化新增题目、暂存校验、发布主库并刷新清单，调用发布校验 |
| [validate_clean_release.py](validate_clean_release.py) | 检查主库、mini、Rubric，并纳入存在的考研、MIT、U-MATH、SOA 题库，检查结构、哈希及引用等 |
| [validate_reports.py](validate_reports.py) | 检查正式报告的可解析性和部分约定的结果完整性 |
| [clean_workspace.py](clean_workspace.py) | 清理指定工作区的中间材料，支持预览 |

命令建议从项目父目录 `D:\codex-project\高考数据集` 执行；使用此目录下的新路径。

