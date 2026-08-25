# 客观题 Mini（70题）

`questions.jsonl` 由 `datasets/main/benchmark.jsonl` 按 `ids.json` 的顺序生成。文本模型通常只评测其中62道无图题；多模态模型可以评测全部70题。选择题评分采用 `choice_aware_v2`，多选题必须比较完整选项集合。
