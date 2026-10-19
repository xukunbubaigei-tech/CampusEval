# MIT 英文大学数学题库

## 数据概况

本题库收录 MIT OpenCourseWare 的部分考试和练习题，共 **146 条英文题目**，全部包含配套解析。覆盖四门课程，不代表 MIT 课程材料全量。首批 52 条，第二批新增 94 条；按原大题保留全部小问。

本目录仅保留 `questions.jsonl` 和本说明。转换概况、收录规则、校验结果及许可署名合并于此，不再保留独立报告、候选来源清单、重复题转换稿或逐题校正依据文件。

### 学科分布

| 主学科 | 数量 |
|---|---:|
| 高等数学 | 41 |
| 线性代数 | 19 |
| 概率论与数理统计 | 86 |

### 课程覆盖

| 课程 | 名称 | 学期 | 数量 |
|---|---|---|---:|
| 18.01SC | Single Variable Calculus | Fall 2010 | 14 |
| 18.02SC | Multivariable Calculus | Fall 2010 | 29 |
| 18.06 | Linear Algebra | Spring 2010 | 17 |
| 18.05 | Introduction to Probability and Statistics | Spring 2022 | 86 |

课程归属与主学科是两种统计口径：课程中的部分题目按实际数学内容划入其他学科，因此两张表不逐项对应。

### 题型与图片

| 题型 | 数量 |
|---|---:|
| 解答题 | 138 |
| 证明题 | 6 |
| 选择题 | 2 |

- 无空解析记录。
- 图片共 **17 张**：题图 2 张，解析图 15 张。
- 图片统一存放在项目根目录的 [`data/images/MIT/`](../../data/images/MIT/)。

## 数据格式与使用

`questions.jsonl` 每行是一条 JSON 记录，顶层字段为 `id`、`question`、`answer`、`metadata`、`source`。

| 字段 | 含义 |
|---|---|
| `id` | 题目唯一标识，保留原有课程、考试与题号编码 |
| `question.text` | 英文题干及 LaTeX 公式 |
| `question.images` | 题图路径列表 |
| `question.options` | 选择题选项；其他题型通常为空列表 |
| `answer.final_answer` | 最终答案或结论 |
| `answer.solution` | 基于原配套解答整理、压缩或校正的解析 |
| `metadata.paper_name` | 已确认的试卷或练习名称 |
| `metadata.question_type` | 解答题、证明题或选择题 |
| `source` | 固定为 `university_exam` |

所有图片路径均相对于项目根目录，例如 `data/images/MIT/文件名.png`。题图由 `question.images` 引用，解析图由 `answer.solution` 中的 Markdown 链接引用；解析图不作为题图发送给待测模型。

## 转换方法与收录规则

- 采用 PDF 文字层提取、原页图文核对及英文/LaTeX 结构化整理；本批未使用 MinerU 输出作为转换输入。
- 题目与已有配套解答对齐，保留全部要求的小问，移除评分说明及考试行政指示。
- 解析基于已发布解答压缩、校正，不是官方解答的逐字副本；缺少原解析的候选不从零编写解析。
- 52 条记录涉及编辑校正或条件澄清；已生效的修订保留在题目和解析中，不在本说明逐题列出依据。
- 18.05 Exam 1 Long List 作为该组练习的主版本，重印练习不重复计数；第 41 题与第 26 题共用数据和模型，第 71 题与第 69 题为纯参数替换的 CLT 模板，未另行收录。
- 18.02SC Practice Final 第 15/16 题合为一条，保留两种解法。
- 条件不充分或矛盾、仅引用其他作业而无自足题干、原解答有待澄清、没有唯一标准结论的候选不收录。
- 精确文本去重不能保证消除全部数学等价题或跨语言变体。
- 本目录整理不改变其他题库及既有训练、评测划分。

## 校验结果与范围

2026-10-19 目录整理时重新检查：146 条记录全部通过现有 JSON Schema，ID 无重复，解析均非空；17 张图片引用有效。整理前后 `questions.jsonl` 及所有引用图片的 SHA-256 均未变化。

此前转换校验报告记录为通过，检查范围包括：题库内部及与 main/kaoyan 的规范化精确题干去重、公式美元定界符与花括号平衡、安全的本地图片引用、原材料页码范围、原有记录保留以及输入 PDF 校验和。这些历史检查不表示本次重新读取了原 PDF。

两批历史符号/数值检查分别执行 **48 项**和 **90 项**，报告均为通过。检查涉及导数、积分、矩阵、概率分布、统计估计等列明的计算；数值矩阵或有限样本检查不能代替一般性证明。

已核对所收录题目的题答与原页，但尚无第二位独立审校者逐题签核。结构及局部计算检查不等于全部题干转写和每一步数学推理均已获独立验证。

当前 `questions.jsonl` SHA-256：

```text
11bc43fbe124e2474bb858e0bc0494f8f92fc45c20160f1ed5102eab5cb4bd64
```

## 署名、许可与修改说明

Source: Massachusetts Institute of Technology, MIT OpenCourseWare.

| 课程 | 署名教师 |
|---|---|
| 18.01SC | David Jerison |
| 18.02SC | Denis Auroux |
| 18.06 | Gilbert Strang |
| 18.05 | Jeremy Orloff、Jennifer French Kamrin |

The 18.01SC content development team also credits Arthur Mattuck, Haynes Miller, Benjamin Brubaker, Jeremy Orloff, Heidi Burgiel, Christine Breiner, David Jordan and Joel Lewis.

沿用收录时记录的 MIT OCW [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 许可说明，保留署名、非商业及相同方式共享条件，以及各资源单独标注的声明；课程内容不改标为本仓库代码许可证。修改包括分题、英文转写、LaTeX 整理、解答压缩、图像裁切、编辑校正及条件澄清。MIT 不为本数据整理工作背书。

以下保留本批已采用的 24 份题目或解答材料的原始资源链接，用于署名与资源识别；不保留候选材料采集清单。

| 课程 | 原资源 |
|---|---|
| 18.01SC | [Final Exam (PDF)](https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/resources/mit18_01scf10_final/) |
| 18.01SC | [Solutions to Final Exam (PDF)](https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/resources/mit18_01scf10_finalsol/) |
| 18.02SC | [Final Exam (PDF)](https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/resources/mit18_02sc_finalexam/) |
| 18.02SC | [Solutions (PDF)](https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/resources/mit18_02sc_finalexamsol/) |
| 18.06 | [mit18_06s10_exam1_s10](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/resources/mit18_06s10_exam1_s10/) |
| 18.06 | [mit18_06s10_exam1_s10_sol](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/resources/mit18_06s10_exam1_s10_sol/) |
| 18.06 | [mit18_06s10_exam2_s10](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/resources/mit18_06s10_exam2_s10/) |
| 18.06 | [mit18_06s10_exam2_s10_soln](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/resources/mit18_06s10_exam2_s10_soln/) |
| 18.06 | [mit18_06s10_exam3_s10](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/resources/mit18_06s10_exam3_s10/) |
| 18.06 | [mit18_06s10_exam3_s10_soln](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/resources/mit18_06s10_exam3_s10_soln/) |
| 18.05 | [Exam 1 (PDF)](https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/resources/mit18_05_s22_exam01_pdf/) |
| 18.05 | [Exam 1 Solutions (PDF)](https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/resources/mit18_05_s22_exam01_sol_pdf/) |
| 18.05 | [Exam 2 (PDF)](https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/resources/mit18_05_s22_exam02_pdf/) |
| 18.05 | [Exam 2 Solutions (PDF)](https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/resources/mit18_05_s22_exam02_sol_pdf/) |
| 18.05 | [Big List of Problems (PDF)](https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/resources/mit18_05_s22_prac_exam01_all_pdf/) |
| 18.05 | [Big List of Solutions (PDF)](https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/resources/mit18_05_s22_prac_exam01_all_sol_pdf/) |
| 18.05 | [Exam 2 Many Practice Problems (PDF)](https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/resources/mit18_05_s22_prac_exam02a_pdf/) |
| 18.05 | [Exam 2 Many Practice Solutions (PDF)](https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/resources/mit18_05_s22_prac_exam02a_sol_pdf/) |
| 18.02SC | [Practice Final Exam (PDF)](https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/resources/mit18_02sc_pracfinal/) |
| 18.02SC | [Solutions (PDF)](https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/resources/mit18_02sc_pracfinalsol/) |
| 18.06 | [mit18_06s10_final_exam](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/resources/mit18_06s10_final_exam/) |
| 18.06 | [mit18_06s10_final_answers](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/resources/mit18_06s10_final_answers/) |
| 18.05 | [Final Exam (PDF)](https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/resources/mit18_05_s22_exam_final_pdf/) |
| 18.05 | [Final Exam Solutions (PDF)](https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/resources/mit18_05_s22_exam_final_sol_pdf/) |
