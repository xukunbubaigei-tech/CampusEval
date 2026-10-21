# 模型评测

模型作答、主观题评分与聚合、客观题评测与重评分的日常入口。

| 文件 | 用途 |
|---|---|
| [generate_subjective_answers.py](generate_subjective_answers.py) | 为主观题生成模型作答 |
| [generate_subjective_rubrics.py](generate_subjective_rubrics.py) | 为有原解析的解答题、证明题生成 20 分制 Rubric 待审核稿，支持断点续跑 |
| [evaluate_subjective_answers.py](evaluate_subjective_answers.py) | 依据 Rubric 对已有模型答案进行盲评 |
| [aggregate_subjective_scores.py](aggregate_subjective_scores.py) | 校验并聚合 Judge 结果，输出分数与分歧记录 |
| [evaluate_qwen_mini.py](evaluate_qwen_mini.py) | 客观题模型作答与最终答案匹配，调用 `evaluation/metrics.py` |
| [rescore_qwen_mini.py](rescore_qwen_mini.py) | 读取已保存结果进行本地重评分，支持答案纠错及历史协议筛选 |

命令建议从项目父目录 `D:\codex-project\高考数据集` 执行；使用此目录下的新路径。

Rubric 生成使用 `prompts/subjective_rubric_generator_zh_v1.txt`。必须显式传入
`--model`、`--base-url`、`--output-dir`，并选择 `--dry-run` 或 `--execute`。
密钥通过 `RUBRIC_API_KEY` 环境变量传入，或用 `--api-key-stdin` 在交互终端隐藏输入；
不将密钥写入配置文件。`--limit` 可试生成少量题目，之后去掉此参数在同一目录续跑。

输出目录须位于正式 `datasets/`、`reports/` 之外。`rubrics.draft.jsonl` 保持既有
Rubric Schema；生成模型、调用用量、失败记录和疑点保存在相邻的 journal、manifest
与报告文件中。输入题目、图像、提示或模型配置变化时应新建输出目录。
程序检查题目 ID、五段结构、每项分值和总分 20，但这些检查不代表数学内容已审核。
缺少原解析的题目会列入跳过清单；第二解法不能可靠给出时为 null。

更换接口时，新建输出目录并用 `--resume-from` 导入此前成功结果；题目、图片和提示
必须一致。明确换模型时再加 `--allow-model-change-on-resume`，成功记录保留原模型来源。
认证或额度错误会停止后续提交；截断响应会提高输出上限后重试，不重复拼入已截断文本。
运行结束后可执行 `scripts/maintenance/finalize_rubric_drafts.py --output-dir <目录>`，
重新核验并导出 Rubric、逐题生成来源、覆盖率报告和可读复核清单。

