# 历史工具归档

保留一次性迁移和早期考研轻量提取工具，供追溯与特殊维护使用。

本目录保留用于历史追溯，当前回归测试已不再读取迁移脚本中的函数。轻量提取工具 `extract_kaoyan_sources.py` 已停用，仅作历史留存；后续按 [workspace 标准步骤](../../workspace/README.md#网页端精准解析标准步骤)使用网页精准解析并下载 JSON，不再调用轻量 API。

| 文件 | 用途 |
|---|---|
| [migrate_add_source.py](migrate_add_source.py) | 为旧版记录补充顶层 `source`，刷新相关清单 |
| [migrate_image_storage.py](migrate_image_storage.py) | 迁移图片位置、核验备份和引用，并提供显式清理功能 |
| [extract_kaoyan_sources.py](extract_kaoyan_sources.py) | 轻量 MinerU 接口提取；主要用于早期草稿定位，并非当前精准解析结果的替代品 |

命令建议从项目父目录 `D:\codex-project\高考数据集` 执行；使用此目录下的新路径。


这些工具可能下载或上传原材料，或写入题库、图片、报告；按具体脚本用途运行。重新构建仍需相应原始文件与中间材料。
