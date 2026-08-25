# 主数据集

- `benchmark.jsonl`：140道 Benchmark 题目；
- `training.jsonl`：1000道训练题，其中566道来自 GAOKAO-Bench、434道来自 Conic10K。

训练集尚未逐题权威复核，不能直接当作严格测试集。每条记录仅保留 `id`、`question`、`answer`、`metadata` 四个核心字段。修改主数据后必须重建两个 mini 数据集并运行完整性校验。
