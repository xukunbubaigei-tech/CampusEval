# Qwen3.6-35B-A3B 主观题三 Judge 评测报告

## 评测设置

- 数据集：`mini_subjective_50_v2_mineru_reviewed.jsonl`，共 50 题。
- 被测答案：`qwen3.6-35b-a3b_answers/answers.jsonl`，共 50 份。
- Rubric：`deepseek-v4-flash-0731_rubrics_v2/rubrics.approved.jsonl`，50/50 已审核通过。
- Judge：`deepseek-v4-flash`、`glm-5.2`、`kimi-k2.6`，每题各独立评分一次。
- 盲评：评分提示不含被测模型身份；三个 Judge 互不可见，也看不到其他 Judge 结果。
- 权重：三个 Judge 均与被测模型不同家族，本次有效权重均为 1.0，最终分为算术平均。
- 分歧门槛：极差大于满分的 20%，或总体方差大于满分平方的 1%，或任一 Judge 主动要求复核时进入人工复核队列。

## 完整性与有效性

- API 请求：150 次正式请求。
- 有效 Judgment：150；每个 Judge 50 条。
- 完整三 Judge 面板：50/50。
- 重复 `(answer_id, judge_slot)`：0。
- Schema/逐项边界/总分一致性非法记录：0。
- 请求失败或重试耗尽：0。

## 核心结果

- 平均得分：18.1133 / 20。
- 平均得分率：90.5667%。
- 满分率：78.00%。
- 人工复核率：12.00%（6/50）。
- Judge 平均极差占满分比例：6.00%。
- 各 Judge 平均得分率：DeepSeek 90.80%，GLM 92.40%，Kimi 88.50%。
- Token：输入 569,630，输出 139,390，合计 709,020。
- API 累计响应耗时：2,030.731 秒。
- 估算费用：未填写。配置中没有经过核验的当前单价，避免猜测费用。

## 人工复核题

| 题目 | 三 Judge 分数 | 聚合分 | 触发原因 |
|---|---:|---:|---|
| gaokao_math_2023_henan_604_17 | 16 / 13 / 12 | 13.6667 | Judge 主动要求复核 |
| gaokao_math_2024_henan_719_19 | 8 / 5 / 8 | 7.0000 | Judge 主动要求复核 |
| gaokao_math_2025_henan_874_19 | 20 / 16 / 7 | 14.3333 | 极差、方差、Judge 主动要求复核 |
| gaokao_math_2026_henan_1032_19 | 4 / 4 / 4 | 4.0000 | Judge 主动要求复核 |
| gaokao_math_2024_henan_719_17 | 8 / 20 / 8 | 12.0000 | 极差、方差 |
| gaokao_math_2025_henan_874_15 | 18 / 18 / 6 | 14.0000 | 极差、方差 |

第 19 题（2026 河南 1032）三个 Judge 一致给出 4/20；这是被测答案中的数学错误所致，并非题目/Rubric 错配。

## 结果文件

- `judgments.jsonl`：150 份结构化逐项评分。
- `raw_responses.jsonl`：原始响应、token、延迟和校验结果。
- `aggregate/aggregated_scores.jsonl`：50 题加权聚合结果。
- `aggregate/summary.json`：总体、逐题和逐知识点统计。
- `aggregate/disagreement_report.json`：分歧详情。
- `aggregate/human_review_queue.json`：6 题人工复核队列。
- `aggregate/invalid_judgments.json`：非法记录清单（本次为空）。

本报告中的分数仍受“每题统一实验性满分 20 分”这一假设约束，不能替代各原卷官方分值。
