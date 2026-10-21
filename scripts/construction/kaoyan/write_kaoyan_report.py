"""Write the human-readable standalone import report from checked artifacts."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
DATA = BASE / "datasets/kaoyan"


def main():
    report = json.loads((DATA / "conversion_report.json").read_text(encoding="utf-8"))
    corrections = json.loads((DATA / "corrections.json").read_text(encoding="utf-8"))
    readme = f"""# 考研数学一：1987—2023

已从用户指定的本地 PDF 完成首轮收录，共 **{report['imported_count']} 条记录**，覆盖37个年份；不含1987—1996年试卷二。题干只取自纯真题合集，答案和原有解析取自指定的37份年度解析。既有 `datasets/main` 不变。

其中 **{report['empty_solution_count']} 条 `answer.solution` 为空**；它们保留最终答案，没有补写原材料缺失的解析。**{report['manually_rechecked_or_corrected_count']} 条问题记录经过原页复核或用户授权的数学校正**，修改依据与原始 OCR 在 [corrections.json](corrections.json) 中逐条记录，不声称这些校正是官方解答。

## 使用文件

- `questions.jsonl`：沿用 id、source、question、answer、metadata 五个顶层字段，source 为 university_exam。
- `data/images/kaoyan/`：从原 PDF 裁出的题图及解析图，保留相对路径引用。
- `conversion_report.md` / `.json`：数量、年度覆盖、规则与限制。
- `workspace/reports/kaoyan_validation.json`：本地格式、重复、选项答案、图片路径及公式定界符检查结果。
- `corrections.json`：原页位置、修改前后记录及校正依据。
- `correction_verification.json`：对所列校正公式进行的符号/数值核验。
- `pending_review.jsonl`：本轮暂存队列；当前为 {report['pending_count']} 条。

## 重要边界

本批已完成转换与结构校验，**不等于全部805题均经过独立数学审校**。轻量 OCR 草稿没有作为最终输入；本批采用 MinerU 已登录网页的完整 JSON 结果，含127页题干和442页年度解析，并保留页码与原文件。

2022年第2题原稿选项重复的问题已由用户于2026-10-19人工修正，当前只有B选项成立，答案为 `B`。人工修正已同步至生成配置和逐条校正记录。

早期的选择、填空小题按分组题号分别收录；解答大题保留所有小问，未按小问人为增加样本。解答题原文未单列简短结论时，`final_answer` 保留原材料完整解答；校正记录优先使用已核对的简短结果。

`metadata.paper_name` 使用材料中可确认的年份与卷名；没有可确认卷名时回填 source。本批未编造学校、官方解答身份或额外考试年份。

## 可复现处理

脚本在 `scripts/`：`scripts/construction/kaoyan/prepare_kaoyan_answer_batches.py`、`scripts/construction/kaoyan/convert_kaoyan_precise.py`、`scripts/construction/kaoyan/build_kaoyan_dataset.py`、`scripts/construction/kaoyan/crop_kaoyan_figures.py`、`scripts/checks/validate_kaoyan_dataset.py`。历史一次性公式试算脚本已清理，校正依据保存在纠错配置与数据维护摘要中。网页精准解析 JSON 及逐年页码映射保存在本机 `workspace/extracted/kaoyan/precise/`；该中间目录不随代码分发。免登录轻量接口仅用于早期草稿定位，后续已停止使用。后续统一访问 https://mineru.net/ ，通过网页端精准解析并下载JSON，存入workspace下以解析内容命名的直接子文件夹；详见项目workspace/README.md。
"""
    (DATA / "README.md").write_text(readme, encoding="utf-8")
    lines = ["# 本地考研数学一收录报告", "", "完成日期：2026-10-19。", "",
             f"题干127页，年度答案解析442页；覆盖1987—2023年，共{report['imported_count']}条，空解析{report['empty_solution_count']}条，待核对队列{report['pending_count']}条。",
             "", "题型统计：" + "，".join(f"{k}{v}条" for k,v in report['question_types'].items()) + "。", "",
             "## 年度覆盖", "", "| 年份 | 候选 | 收录 |", "|---|---:|---:|"]
    lines += [f"| {year} | {v['candidates']} | {v['imported']} |" for year,v in report['by_year'].items()]
    lines += ["", "## 已处理的边界", "",
              "- 1987—1996年的试卷二按用户要求整段排除；同卷一重复引用也未据此增加题数。",
              "- 合集第111页放错位置；与2010年年度解析的21—23题一致，已归回2010年。",
              "- 2022年合集缺年份标题，按年度解析中一致的题干、题号确认归属。",
              "- 1997年重叠字形与残损编号按原页及年度解答修复；没有添加新学校或新年份。",
              "- 本次54条复核/校正已获得用户明确授权；无原解析的题仍不补写解析。",
              "- 2022年第2题已采用用户人工修正的选项，最终答案为B；修改依据见逐条校正记录。", "",
              "## 校正逐条摘要", "", "完整修改前后文本与PDF页码见 corrections.json。", "",
              "| ID | 依据 |", "|---|---|"]
    lines += [f"| {c['id']} | {c['verification_basis'].replace('|',' / ')} |" for c in corrections]
    lines += ["", "## 校验与限制", ""] + ["- " + s for s in report['limitations']]
    lines += ["- JSON Schema、ID、完全重复题干、选项答案、图片引用和美元公式定界符的结果见本地 workspace/reports/kaoyan_validation.json。",
              "- 符号与数值交叉验证的范围和计算项目见 correction_verification.json，不能将其外推为805题全部数学正确。", ""]
    (DATA / "conversion_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("Wrote standalone dataset README and conversion report")


if __name__ == "__main__":
    main()
