# 主观题 Mini（50题）

组成：36道有完整答案与解析的高考主观题，加14道 Conic10K 补充题。`questions.jsonl` 由主数据按 `ids.json` 重建；`rubrics.jsonl` 为已审核评分标准（新三字段纯文本格式：`rubric` 评分标准 + 两种参考解法）。

Rubric 采用实验性统一满分20分，并非试卷官方分值。Judge 按协议 v2 输出整体分数（`score/max_score`）、`reason`、正确/错误内容、证据引用、置信度与人工复核标记，不再逐分项评分。
