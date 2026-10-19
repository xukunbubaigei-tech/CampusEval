# MIT 数据构建

收集来源材料、构建首批数据及追加第二批数据。

| 文件 | 用途 |
|---|---|
| [collect_mit_sources.py](collect_mit_sources.py) | 下载来源 PDF，保存来源信息及文本提取结果 |
| [build_mit_dataset.py](build_mit_dataset.py) | 根据首批人工整理内容构建 MIT 题库与来源、报告产物 |
| [extend_mit_dataset.py](extend_mit_dataset.py) | 在既有题库上追加第二批内容并处理指定修订 |

命令建议从项目父目录 `D:\codex-project\高考数据集` 执行；使用此目录下的新路径。


这些工具可能下载或上传原材料，或写入题库、图片、报告；按具体脚本用途运行。重新构建仍需相应原始文件与中间材料。
