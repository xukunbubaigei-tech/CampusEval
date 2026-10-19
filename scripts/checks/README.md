# 专项校验与数学复核

按来源检查题库，以及核验代码中明确列出的公式和数值结果。

| 文件 | 用途 |
|---|---|
| [validate_kaoyan_dataset.py](validate_kaoyan_dataset.py) | 考研题库的结构、选项答案、图片及部分公式格式检查 |
| [validate_soa_dataset.py](validate_soa_dataset.py) | SOA 格式检查，并与本地原 PDF 答案表逐项对照 |
| [verify_kaoyan_corrections.py](verify_kaoyan_corrections.py) | 对指定考研纠错公式进行符号或数值核验 |
| [verify_mit_mathematics.py](verify_mit_mathematics.py) | 对 MIT 首批指定结果进行数学核验 |
| [verify_mit_batch2.py](verify_mit_batch2.py) | 对 MIT 第二批指定结果进行数学核验 |

命令建议从项目父目录 `D:\codex-project\高考数据集` 执行；使用此目录下的新路径。


数学核验仅覆盖代码列出的断言，不能作为全题库数学正确性的证明。部分工具运行时会更新校验报告。
