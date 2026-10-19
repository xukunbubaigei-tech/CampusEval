# 考研数据构建

准备答案批次、转换精准提取结果、构建题库、裁图及生成说明。

| 文件 | 用途 |
|---|---|
| [prepare_kaoyan_answer_batches.py](prepare_kaoyan_answer_batches.py) | 准备年度答案 PDF 批次及页码来源映射 |
| [convert_kaoyan_precise.py](convert_kaoyan_precise.py) | 将保存的精准解析 JSON 转为按页可定位的中间材料 |
| [build_kaoyan_dataset.py](build_kaoyan_dataset.py) | 配对题目、答案及纠错记录，生成题库与相关记录 |
| [crop_kaoyan_figures.py](crop_kaoyan_figures.py) | 根据原页与裁图任务保存题干、解析引用的图片 |
| [write_kaoyan_report.py](write_kaoyan_report.py) | 根据现有统计与纠错产物生成说明、转换报告 |

命令建议从项目父目录 `D:\codex-project\高考数据集` 执行；使用此目录下的新路径。


这些工具可能下载或上传原材料，或写入题库、图片、报告；按具体脚本用途运行。重新构建仍需相应原始文件与中间材料。

## 后续提取规范

后续采用网页端精准解析并下载 JSON，保存到 `workspace/<解析内容名称>/`，题干与答案解析分别命名。详见 [workspace 标准流程](../../../workspace/README.md#网页端精准解析标准步骤)。旧批次仍保留原位置，运行构建器前按新批次适配输入路径。
