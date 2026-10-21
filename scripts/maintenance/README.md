# 通用维护

新增数据导入、发布完整性检查、报告检查及工作区清理。

| 文件 | 用途 |
|---|---|
| [update_dataset_readme.py](update_dataset_readme.py) | 按实际文件更新数据集 README 的路径、数量、大小与版本哈希 |
| [import_dataset.py](import_dataset.py) | 规范化新增题目、暂存校验、发布主库并刷新清单，调用发布校验 |
| [validate_clean_release.py](validate_clean_release.py) | 检查主库、固定 mini 和原有50份 Rubric 的结构、ID及图片引用，结果写入本地 `workspace/reports/dataset_validation.json` |
| [validate_reports.py](validate_reports.py) | 检查正式报告的可解析性和部分约定的结果完整性 |
| [clean_workspace.py](clean_workspace.py) | 默认仅清理 `workspace/staging/`；其他范围需显式指定，支持预览 |

命令建议从项目父目录 `D:\codex-project\高考数据集` 执行；使用此目录下的新路径。

