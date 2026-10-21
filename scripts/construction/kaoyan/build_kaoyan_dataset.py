"""Match local Math I questions to their annual MinerU precise extractions.

Unmatched or visibly ambiguous material remains in a review queue. No solutions
are generated. Original intermediate files remain available for rechecking.
"""
from __future__ import annotations

import json
import re
import unicodedata
import runpy
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
WORK = BASE / "workspace/extracted/kaoyan/precise"
OUT = BASE / "datasets/kaoyan"
CORRECTIONS = runpy.run_path(str(BASE / "scripts/curation/kaoyan/kaoyan_corrections.py"))["CORRECTIONS"]
GRAPHIC_OPTIONS = {
    (2001, 2, 1): [2, 3, 4, 5],
    (2002, 2, 4): [1, 2, 3, 4],
    (2009, 1, 3): [1, 2, 4, 5],
}
CN = {s: i for i, s in enumerate(
    ["", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二", "十三", "十四", "十五"])}
MAJOR = re.compile(r"^([一二三四五六七八九十]+)(?:[、.．]|(?=【))")
NUMBER = re.compile(r"^(?:\(?(\d{1,2})\)|([0-9]{1,2})[.、]|\((\d{1,2})(?=\s))\s*")
MARKER = re.compile(r"【(?:答案|解析|详解|分析|解|证明|证)】")


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def norm(s):
    return unicodedata.normalize("NFKC", s).strip()


def clean(s):
    s = re.sub(r"[ \t]+", " ", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def pages(name):
    data = json.loads((WORK / (name + ".pages.json")).read_text(encoding="utf-8"))
    for page in data:
        page["source_name"] = name
        for b in page["blocks"]:
            t = clean(norm(b["text"]))
            if name == "questions_all":
                prefixes = {
                    (56, "某种飞机"): "(16) ",
                    (62, "设区域"): "(15) ",
                    (65, "设函数"): "(19) ",
                    (71, "设 $a_{n}$"): "(16) ",
                }
                for (n, prefix), label in prefixes.items():
                    if page["page"] == n and t.startswith(prefix):
                        t = label + t
                if page["page"] == 117:
                    t = re.sub(r"^([345])\)", lambda m: "(1" + m[1] + ")", t)
            else:
                year = int(name[-4:])
                # Lost question labels, identified using the matching question
                # statement and the neighbouring original labels.
                prefixes = {
                    (1990, 8, "求幂级数"): "四、",
                    (2016, 2, "解二次型的矩阵"): "(6) ",
                    (2017, 4, "解 X 的概率密度"): "(14) ",
                    (2018, 4, ")解(I)"): "(18",
                    (2010, 8, "$\\begin{array}{r l} f (x, y)"): "(22) ",
                    (2022, 5, "$x ^ { 2 } + y ^ { 2 }"): "(13) ",
                }
                for (y, n, prefix), label in prefixes.items():
                    if year == y and page["page"] == n and t.startswith(prefix):
                        t = label + t
                if year == 2001 and "三【详解】" in t:
                    t = "三、【详解】\n" + t
                t = re.sub(r"\((\d{1,2})\s*【\)([^】]+)】", r"(\1)【\2】", t)
                t = re.sub(r"\((\d{1,2})【", r"(\1)【", t)
                t = re.sub(r"\$\s*\(\s*(\d)\s+(\d)\s*\)\s*~?", r"\n(\1\2) $", t)
            b["text"] = t
        if name == "questions_all" and page["page"] == 40:
            fixed = []
            skip = False
            for b in page["blocks"]:
                if b["text"].startswith("$f (x)"):
                    b["text"] = (r"(3) 设 $f(x)=\begin{cases}x,&0\le x\le\frac12,\\2-2x,&\frac12<x<1,\end{cases}$ "
                                 r"$S(x)=\frac{a_0}{2}+\sum_{n=1}^{\infty}a_n\cos n\pi x,\ -\infty<x<+\infty$, "
                                 r"其中 $a_n=2\int_0^1 f(x)\cos n\pi x\,dx\ (n=0,1,2,\cdots)$, "
                                 r"则 $S(-\frac52)$ 等于（ ）。(A) $\frac12$ (B) $-\frac12$ (C) $\frac34$ (D) $-\frac34$")
                    fixed.append(b)
                    skip = True
                elif skip and b["text"].startswith("(4)"):
                    skip = False
                    fixed.append(b)
                elif not skip:
                    fixed.append(b)
            page["blocks"] = fixed
    return data


def units(pages_):
    for page in pages_:
        for b in page["blocks"]:
            # Preserve image/table blocks with their original coordinates.
            text = norm(b["text"])
            if not text and b["type"] not in {"image", "chart"}:
                continue
            yield {"text": text, "page": page["page"], "bbox": b["bbox"],
                   "type": b["type"], "page_size": page["page_size"],
                   "source_name": page["source_name"]}


def figure_path(u):
    coordinates = "_".join(str(round(v)) for v in u["bbox"])
    return f"data/images/kaoyan/{u['source_name']}_p{u['page']:03d}_{coordinates}.png"


def sections(items):
    result = []
    current = None
    for u in items:
        m = MAJOR.match(u["text"])
        if m and m[1] in CN:
            current = {"major": CN[m[1]], "heading": u["text"], "items": []}
            result.append(current)
            # Some answer sections begin immediately with a solution marker.
            marker = MARKER.search(u["text"])
            if marker:
                current["items"].append(dict(u, text=u["text"][marker.start():]))
        elif current is not None:
            current["items"].append(u)
    return result


def section_type(s):
    if "填空" in s["heading"]:
        return "填空题"
    if "选择" in s["heading"] or "选抒" in s["heading"]:
        return "选择题"
    return "解答题"


def numbered(items, answers=False, expected_start=None):
    items = [dict(u) for u in items]
    if items and expected_start is not None and not NUMBER.match(items[0]["text"]):
        items[0]["text"] = f"({expected_start}) " + items[0]["text"]
    result = []
    current = None
    last = 0
    first_numbered = next((u["text"] for u in items if NUMBER.match(u["text"])), "")
    has_markers = answers and bool(MARKER.search(first_numbered[:30]))
    for u in items:
        # OCR can merge neighbouring numbered questions into one paragraph.
        text = re.sub(r"(?<!^)(?<!\n)(\(\d{1,2}\)\s*【(?:答案|解析|详解|分析)】)", r"\n\1", u["text"])
        pieces = re.split(r"\n(?=(?:\([0-9]{1,2}\)|[0-9]{1,2}[.、]))", text)
        for piece in pieces:
            v = dict(u, text=piece.strip())
            m = NUMBER.match(v["text"])
            n = int(next(g for g in m.groups() if g)) if m else None
            marker_start = bool(MARKER.search(v["text"][:30]))
            short_answer = bool(m and re.match(r"^[A-Da-d](?:\W|$)", v["text"][m.end():].strip()))
            explicit_stem = bool(m and v["text"][m.end():].startswith("设级数"))
            answer_cycle = answers and n is not None and n < last and marker_start
            new = n is not None and (n > last or answer_cycle) and (not has_markers or marker_start or short_answer or explicit_stem)
            if new:
                current = {"number": n, "items": []}
                result.append(current)
                last = n
                v["text"] = v["text"][m.end():]
            elif m and n == last and marker_start:
                v["text"] = v["text"][m.end():]
            if current is not None:
                current["items"].append(v)
    return result


def question_groups():
    groups = defaultdict(list)
    exclusions = []
    year = None
    excluded = False
    for u in units(pages("questions_all")):
        m = re.match(r"^((?:19|20)\d{2})\s*年全国", u["text"])
        if m:
            year = int(m[1])
            excluded = False
            continue
        # The 2022 scan omits its year heading. Identify it by the corresponding
        # local annual answer's identical first question; record this exception.
        if u["page"] == 120:
            year, excluded = 2022, False
        if u["page"] == 111:
            groups[2010].append(u)
            continue
        if year is None:
            continue
        if 1987 <= year <= 1996 and re.search(r"试卷\s*(?:II|Ⅱ|二)", u["text"]):
            excluded = True
        if excluded:
            exclusions.append({"year": year, "page": u["page"], "reason": "用户明确排除试卷二"})
            continue
        if re.match(r"^\(?试卷", u["text"]) or re.match(r"^数学\s*[（(]", u["text"]):
            continue
        groups[year].append(u)
    return groups, exclusions


def make_questions():
    groups, exclusions = question_groups()
    result = []
    for year, items in groups.items():
        for section in sections(items):
            kind = section_type(section)
            split = kind != "解答题" or year >= 2004
            start = expected_number(year, section["major"])
            children = numbered(section["items"], expected_start=start) if split else [{"number": 0, "items": section["items"]}]
            for child in children:
                key = (year, section["major"], child["number"])
                text = clean("\n\n".join(x["text"] for x in child["items"]))
                result.append({"key": key, "kind": kind, "text": text,
                               "items": child["items"], "heading": section["heading"]})
    return result, exclusions


def expected_number(year, major):
    if year < 2004 or major == 1:
        return 1
    if major == 2:
        return 7 if year <= 2006 else 11 if year == 2007 or year >= 2021 else 9
    return 17 if year == 2007 or year >= 2021 else 15


def make_answers(year):
    ss = sections(list(units(pages(f"answers_{year}"))))
    # Files such as 1989 and 1993 contain a full paper followed by its solutions.
    # Prefer the final cycle of numbered sections.
    by_major = {s["major"]: s for s in ss}
    result = {}
    for major, section in by_major.items():
        kind = section_type(section)
        split = kind != "解答题" or year >= 2004
        children = numbered(section["items"], answers=True, expected_start=expected_number(year, major)) if split else [{"number": 0, "items": section["items"]}]
        for child in children:
            text = clean("\n\n".join(u["text"] if u["type"] not in {"image", "chart"}
                                      else f"![原解析图]({figure_path(u)})" for u in child["items"]))
            result[(year, major, child["number"])] = {"text": text, "items": child["items"]}
    if year == 2021:
        # The annual answer material orders these three worked responses as
        # distance / double integral / series, unlike the question collection.
        keys = [(2021, 3, number) for number in (18, 19, 20)]
        current = [result[key] for key in keys]
        if ("曲线" in current[0]["text"] and "I" in current[1]["text"]
                and "级数" in current[2]["text"]):
            result.update(zip(keys, (current[2], current[0], current[1])))
        assert ("级数" in result[keys[0]]["text"]
                and "曲线" in result[keys[1]]["text"]
                and "I" in result[keys[2]]["text"]), "2021 answers 18--20 need content alignment review"
    return result


def split_options(text):
    text = re.sub(r"\$\\mathrm\s*\{\(([A-D])\)(.*?)\}\$", r"(\1) $\2$", text)
    pattern = re.compile(r"(?<![A-Za-z\\])\(([A-D])\)|(?<![A-Za-z\\])([A-D])\.\s*")
    matches = list(pattern.finditer(text))
    # Matrix/event names such as P(A), f(B) inside formulas are not labels.
    matches = [m for m in matches if text[:m.start()].count("$") % 2 == 0]
    labels = [m[1] or m[2] for m in matches]
    if labels != ["A", "B", "C", "D"]:
        return text, [], f"选项标签无法唯一分离:{','.join(labels)}"
    options = [{"label": m[1] or m[2], "text": clean(text[m.end():matches[i+1].start() if i+1 < 4 else len(text)])}
               for i, m in enumerate(matches)]
    return clean(text[:matches[0].start()]), options, None


def response_parts(question, answer):
    raw = answer["text"]
    # Related textbook material follows the worked answer; preserve the original
    # JSON but omit it from the solution field.
    raw = clean(raw.split("【相关知识点】")[0])
    raw = raw.replace(r"\tag{\(x\in (0,1)\}", r"\quad (x\in(0,1))")
    raw = raw.replace(r"\tag{\((^{*} *)\}", r"\tag{**}")
    explicit = re.search(r"【答案】\s*(.*?)(?=【(?:解析|详解|分析|解|证明)】|\n\n|$)", raw, re.S)
    final = clean(explicit[1]) if explicit else ""
    marker = re.search(r"【(?:解析|详解|解|证明)】|(?:^|\n)(?:解法|证明|解|证)|(?:^|\n)\((?:I|II|III|1|2)\)\s*(?:解|证)", raw)
    solution = clean(raw[marker.start():]) if marker else ""
    if marker and raw[:marker.start()].count("$") % 2:
        # A solution label can be OCR'd inside a display equation. Keep its
        # opening array and math delimiters instead of truncating the formula.
        solution = raw[raw.rfind("$", 0, marker.start()):]
        solution = re.sub(r"【(?:解析|详解|解|证明)】", "", solution)
    if solution.startswith("【"):
        solution = re.sub(r"^【[^】]+】\s*", "", solution)
    if question["kind"] == "选择题":
        # Explicit statement conclusions, never select a letter from options.
        if not re.fullmatch(r"[($\s]*[A-Da-d][)$.\s。]*", final):
            final = ""
        if not final:
            m = re.match(r"^\s*([A-Da-d])(?:\s|$|[.。])", raw)
            if m:
                final = m[1]
        if not final:
            ms = re.findall(r"(?:故应选|故选|所以选|正确选项为)[\s(]*([A-Da-d])", raw)
            if ms:
                final = ms[-1]
        if final:
            final = re.search(r"[A-Da-d]", final)[0].upper()
        return final, solution, "explicit_choice" if final else "missing_final_answer"
    if not final and marker:
        # Do not manufacture a short final result for a multi-part derivation.
        # Retain the supplied worked response verbatim as the answer as well.
        final = solution
        return final, solution, "original_worked_response"
    if not final and raw:
        first = raw.split("\n\n", 1)[0]
        if question["kind"] == "填空题" and (first.startswith("$") or len(first) < 35):
            final = first
        elif question["kind"] == "解答题" and raw.startswith("$"):
            final = raw
            solution = raw if len(raw) > 200 else ""
        elif question["kind"] == "解答题" and re.search(r"\\text\s*\{证", raw):
            final, solution = raw, raw
    return final, solution, "explicit_answer" if final else "missing_final_answer"


def publish(questions, answers, exclusions):
    records, pending, audit = [], [], []
    correction_log = []
    manual_choices = {(1987, 5, 1): "C", (1987, 5, 2): "D",
                      (1987, 5, 3): "B", (1987, 5, 4): "C",
                      (1988, 3, 1): "B", (1988, 3, 2): "A", (1988, 3, 3): "C",
                      (1988, 3, 4): "B", (1988, 3, 5): "D"}
    # Transcribed from the underlined answers on the original annual PDFs.
    manual_fills = {
        (1987, 1, 2): r"$-\frac{1}{\ln 2}$", (1987, 1, 3): r"$\frac32$",
        (1987, 1, 4): r"$-18\pi$", (1987, 1, 5): r"$(1,1,-1)$",
        (1987, 10, 1): r"$1-(1-p)^n$；$[1+(n-1)p](1-p)^{n-1}$",
        (1987, 10, 2): r"$\frac{53}{120}$；$\frac{20}{53}$",
        (1988, 2, 1): r"$(2t+1)e^{2t}$", (1988, 2, 3): r"$\frac1{12}$",
        (1988, 2, 4): "40", (1988, 10, 1): r"$\frac13$",
        (1988, 10, 2): r"$\frac{17}{25}$", (1988, 10, 3): "0.9876",
    }
    for q in questions:
        key = tuple(q["key"])
        year, major, number = key
        record_id = f"kaoyan_math1_{year}_{major:02d}_{number:02d}"
        a = answers.get(key)
        correction = CORRECTIONS.get(key)
        reasons = []
        if not a:
            reasons.append("未匹配到原答案段")
            final, solution, method = "", "", "unmatched"
        else:
            final, solution, method = response_parts(q, a)
        if key in manual_choices:
            final, solution, method = manual_choices[key], "", "原PDF右侧答案字母人工读取"
        if key in manual_fills:
            final, solution, method = manual_fills[key], "", "原PDF填空答案人工读取"
        if correction:
            final = correction["final_answer"]
            solution = correction.get("solution", solution)
            method = "用户授权的原页核对/数学校正，详见corrections.json"
        if not final:
            reasons.append("原材料最终答案为空或未能可靠提取")
        text = re.sub(r"^\(本题满分\s*\d+\s*分\)\s*", "", q["text"])
        text = re.sub(r"\n*绝密\s*[★*]?\s*启用前\s*$", "", text).strip()
        if correction:
            text = correction.get("question_text", text)
        options = []
        if q["kind"] == "选择题":
            if correction and "options" in correction:
                # The original full text may still include its options.
                if "question_text" not in correction:
                    parsed_text, _, _ = split_options(text)
                    first_label = re.search(r"\(\s*A\s*\)|(?<![A-Za-z\\])A\.\s*", text)
                    text = parsed_text if parsed_text != text else text[:first_label.start()] if first_label else text
                options, error = correction["options"], None
            else:
                text, options, error = split_options(text)
            if error:
                reasons.append(error)
            if key in GRAPHIC_OPTIONS:
                for option, image_index in zip(options, GRAPHIC_OPTIONS[key]):
                    option["text"] = f"见题图第{image_index}张（选项{option['label']}）。"
        if not correction and key in {(1987, 4, 0), (1987, 6, 0)}:
            reasons.append("原解析存在公式错误或与题干的指数不一致，需数学复核")
        if not correction and key in {(1987, 1, 1), (1988, 2, 2), (1988, 5, 0)}:
            reasons.append("已核对原页，原材料答案存在数学错误，不能直接采用")
        if not correction and year == 1997:
            reasons.append("该年题干存在多处公式及文字识别异常，需逐题核对原页")
        if not correction and year == 2022:
            reasons.append("该年原稿及识别结果存在重复选项/公式异常，需逐题核对原页")
        if not correction and key == (2013, 2, 14):
            reasons.append("原解析中的条件概率公式识别为乱码，需核对原页")
        if any("\ufffd" in s for s in [text, final, solution]):
            reasons.append("识别结果含替换字符")
        kind = q["kind"]
        if kind == "解答题" and "证明" in text and not re.search(r"求|计算", text):
            kind = "证明题"
        record = {"id": record_id, "source": "university_exam",
                  "question": {"text": text, "images": [figure_path(u) for u in q["items"] if u["type"] in {"image", "chart"}], "options": options},
                  "answer": {"final_answer": final, "solution": solution},
                  "metadata": {"paper_name": f"{year}年全国硕士研究生招生考试数学一" + ("（试卷Ⅰ）" if year <= 1996 else ""),
                               "question_type": kind}}
        item = {"id": record_id, "key": key, "question_pages": sorted({u["page"] for u in q["items"]}),
                "answer_pages": sorted({u["page"] for u in a["items"]}) if a else [],
                "answer_extraction": method, "review_status": "needs_mathematical_review",
                "reasons": reasons}
        audit.append(item)
        if correction:
            item["review_status"] = correction["review_status"]
            correction_log.append({"id": record_id,
                "question_pdf_pages": item["question_pages"], "annual_answer_pdf_pages": item["answer_pages"],
                "original_question_ocr": q["text"], "original_answer_ocr": a["text"] if a else "",
                "corrected_record": record, **correction})
        if reasons:
            pending.append({"record": record, "issues": reasons})
        else:
            records.append(record)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "questions.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    (OUT / "pending_review.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in pending), encoding="utf-8")
    save(WORK / "record_audit.json", audit)
    save(OUT / "corrections.json", correction_log)
    source_root = next(BASE.parent.glob("考研*/【1】*/01-*"))
    jobs = {}
    used_figures = {path for r in records for path in r['question']['images']}
    for r in records:
        used_figures.update(re.findall(r'!\[[^\]]*\]\(([^)]+)\)', r['answer']['solution']))
    for u in [u for q in questions for u in q["items"]] + [u for a in answers.values() for u in a["items"]]:
        if u["type"] not in {"image", "chart"}:
            continue
        name = figure_path(u)
        if name not in used_figures:
            continue
        source = next(source_root.glob("【合集】*.pdf")) if u["source_name"] == "questions_all" else source_root / "答案解析" / (u["source_name"][-4:] + "考研数一真题解析.pdf")
        jobs[name] = {"target": str(BASE / name), "source": str(source),
                      "page": u["page"], "bbox": u["bbox"], "page_size": u["page_size"]}
    save(WORK / "figure_jobs.json", list(jobs.values()))
    summary = {"status": "converted_requires_mathematical_review", "candidate_count": len(questions),
               "imported_count": len(records), "pending_count": len(pending),
               "empty_solution_count": sum(not r["answer"]["solution"] for r in records),
               "manually_rechecked_or_corrected_count": len(correction_log),
               "question_pages": 127, "annual_answer_pages": 442,
               "by_year": {str(y): {"candidates": sum(q["key"][0] == y for q in questions),
                                      "imported": sum(f"_{y}_" in r["id"] for r in records)} for y in range(1987,2024)},
               "question_types": dict(Counter(r["metadata"]["question_type"] for r in records)),
               "graphic_option_mappings": {f"kaoyan_math1_{y}_{m:02d}_{n:02d}": dict(zip("ABCD", order)) for (y,m,n),order in GRAPHIC_OPTIONS.items()},
               "limitations": ["已完成格式和题号校验；54条有明确问题的记录已原页核对/校正，其余记录未全部逐题数学复核", "解答题未能分离简短结论时，final_answer保留原材料的完整解答", "校正内容属于用户授权的编辑修订，不声称是官方解答；详见corrections.json", "2022年第2题已由用户人工修正C/D选项，最终答案B；已同步至可复现校正配置", "3道图形选项以question.images的一基图片序号对应A/B/C/D，映射见graphic_option_mappings", "1987—1996试卷二不收录", "已依据2010年度解析将合集第111页归入2010年21—23题"]}
    save(OUT / "conversion_report.json", summary)
    print(json.dumps({k:v for k,v in summary.items() if k not in {"by_year", "limitations"}}, ensure_ascii=False))
    return records, pending, audit


def main():
    questions, exclusions = make_questions()
    answers = {}
    for year in range(1987, 2024):
        answers.update(make_answers(year))
    save(WORK / "question_segments.json", questions)
    save(WORK / "answer_segments.json", [{"key": k, **v} for k, v in answers.items()])
    save(WORK / "exclusions.json", exclusions)
    publish(questions, answers, exclusions)


if __name__ == "__main__":
    main()
