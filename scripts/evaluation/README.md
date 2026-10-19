# 模型评测

模型作答、主观题评分与聚合、客观题评测与重评分的日常入口。

| 文件 | 用途 |
|---|---|
| [generate_subjective_answers.py](generate_subjective_answers.py) | 为主观题生成模型作答 |
| [evaluate_subjective_answers.py](evaluate_subjective_answers.py) | 依据 Rubric 对已有模型答案进行盲评 |
| [aggregate_subjective_scores.py](aggregate_subjective_scores.py) | 校验并聚合 Judge 结果，输出分数与分歧记录 |
| [evaluate_qwen_mini.py](evaluate_qwen_mini.py) | 客观题模型作答与最终答案匹配，调用 `evaluation/metrics.py` |
| [rescore_qwen_mini.py](rescore_qwen_mini.py) | 读取已保存结果进行本地重评分，支持答案纠错及历史协议筛选 |

命令建议从项目父目录 `D:\codex-project\高考数据集` 执行；使用此目录下的新路径。

