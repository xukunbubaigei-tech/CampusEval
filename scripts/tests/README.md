# 程序回归测试

本目录保留当前程序功能的回归测试。一次性数学试算已移除；数据结构、ID、固定子集、Rubric 和图片引用的重复检查合并为 `test_dataset_release.py`，统一调用正式发布校验器，不再写死可扩充主库的题数或依赖历史迁移脚本。

## 默认测试

从项目父目录执行：

```powershell
.venv\Scripts\python.exe -m unittest discover -s CampusEval\scripts\tests
```

- 作答与评分：答案匹配、多选完整集合、盲评提示、Judge 结果校验与聚合。
- 通用功能：图片读取、输出目录保护、耗时与 token 统计。
- 数据维护：导入成功与拒绝、预览不写入、清理范围保护、训练纠错转换与重复执行。
- Rubric 生成：20分计分解析、字段规范、参考解法、JSON 修复、截断重试和额度错误停止。
- 考研构建：选项切分、缺答案识别及已确认选项修订的回归检查。
- 正式数据：调用 [validate_clean_release.py](../maintenance/validate_clean_release.py) 检查实际题库；固定50份 Rubric 的统一20分尺度与非空第二解法要求也在该校验器中保留。

测试使用模拟响应或预览模式，不调用真实模型 API。需要临时文件的测试使用临时目录，正式数据校验结果写入本地 `workspace/reports/`。`fixtures/subjective/` 的4份小样本仍被评分与聚合测试使用。

## 可选的本地来源集成检查

```powershell
.venv\Scripts\python.exe -m unittest discover -s CampusEval\scripts\tests\integration -p "check_*.py"
```

`integration/check_kaoyan_sources.py` 保存3项依赖本地 MinerU 解析及页码映射的检查：2021年答案对齐、早期试卷二排除、2010年错置页归属。缺少对应原始材料时跳过；文件命名使它们不进入默认测试发现范围。

程序测试和结构检查不能替代全库数学正确性复核。`__pycache__/` 是缓存，无需上传或长期保留。
