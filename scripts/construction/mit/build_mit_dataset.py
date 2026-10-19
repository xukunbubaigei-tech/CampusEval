"""Publish the first checked MIT OCW exam batch in the existing core schema.

The curated modules are transcriptions and edited/condensed source solutions,
not newly generated substitutes for missing solutions. Downloaded source PDFs
and their checksums are retained to permit independent review.
"""
import hashlib
import json
import re
import runpy
import shutil
from collections import Counter
from pathlib import Path

import pymupdf as fitz
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'datasets/MIT'
SCRIPT = ROOT / 'scripts'
RAW = ROOT / 'workspace/extracted/MIT'

SPECS = {
 'single': ('1801sc','mit18_01scf10_final','mit18_01scf10_finalsol','MIT OCW 18.01SC Single Variable Calculus - Final Exam','高等数学'),
 'multi': ('1802sc','mit18_02sc_finalexam','mit18_02sc_finalexamsol','MIT OCW 18.02SC Multivariable Calculus - Final Exam','高等数学'),
 'quiz1': ('1806','mit18_06s10_exam1_s10','mit18_06s10_exam1_s10_sol','MIT 18.06 Linear Algebra - Quiz 1 (Spring 2010)','线性代数'),
 'quiz2': ('1806','mit18_06s10_exam2_s10','mit18_06s10_exam2_s10_soln','MIT 18.06 Linear Algebra - Quiz 2 (Spring 2010)','线性代数'),
 'quiz3': ('1806','mit18_06s10_exam3_s10','mit18_06s10_exam3_s10_soln','MIT 18.06 Linear Algebra - Quiz 3 (Spring 2010)','线性代数'),
 'stats1': ('1805','mit18_05_s22_exam01_pdf','mit18_05_s22_exam01_sol_pdf','MIT 18.05 Introduction to Probability and Statistics - Exam 1 (Spring 2022)','概率论与数理统计'),
 'stats2': ('1805','mit18_05_s22_exam02_pdf','mit18_05_s22_exam02_sol_pdf','MIT 18.05 Introduction to Probability and Statistics - Exam 2 (Spring 2022)','概率论与数理统计'),
}


def write_json(path, obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def rid(key, number):
    code = {'single':'1801sc_f2010_final','multi':'1802sc_f2010_final',
            'quiz1':'1806_s2010_quiz1','quiz2':'1806_s2010_quiz2','quiz3':'1806_s2010_quiz3',
            'stats1':'1805_s2022_exam1','stats2':'1805_s2022_exam2'}[key]
    return f'mit_{code}_{number:02d}' if isinstance(number,int) else f'mit_{code}_{number.lower()}'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'questions.jsonl').exists() and len((OUT/'questions.jsonl').read_text(encoding='utf-8').splitlines())>52:
        raise RuntimeError('The MIT dataset contains appended batches. Use extend_mit_dataset.py; refusing to overwrite them with the first batch.')
    all_sources=json.loads((OUT/'source_manifest.json').read_text(encoding='utf-8'))
    by_slug={s['resource_url'].rstrip('/').split('/')[-1]:s for s in all_sources}
    calculus=runpy.run_path(str(SCRIPT/'curation/mit/mit_curated_calculus.py'))
    others=runpy.run_path(str(SCRIPT/'curation/mit/mit_curated_algebra_stats.py'))
    groups={'single':calculus['SINGLE'],'multi':calculus['MULTI'],**others['ALGEBRA'],
            'stats1':others['STATS1'],'stats2':others['STATS2']}
    sources=[]
    mappings=[]
    records=[]
    for key,entries in groups.items():
        course,qslug,sslug,title,subject=SPECS[key]
        qsource=by_slug[qslug]; ssource=by_slug[sslug]
        for src in [qsource,ssource]:
            saved={**src}
            target=OUT/'sources'/course/Path(src['local_pdf']).name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/src['local_pdf'],target)
            saved['local_pdf']=target.relative_to(OUT).as_posix()
            if saved not in sources:sources.append(saved)
        for number,question,final,solution,qpages,spages in entries:
            # Question papers leave working space: their pagination differs
            # substantially from the compact solution PDFs.
            if key=='quiz2':qpages={1:[1],2:[2],3:[3]}[number]
            if key=='stats1':qpages={2:[3],3:[4],4:[5],5:[6,7],6:[8]}[number]
            if key=='stats2':qpages={'I_1':[2],'I_2':[3],'I_4':[4],'I_5':[5],
                'II_1':[6],'II_2':[7],'II_3':[8],'II_4':[9],'II_5':[10]}[number]
            ident=rid(key,number)
            options=[]
            qtype='证明题' if (key,number) in [('single',15),('quiz3',2)] else '解答题'
            if key=='stats2' and number=='I_4':
                options=[{'label':'A','text':r'$\operatorname{Uniform}([0,0.5])$'},
                         {'label':'B','text':r'$\operatorname{Beta}(2,2)$'},
                         {'label':'C','text':r'$N(0.5,0.25)$'}]
                qtype='选择题'
            records.append({'id':ident,'source':'university_exam',
                'question':{'text':question,'images':[],'options':options},
                'answer':{'final_answer':final,'solution':solution},
                'metadata':{'paper_name':title,'question_type':qtype}})
            mappings.append({'id':ident,'course':course,'subject':'线性代数' if key=='multi' and number==3 else subject,
                'source_question_number':number,'question_pdf':f'sources/{course}/{Path(qsource["local_pdf"]).name}',
                'solution_pdf':f'sources/{course}/{Path(ssource["local_pdf"]).name}',
                'question_pdf_pages':qpages,'solution_pdf_pages':spages})

    # Retain original solution figures, without leaking any solution into question.images.
    figures=[('single',4,3,0),('single',5,4,0),('single',10,7,0),('single',11,9,0),
             ('multi',9,4,0),('multi',11,4,1),('multi',12,5,0),('multi',13,6,0),
             ('multi',14,6,1),('multi',15,7,0)]
    assets=[]
    for key,number,page,index in figures:
        source=by_slug[SPECS[key][2]]
        doc=fitz.open(ROOT/source['local_pdf'])
        pdfpage=doc[page-1]
        xref=pdfpage.get_images()[index][0]
        rect=pdfpage.get_image_rects(xref)[0]
        name=f'{rid(key,number)}_solution.png'
        path=ROOT/'data/images/MIT'/name
        path.parent.mkdir(parents=True,exist_ok=True)
        pdfpage.get_pixmap(matrix=fitz.Matrix(2,2),clip=rect,alpha=False).save(path)
        relative=path.relative_to(ROOT).as_posix()
        next(r for r in records if r['id']==rid(key,number))['answer']['solution']+=f'\n\n![Source solution figure]({relative})'
        assets.append({'id':rid(key,number),'file':relative,'source_pdf_page':page,'source_pdf_url':source['pdf_url']})

    corrections=[
      ('single',2,'原解答隐式求导中的 x3y² 容易误读；统一为 3xy²，并以原题方程求导核对。'),
      ('single',4,'原解答用横坐标列拐点；整理为完整坐标，并列出原图对应的导数，未改变原题。'),
      ('single',13,'原解答按正向时间给 t0；补明 t0≥0，负向区间弧长为 |t0|，未改题干。'),
      ('single',14,'原解答比值测试中系数比写反，且将区间称为半径；修正为逐项比值极限 |x| 与半径1。保留其有效但较松的误差界1/3，同时说明更紧界1/24。'),
      ('multi',1,'原解答中间平面等式和法向点积有排版/符号笔误；叉积为(0,6,4)，平面3y+2z=7；所选单位向量点积为-3/√84，方向反选则变号。'),
      ('multi',4,'原解答 T 的文字层可能丢失负号，T′ 的一处中间式漏链式因子 e^t；按 r(t) 逐项求导。'),
      ('multi',6,'原解答 fxx 的分母 x²y 应为 x³y；在临界点的原结论和Hessian数值不变。'),
      ('multi',8,'原解答只列链式法则三个坐标导数，未写最终和；整理原步骤得1-2+2√2=2√2-1。'),
      ('multi',13,'原解答路径积分公式第三段将R误写Q，终点势函数数值一行顺序混乱；保留势函数并明确3-10=-7。'),
      ('multi',14,'原解答半角公式漏2θ；整理使用正确的cos²θ=(1+cos2θ)/2，通量仍为4π。'),
      ('multi',15,'原解答将三段曲线编号与题干顺序混用并在总和重复C2；改按所在坐标平面说明各段，保留正向取向与4-4+0=0。'),
      ('quiz2',1,'原解答零空间平面漏 z 的系数3；改为2x+y+3z=0，与a=(2,1,3)及所列基向量一致；特征向量明确排除零向量。'),
      ('quiz2',2,'原解答将列相关时投影不唯一与系数不唯一混淆：投影p唯一，系数可不唯一。对固定误差e，所有垂直向量构成e⊥；C(A)垂直于每个可能的误差，不能对固定e声称二者恒相等。'),
      ('quiz2',3,'原解答一处写特征向量分量和为1，应为0；按A3v=v及点积核验。'),
      ('quiz3',1,'原解答H²中间乘积有多余u、HTH=1应为I；按(u uT)²=u uT核验。'),
      ('quiz3',3,'原解答SVD列关系写作A u_j=σ_j v_j，应为A v_j=σ_j u_j；保留其正确的U、Σ、V并乘回复核。'),
      ('stats1',6,'原解答一行总方差写10^5，与其σ=1000矛盾；20×5×10^4=10^6，原正态近似结果0.3085不变。'),
      ('stats2','I_1','原题(d)的average weight有语义歧义；按原解答的总体均值/未知参数含义解释，并在答案明确该解释，未把此解释冒充无条件结论。'),
      ('stats2','II_5','题干用allele frequencies，但观测表是基因型分类频数；保留原表，以两类基因型的同质性检验表达，原统计量6.25不变。'),
    ]
    edits=[{'id':rid(k,n),'basis':basis,'status':'editorial_correction_or_clarification',
            'solution_origin':'Edited from MIT OCW published solution; not a verbatim official solution'} for k,n,basis in corrections]
    deferred=[
      {'course':'1801sc','question':'Final 6','reason':'飞机与汽车的相对运动方向在题干中不够明确；原解析有符号和近似问题，暂不发布。'},
      {'course':'1802sc','question':'Final 2','reason':'原题点P、平面P、P0等符号的文字层丢失区别；尚需逐符号完成转写，不发布残损题干。'},
      {'course':'1805','question':'Exam 1, Problem 1','reason':'包含必要概率密度图，首批尚未完成题图裁切与关联。'},
      {'course':'1805','question':'Exam 2, I.3','reason':'包含必要的两个功效比较图，首批尚未完成题图裁切与关联。'},
    ]
    report={'batch':'MIT OCW first checked exam batch','date':'2026-10-19',
      'record_count':len(records),'by_course':dict(Counter(m['course'] for m in mappings)),
      'by_subject':dict(Counter(m['subject'] for m in mappings)),
      'language':'en','empty_solutions':0,'source_pdf_count':len(sources),
      'source_pdf_pages':sum(s['pages'] for s in sources),'solution_figure_count':len(assets),
      'editorial_correction_or_clarification_count':len(edits),'records':mappings,
      'figures':assets,'deferred_selected_exam_questions':deferred,
      'scope':'Seven selected exams, not all MIT course materials. Practice and final exams from other downloaded resources remain unconverted.',
      'method':'PDF text-layer extraction plus visual source-page review and manually structured English/LaTeX. MinerU upload was attempted but not successful and was not used as extraction input.',
      'solution_policy':'Existing published solutions edited and condensed; grading rubrics and administrative directions removed; main arguments and all requested subparts retained. No solution fabricated for a source without one.',
      'license':'CC BY-NC-SA 4.0 per MIT OCW current course footer; retain individual resource notices.',
      'license_url':'https://creativecommons.org/licenses/by-nc-sa/4.0/',
      'limitations':['已核对所收录题目的题答与原页；尚无第二位独立审校者逐题签核。',
                     '数学检验只覆盖validation_report列明的内容，不等于自动证明每条解析全部正确。',
                     '尚未合并main、mini或修改训练/评测划分。']}
    schema=json.loads((ROOT/'schemas/dataset.schema.json').read_text(encoding='utf-8'))
    validator=Draft202012Validator(schema)
    ids=set(); texts=set();errors=[]
    for record in records:
        for error in validator.iter_errors(record):errors.append(f'{record["id"]}: {error.message}')
        if not record['answer']['solution'].strip():errors.append('empty solution '+record['id'])
        if record['id'] in ids:errors.append('duplicate ID '+record['id'])
        ids.add(record['id'])
        text=re.sub(r'\s+','',record['question']['text']).lower()
        if text in texts:errors.append('duplicate question '+record['id'])
        texts.add(text)
        for value in [record['question']['text'],record['answer']['final_answer'],record['answer']['solution']]+[o['text'] for o in record['question']['options']]:
            if value.count('$')%2:errors.append('unbalanced math dollars '+record['id'])
            if value.count('{')!=value.count('}'):errors.append('unbalanced braces '+record['id'])
            if '\ufffd' in value:errors.append('replacement character '+record['id'])
        if record['metadata']['question_type']=='选择题' and record['answer']['final_answer'] not in [o['label'] for o in record['question']['options']]:errors.append('invalid choice answer '+record['id'])
        for ref in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',record['answer']['solution']):
            if not (ROOT/ref).is_file():errors.append('missing figure '+ref)
    # Exact normalized-text overlap against existing published datasets.
    overlaps=[]
    for folder in [ROOT/'datasets/main',ROOT/'datasets/kaoyan']:
        for path in folder.glob('*.jsonl'):
            for line in path.read_text(encoding='utf-8').splitlines():
                if not line.strip():continue
                old=json.loads(line)
                if not isinstance(old,dict) or not isinstance(old.get('question'),dict):continue
                if re.sub(r'\s+','',old['question'].get('text','')).lower() in texts:overlaps.append(old.get('id'))
    if overlaps:errors.append('existing exact-text overlap: '+str(overlaps))
    raw=''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in records)
    validation={'passed':not errors,'records':len(records),'errors':errors,
        'checks':['existing JSON Schema','unique IDs and exact normalized-text deduplication',
                  'exact normalized-text overlap against main and kaoyan','nonempty original-based solutions',
                  'choice label agreement','math dollar and brace balance','local figure references'],
        'questions_sha256':hashlib.sha256(raw.encode('utf-8')).hexdigest()}
    if errors:raise ValueError(errors)
    # Publish only after all record and asset checks pass.
    (OUT/'questions.jsonl').write_bytes(raw.encode('utf-8'))
    write_json(OUT/'conversion_report.json',report)
    write_json(OUT/'validation_report.json',validation)
    write_json(OUT/'editorial_changes.json',edits)
    write_json(OUT/'published_sources.json',sources)
    (OUT/'conversion_report.md').write_text(f'''# MIT 首批收录报告

日期：2026-10-19。收录{len(records)}道英文大学数学题，来自7份考试、14份题答PDF；保留原大题编号及全部小问，未通过拆小问增加样本。

| 课程 | 收录题数 |
|---|---:|
'''+''.join(f'| {course} | {count} |\n' for course,count in report['by_course'].items())+f'''
主学科分布：高等数学27题、线性代数11题、概率论与数理统计14题。18.02SC中的矩阵题按主考查内容计入线代。

提取与核对：PDF文字层提取后对照原页整理英文及LaTeX，题干、最终答案、配套解析分别保存。原解析有压缩和明确记录的勘误，并非原文逐字复制。没有使用模型从零生成缺失解析。MinerU上传未成功，本批未采用MinerU结果。

已通过既有Schema、ID、规范化题干精确去重、与main/kaoyan的精确重复检查、选择题答案、公式分隔符、图片引用校验。数学校验的具体条目见mathematical_checks.json，不将结构通过等同于数学完全正确。

## 暂缓收录

'''+''.join(f'- {item["course"]} {item["question"]}：{item["reason"]}\n' for item in deferred)+f'''
其他已下载的练习卷、期末卷和课程作业尚未全部转换，下载候选量不计入正式题数。本批不代表MIT课程全量收录。

## 可追溯材料

- questions.jsonl：正式{len(records)}条记录。
- published_sources.json及sources/：本批题答原文件、官方链接、页数、SHA-256。
- conversion_report.json：每条记录对应的题目/解析文件、原题号、原PDF页码及{len(assets)}张原图出处。
- editorial_changes.json：{len(edits)}条编辑修订或澄清依据。
- validation_report.json和mathematical_checks.json：校验实际范围及结果。
- README.md：材料署名、许可条件、整理方式及限制。

main、mini、kaoyan与既有训练/评测划分未更改。精确文本去重不覆盖所有跨语言或数学等价变体。
''',encoding='utf-8')
    (OUT/'README.md').write_text(f'''# MIT English university mathematics: first batch

首批 **{len(records)} 条英文题目**，取自MIT OCW的7份考试材料，每题均有原材料配套解析。按原卷大题计数，所有小问整体保留。本批不是MIT课程全量。

| 主学科 | 条数 |
|---|---:|
'''+''.join(f'| {s} | {n} |\n' for s,n in report['by_subject'].items())+f'''
课程分布：{json.dumps(report['by_course'],ensure_ascii=False)}。

- `questions.jsonl`：沿用id、source、question、answer、metadata五个顶层字段；本批均为真实考试题，source为university_exam。
- `sources/`：本批{len(sources)}份官方题答PDF，保留原始内容。
- `published_sources.json`：材料级来源URL、文件路径、页数及SHA-256；下载全集候选清单为source_manifest.json。
- `data/images/MIT/`：{len(assets)}张原解答图，通过answer.solution中的相对Markdown链接引用，不泄露到question.images。
- `conversion_report.json`：课程、主学科、原题号与PDF页码对应、暂缓收录项及处理方法。
- `editorial_changes.json`：{len(edits)}条勘误或解释性澄清的依据。
- `validation_report.json`：结构校验结果与数据校验和；`mathematical_checks.json`另列实际执行的数学校验。

题干保持英文，公式规范为LaTeX；原解答经整理与压缩，去掉评分rubric、行政说明和重复叙述，保留各小问的主要推理。不是原解答逐字复制。已有解答的笔误修复单独披露，不冒充原版官方文字。

提取方式为PDF文字层、原页视觉核对和人工结构化；MinerU网页上传未成功，本批未采用其识别结果。未改动main、mini、kaoyan或已有训练/评测划分。与现有题库完成规范化文本精确去重；跨语言和数学等价题仍需后续审查。

## Attribution and license

Source: Massachusetts Institute of Technology, MIT OpenCourseWare. Courses: 18.01SC Single Variable Calculus (Fall 2010, David Jerison), 18.02SC Multivariable Calculus (Fall 2010, Denis Auroux), 18.06 Linear Algebra (Spring 2010, Gilbert Strang), and 18.05 Introduction to Probability and Statistics (Spring 2022, Jeremy Orloff and Jennifer French Kamrin). See the exact source URLs in published_sources.json and original resource notices. The 18.01SC content development team also credits Arthur Mattuck, Haynes Miller, Benjamin Brubaker, Jeremy Orloff, Heidi Burgiel, Christine Breiner, David Jordan and Joel Lewis.

本子目录中的课程内容及其整理版本按MIT OCW当前课程页标注的[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)保留署名、非商业及相同方式共享条件；不将该内容改标为本仓库代码许可证。转换修改包括分题、英文转写、LaTeX整理、解答压缩、图像裁出与明确披露的勘误。MIT不为本数据整理工作背书。

已核对所收录题目的原页与解答，但尚无第二位独立审校者逐题签核；结构校验通过不等于所有数学推理得到机器证明。
''',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['record_count','by_course','by_subject','source_pdf_count','solution_figure_count']},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
