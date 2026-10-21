# 训练集清理

`repair_training.py` 从 JSONL 快照生成单独的候选输出，不原地覆盖输入。`overrides.json` 保存按既有 ID 审核的最终结论和需要单独修复的正文；通用规则负责命令分隔、已确认的错字、模板残片及数学表达式格式化。

Conic10K 的 Python 风格表达式通过白名单 AST 转为 LaTeX，不执行表达式代码；集合、区间、并集、方程、度数、正负号分别处理。高考解答题将原 `final_answer` 中的完整解答移到 `solution`，再设置分小问的结论；有语义损坏的解答使用审核后的重写版本。重复运行不会用结论覆盖详细解析。

从项目根目录运行，例如：

```powershell
python scripts/curation/training/repair_training.py --input input.jsonl --output candidate.jsonl
```

输出后仍须核验 Schema、ID 和数量、公式渲染、数学修正、固定子集与 rubric 的一致性，再发布并更新清单。脚本不生成新题、不重新编号、不自动删除题目、不重新生成 rubric。
