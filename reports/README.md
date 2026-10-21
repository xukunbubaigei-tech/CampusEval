# 模型测试结果

本目录保存模型测试的逐题结果、评分、统计与汇总报告。数据整理、修复审计、Rubric 生成验证和目录清理记录不放在这里。

- `objective/`：客观题模型结果、重评分结果、摘要和横向对比。
- `subjective/`：各模型的被测答案、三 Judge 逐题评分和聚合结果；历史 Qwen3.6-35B-A3B 目录另含10题思考模式试验。
- [2026.10.13-report.md](2026.10.13-report.md)：既有三模型 Mini 测试汇总。

这些结果对应运行时的数据与协议，是历史记录。数据集内容或评分协议改变后，不应原地覆盖；新测试先写入 `runs/`，验证完成后再作为新的正式报告发布。

[数据维护摘要](../datasets/MAINTENANCE.md) 集中记录已完成修订、验证范围和待处理问题。历史协议与阶段文档移至 [docs/history/](../docs/history/README.md)。审计及校验输出保存在本地 `workspace/reports/`，正式数据清单见 [数据集 README](../datasets/README.md)。
