"""Append a reviewed second MIT batch, preserving existing core records.

Run after build_mit_dataset.py. Re-running preserves any existing manual edits.
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

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'datasets/MIT'
SCRIPTS=ROOT/'scripts'
RAW=ROOT/'workspace/extracted/MIT'


def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def write(name,value):(OUT/name).write_bytes((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))


def source_pages(path,number):
    """Find a numbered problem span across original PDF pages, not OCR page counters."""
    doc=fitz.open(path)
    full=''; offsets=[]
    for page in doc:
        offsets.append((len(full),len(full)+len(page.get_text())))
        full+=page.get_text()+'\n'
    if isinstance(number,str) and number.startswith('concept'):
        target='Concept '+number[7:]+'.'
    else:target='Problem '+str(number).replace('_','.')+'.'
    match=re.search(re.escape(target),full)
    if not match:raise ValueError(f'Missing heading {target}: {path}')
    next_head=re.search(r'(?:Problem\s+(?:[IV]+\.)?\d+\.|Concept\s+\d+\.)',full[match.end():])
    end=match.end()+next_head.start() if next_head else len(full)
    # Exclude blank working pages, administrative appendices and tables after
    # the last question; curated explicit overrides cover those cases.
    return [i+1 for i,(a,b) in enumerate(offsets) if b>match.start() and a<end]


def main():
    before=(OUT/'questions.jsonl').read_bytes()
    existing=[json.loads(line) for line in before.decode('utf-8').splitlines() if line.strip()]
    old_by_id={r['id']:r for r in existing}
    # Complete the core MCQ mapping for the newly transcribed five-choice item.
    # Only migrate our exact unedited conversion; never replace user edits.
    concept_id='mit_1805_s2022_final_concept16'
    if concept_id in old_by_id and old_by_id[concept_id]['metadata']['question_type']=='解答题':
        ref=next(i for i in runpy.run_path(str(SCRIPTS/'curation/mit/mit_batch2_final_statistics.py'))['ITEMS'] if i[0]=='concept16')
        item=old_by_id[concept_id]
        if item['question']['text']==ref[1] and item['answer']=={'final_answer':ref[2],'solution':ref[3]}:
            format_concept_choice(item)
    backup=ROOT/'workspace/review/MIT/backups'/f'questions_{hashlib.sha256(before).hexdigest()}.jsonl'
    backup.parent.mkdir(parents=True,exist_ok=True)
    if not backup.exists():backup.write_bytes(before)
    # Long-list 71 is the same bare iid-sum CLT template as 69, with only
    # numerical parameters changed. Keep 69; retain 71 outside published data.
    duplicate_id='mit_1805_s2022_practice1_all_71'
    if duplicate_id in old_by_id:
        reference=next(item for item in runpy.run_path(str(SCRIPTS/'curation/mit/mit_batch2_probability.py'))['ITEMS'] if item[0]==71)
        duplicate=old_by_id[duplicate_id]
        if duplicate['question']['text']!=reference[1] or duplicate['answer']!={'final_answer':reference[2],'solution':reference[3]}:
            raise ValueError('The duplicate candidate has manual changes; refusing to remove them.')
        write('excluded_duplicates.json',[{'record':duplicate,'canonical_id':'mit_1805_s2022_practice1_all_69',
            'reason':'Same bare iid-sum CLT task with only mean, variance, n and threshold changed.'}])
        existing=[r for r in existing if r['id']!=duplicate_id]
        old_by_id.pop(duplicate_id)
    report=read('conversion_report.json')
    mappings={r['id']:r for r in report['records']}
    mappings.pop(duplicate_id,None)
    sources=read('published_sources.json')
    manifest={s['resource_url'].rstrip('/').split('/')[-1]:s for s in read('source_manifest.json')}
    edits=read('editorial_changes.json')
    figures=report['figures']
    records=list(existing)
    records_by_id={r['id']:r for r in records}
    new_ids=[]
    p=runpy.run_path(str(SCRIPTS/'curation/mit/mit_batch2_probability.py'))['ITEMS']
    p=[item for item in p if item[0]!=71]
    st=runpy.run_path(str(SCRIPTS/'curation/mit/mit_batch2_statistics.py'))['ITEMS']
    ca=runpy.run_path(str(SCRIPTS/'curation/mit/mit_batch2_calculus_algebra.py'))
    final=runpy.run_path(str(SCRIPTS/'curation/mit/mit_batch2_final_statistics.py'))['ITEMS']
    groups={
      'probpractice':('1805','mit18_05_s22_prac_exam01_all_pdf','mit18_05_s22_prac_exam01_all_sol_pdf','mit_1805_s2022_practice1_all','MIT 18.05 - Exam 1 Practice: Long List (Spring 2022)','概率论与数理统计',p),
      'statpractice':('1805','mit18_05_s22_prac_exam02a_pdf','mit18_05_s22_prac_exam02a_sol_pdf','mit_1805_s2022_practice2a','MIT 18.05 - Exam 2 Practice Questions (Spring 2022)','概率论与数理统计',st),
      'multipractice':('1802sc','mit18_02sc_pracfinal','mit18_02sc_pracfinalsol','mit_1802sc_f2010_practicefinal','MIT OCW 18.02SC - Practice Final Exam','高等数学',ca['MULTI']),
      'linearfinal':('1806','mit18_06s10_final_exam','mit18_06s10_final_answers','mit_1806_s2010_final','MIT 18.06 - Final Exam (Spring 2010)','线性代数',ca['LINEAR']),
      'statfinal':('1805','mit18_05_s22_exam_final_pdf','mit18_05_s22_exam_final_sol_pdf','mit_1805_s2022_final','MIT 18.05 - Final Exam (Spring 2022)','概率论与数理统计',final),
    }
    base=runpy.run_path(str(SCRIPTS/'construction/mit/build_mit_dataset.py'))
    for key,n,q,a,sol in ca['RESOLVED']:
        course,qs,ss,title,subject=base['SPECS'][key]
        ident=base['rid'](key,n)
        groups['resolved_'+key]=(course,qs,ss,ident.rsplit('_',1)[0],title,subject,[(n,q,a,sol)])

    def save_source(slug):
        src=manifest[slug]
        path=OUT/'sources'/src['course']/Path(src['local_pdf']).name
        path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists():shutil.copyfile(ROOT/src['local_pdf'],path)
        item={**src,'local_pdf':path.relative_to(OUT).as_posix()}
        if not any(s['resource_url']==src['resource_url'] for s in sources):sources.append(item)
        return item

    identities={}
    for key,(course,qslug,sslug,prefix,title,subject,items) in groups.items():
        qsrc=save_source(qslug);ssrc=save_source(sslug)
        for number,question,answer,solution in items:
            if key.startswith('resolved_'):
                ident=base['rid'](key[9:],number)
            else:ident=f'{prefix}_{number:02d}' if isinstance(number,int) else f'{prefix}_{number}'
            identities[(key,number)]=ident
            if ident in old_by_id:continue
            if key=='linearfinal':
                qpages=[number]
                spages={2:[3],3:[4],4:[5,6],5:[7],6:[8,9],7:[10],8:[11]}[number]
            elif number=='15_16':
                qpages=sorted(set(source_pages(OUT/qsrc['local_pdf'],15)+source_pages(OUT/qsrc['local_pdf'],16)))
                spages=sorted(set(source_pages(OUT/ssrc['local_pdf'],15)+source_pages(OUT/ssrc['local_pdf'],16)))
            else:
                qpages=source_pages(OUT/qsrc['local_pdf'],number)
                spages=source_pages(OUT/ssrc['local_pdf'],number)
            if key=='statfinal' and number==13:qpages=[18];spages=[14]
            record={'id':ident,'source':'university_exam',
                'question':{'text':question,'images':[],'options':[]},
                'answer':{'final_answer':answer,'solution':solution},
                'metadata':{'paper_name':title,'question_type':'证明题' if (key,number) in [('probpractice',50),('probpractice',59),('probpractice',60),('linearfinal',8)] else '解答题'}}
            if key=='statfinal' and number=='concept16':format_concept_choice(record)
            records.append(record);records_by_id[ident]=record;new_ids.append(ident)
            mappings[ident]={'id':ident,'course':course,'subject':'线性代数' if key=='multipractice' and number==2 else subject,
                'source_question_number':number,'question_pdf':qsrc['local_pdf'],'solution_pdf':ssrc['local_pdf'],
                'question_pdf_pages':qpages,'solution_pdf_pages':spages,'batch':'2026-10-19-MIT-02'}

    def figure(key,n,role,page,clip=None,image_index=None,vector=False):
        ident=identities[(key,n)]
        if ident in old_by_id:return
        mapping=mappings[ident]
        path=OUT/mapping['question_pdf' if role=='question' else 'solution_pdf']
        doc=fitz.open(path);pdfpage=doc[page-1]
        if image_index is not None:
            xref=pdfpage.get_images()[image_index][0];clip=pdfpage.get_image_rects(xref)[0]
        if vector:
            rects=[d['rect'] for d in pdfpage.get_drawings() if d['rect'].width>1 or d['rect'].height>1]
            if not rects:raise ValueError('No figure drawings '+str(path))
            clip=fitz.Rect(rects[0])
            for rect in rects[1:]:clip|=rect
            clip=fitz.Rect(clip.x0-25,clip.y0-25,clip.x1+25,clip.y1+25)&pdfpage.rect
        filename=f'data/images/MIT/{ident}_{role}.png'
        (ROOT/filename).parent.mkdir(parents=True,exist_ok=True)
        pdfpage.get_pixmap(matrix=fitz.Matrix(2,2),clip=fitz.Rect(clip),alpha=False).save(ROOT/filename)
        if role=='question':records_by_id[ident]['question']['images'].append(filename)
        else:records_by_id[ident]['answer']['solution']+=f'\n\n![Source solution figure]({filename})'
        figures.append({'id':ident,'file':filename,'role':role,'source_pdf_page':page,'source_pdf':mapping['question_pdf' if role=='question' else 'solution_pdf']})

    figure('resolved_multi',2,'solution',1,image_index=0)
    figure('resolved_stats1',1,'question',2,clip=(155,125,415,243))
    figure('resolved_stats2','I_3','question',4,clip=(65,135,540,210))
    # Explicit graph-only crops: formula glyph outlines and update-table rules
    # are also PDF drawings and must not expand the crop into other questions.
    for n,page,clip in [(14,10,(170,130,405,310)),(17,12,(135,440,435,555)),(18,13,(130,245,440,355))]:
        figure('statpractice',n,'solution',page,clip=clip)
    figure('statfinal',12,'solution',14,clip=(180,100,430,315))

    # Keep editorial provenance outside the core question shown to the model.
    for key,n,remove in [
      ('multipractice',6,' This uses the surface in the published solution; the question sheet repeats $z^2$ where $x^2$ is intended.'),
      ('multipractice',7,' This uses the plane from the published solution; the question sheet misprints the first variable as $z$.'),
      ('multipractice',9,' The variable and lower limit are transcribed from the matching published solution because the question sheet contains inconsistent symbols.'),
      ('multipractice',13,' The first differential is taken as $dx$, consistently with the published solution.'),
      ('multipractice','15_16',' These two consecutive questions sharing the same data are retained as one record.')]:
        ident=identities[(key,n)]
        if ident not in old_by_id:records_by_id[ident]['question']['text']=records_by_id[ident]['question']['text'].replace(remove,'').replace(' (original Problem 15)','').replace(' (original Problem 16)','')

    edit_specs=[
      ('probpractice',32,'非负随机变量最终赌注的期望是扩展值+∞；修正原解答把它称为undefined的表述，不保留其混用St Petersburg名称的断言。'),
      ('probpractice',37,'原解答均值计算末项12×6应为12×0.6；最终8.4不变。'),
      ('probpractice',49,'原解答总方差一行将Var(X_j²)误写Var(X_j)；以Var(X_j²)=2核验总方差200。'),
      ('probpractice',50,'原解答密度链式法则一处写成1/[aφ]；修正为φ((y-b)/a)/a。'),
      ('probpractice',52,'原解答第二种方法中的标准均匀U误写U(a,b)；改为U(0,1)。'),
      ('probpractice',59,'原解答tY的中心化一行系数误写s，统一为t。'),
      ('probpractice',66,'原解答标准差根号范围易误读，明确为√(1/2)，相关系数1/2不变。'),
      ('probpractice',67,'原解答标准差根号范围易误读，明确为√(3/4)，相关系数1/3不变。'),
      ('probpractice',72,'原解答0.239751与精确值0.2765539不可能精确到两位小数；保留无连续修正结果并明确该断言错误，另列连续修正近似0.273906。'),
      ('probpractice',73,'总体仅给均值方差不能精确确定样本均值极端尾部概率；明确原解答为正态近似，且不能声称极端尾部具有CLT误差保证。'),
      ('probpractice',74,'原解答最终双重求和索引对应L<S而文字称L>S，已改为s<l；明确独立、等概率出生等原解答使用的模型假设。'),
      ('statpractice',1,'原解答用粗插值给1.275，保留粗值说明并提供标准分位数1.28155，不把粗值当精确边界。'),
      ('statpractice',2,'原题t临界值说明中p<0.5的比较号有笔误；用右尾定义与对称性明确问题，不改变数值任务。'),
      ('statpractice',3,'原解答χ²16在20的尾部0.25是粗插值；同时给约0.2202的数值值，明确近似精度。'),
      ('statpractice',5,'补充全部正面或全部反面时MLE位于参数区间端点。'),
      ('statpractice',7,'样本和为0时不存在有限率参数MLE，补明常规公式适用条件。'),
      ('statpractice',8,'全部几何观测为1时最优参数a=1，补明端点情形。'),
      ('statpractice',14,'原解答第二次更新一行遗漏系数4；采用同页更新表和归一化一致的4(1-θ)^3。'),
      ('statpractice',15,'原解答贝叶斯分子出现(1-θ)^14且归一化常数漏阶乘；以正确二项似然(1-θ)^4和证据积分表达。'),
      ('statpractice',18,'原解答双侧p<0.01错误；t=2.625、df48对应约0.011588，仍在0.05水平拒绝。'),
      ('multipractice',6,'题目PDF原页首项z²与末项2z²重复；匹配解答使用x²+2y²+2z²，并据梯度核验。此题为明确披露的题干校正版。'),
      ('multipractice',7,'题目PDF原页把2x误印2z；采用配套解答约束2x+y-z=6及核验点(2,1,-1)。此题为题干校正版。'),
      ('multipractice',9,'题目PDF积分混用x、z，内下限z³；采用配套解答清楚使用的x²≤y≤9、0≤x≤3。此题为题干校正版。'),
      ('multipractice',13,'题目PDF第一个微分显示/提取为dz而配套解答用dx；以原解答参数计算明确为(y-x)dx+(y-z)dz。此题为题干校正版。'),
      ('multipractice','15_16','原题16完全依赖15且要求同一通量的另一个方法；合并保留两种方法为一条，不重复计数。'),
      ('linearfinal',4,'原解答初值分解为两特征向量之差，但指数解误写加号；改为e^t(2,1)-e^-t(1,1)，代回初值核验。'),
      ('linearfinal',5,'原解答投影平面内两特征向量的特征值误写0；应为1，法向特征值才是0。原旋转有方向选择，明确沿题意i→j。'),
      ('linearfinal',7,'原解答将一般非正交平行多面体称box；整理为parallelepiped，其绝对行列式为体积。'),
      ('statfinal',5,'原解答假定所有观测至少1便能使对数和严格大于0不成立；补明全部恰为1时没有有限MLE。'),
      ('statfinal',9,'原解答sp²实际为均值差标准误平方而非单独的合并样本方差；分别明确50与100/11，并按未取粗略根号值计算p。'),
      ('statfinal',10,'原题样本数依赖置信区间约定；明确原解答400为最坏方差及临界值2的经验公式，385为同一最坏方差用1.96的结果。'),
      ('statfinal',11,'原解答将[-0.196,0.196]误称拒绝域；修正为接受/不拒绝区间，功效结果不变。'),
      ('statfinal',13,'原解答使用第25及475顺序统计量；题干明确最近秩经验分位数约定，避免软件插值定义导致不同区间。'),
    ]
    for key,n,basis in edit_specs:
        item={'id':identities[(key,n)],'basis':basis,'status':'editorial_correction_or_clarification',
              'solution_origin':'Edited from MIT OCW published solution; not a verbatim official solution','batch':'2026-10-19-MIT-02'}
        if not any(e['id']==item['id'] and e['basis']==basis for e in edits):edits.append(item)

    deferred=[item for item in report.get('deferred_selected_exam_questions',[]) if item['question'] not in ['Final 2','Exam 1, Problem 1','Exam 2, I.3']]
    more_deferred=[
      {'course':'1806','question':'Final 1 and 9','reason':'解析PDF相应页为图像，尚需完整转写；第9题原解答亦承认原KCL条件无解，暂不收录。'},
      {'course':'1802sc','question':'Practice Final 3','reason':'依赖胶带展开示意，首批后续仍需核对模型与图。'},
      {'course':'1802sc','question':'Practice Final 10','reason':'原题称半径1、中心(±2,0)/(0,±2)且端点(±1,±1)，几何条件不相容，暂不猜改。'},
      {'course':'1802sc','question':'Practice Final 17','reason':'任意闭曲线未保证在柱面上界出曲面；如xz截面圆心偏离z=0，原命题一般不成立，暂不补造条件。'},
      {'course':'1805','question':'Practice 2a 19','reason':'仅指向其他作业，无独立题干和自足解析。'},
      {'course':'1805','question':'Practice 2a 20','reason':'原卡方分组含期望数低于5，且率参数/代码有笔误；待明确分组合并方案。'},
      {'course':'1805','question':'Final 4','reason':'包含主观的愿意支付金额，没有唯一标准结论，暂不作为本批评测题。'},
      {'course':'1805','question':'Exam 1 long list 70','reason':'原赌博策略比较的论证不充分，尚需严格审校。'},
      {'course':'1805','question':'Exam 1 long list 71','reason':'与第69题同为纯参数替换的iid总和CLT模板，作为重复变体不另计；转换稿留在excluded_duplicates.json。'},
    ]
    for item in more_deferred:
        if item not in deferred:deferred.append(item)
    validation=validate(records,mappings,sources)
    # Existing records are protected byte-for-byte at their object level.
    assert all(records_by_id[k]==v for k,v in old_by_id.items())
    raw=''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in records).encode('utf-8')
    validation['questions_sha256']=hashlib.sha256(raw).hexdigest()
    validation['preserved_existing_records']=len(old_by_id)
    validation['new_records_this_run']=len(new_ids)
    if not validation['passed']:raise ValueError(validation['errors'])
    for item in sources:
        if hashlib.sha256((OUT/item['local_pdf']).read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Source checksum mismatch')
    report.update({'batch':'MIT OCW checked batches 1 and 2','record_count':len(records),
      'by_course':dict(Counter(m['course'] for m in mappings.values())),
      'by_subject':dict(Counter(m['subject'] for m in mappings.values())),
      'records':list(mappings.values()),'source_pdf_count':len(sources),'source_pdf_pages':sum(s['pages'] for s in sources),
      'solution_figure_count':sum(f.get('role','solution')=='solution' for f in figures),
      'question_figure_count':sum(f.get('role')=='question' for f in figures),
      'figures':figures,'editorial_correction_or_clarification_count':len(edits),
      'deferred_selected_exam_questions':deferred,
      'scope':'Two selected batches of exams and practice exams, not all MIT course materials.',
      'duplicate_policy':'The Exam 1 Long List is canonical; overlapping separate practice sheets are not counted again. Long-list 41 repeats the data/model of 26. Long-list 71 is the same bare CLT template as 69 with changed parameters and is not counted. Practice Final 15/16 form one combined record.',
      'batch2_record_ids':list(identities.values())})
    (OUT/'questions.jsonl').write_bytes(raw)
    write('published_sources.json',sources);write('editorial_changes.json',edits)
    write('conversion_report.json',report);write('validation_report.json',validation)
    write_reports(report)
    print(json.dumps({'added':len(new_ids),'total':len(records),'by_subject':report['by_subject'],'source_pdfs':len(sources),'figures':len(figures)},ensure_ascii=False,indent=2))


def validate(records,mappings,sources):
    validator=Draft202012Validator(json.loads((ROOT/'schemas/dataset.schema.json').read_text(encoding='utf-8')))
    errors=[];ids=set();texts=set()
    for r in records:
        errors.extend(f'{r["id"]}: {e.message}' for e in validator.iter_errors(r))
        if r['id'] in ids:errors.append('duplicate ID '+r['id'])
        ids.add(r['id'])
        normalized=re.sub(r'\s+','',r['question']['text']).lower()
        if normalized in texts:errors.append('duplicate text '+r['id'])
        texts.add(normalized)
        if not r['answer']['solution'].strip():errors.append('empty solution '+r['id'])
        if r['metadata']['question_type']=='选择题' and r['answer']['final_answer'] not in [o['label'] for o in r['question']['options']]:errors.append('choice label mismatch '+r['id'])
        vals=[r['question']['text'],r['answer']['final_answer'],r['answer']['solution']]+[o['text'] for o in r['question']['options']]
        for v in vals:
            if v.count('$')%2 or v.count('{')!=v.count('}'):errors.append('math delimiter '+r['id'])
            if '\ufffd' in v:errors.append('replacement character '+r['id'])
        assets=list(r['question']['images'])+re.findall(r'!\[[^\]]*\]\(([^)]+)\)',r['answer']['solution'])
        for asset in assets:
            path=(ROOT/asset).resolve()
            if (ROOT/'data/images/MIT').resolve() not in path.parents or not path.is_file():errors.append('missing/unsafe asset '+asset)
        mapping=mappings[r['id']]
        for field,pages_field in [('question_pdf','question_pdf_pages'),('solution_pdf','solution_pdf_pages')]:
            doc=fitz.open(OUT/mapping[field])
            if not mapping[pages_field] or any(p<1 or p>len(doc) for p in mapping[pages_field]):errors.append('invalid PDF page '+r['id'])
    for folder in [ROOT/'datasets/main',ROOT/'datasets/kaoyan']:
        for path in folder.glob('*.jsonl'):
            for line in path.read_text(encoding='utf-8').splitlines():
                if not line.strip():continue
                old=json.loads(line)
                if isinstance(old,dict) and isinstance(old.get('question'),dict) and re.sub(r'\s+','',old['question'].get('text','')).lower() in texts:errors.append('existing text overlap '+old['id'])
    return {'passed':not errors,'records':len(records),'errors':errors,'checks':['existing JSON Schema','unique IDs','normalized exact-text deduplication within MIT and against main/kaoyan','nonempty source-based solutions','math dollar/brace balance','local safe image references','source PDF page bounds','preservation of existing core records','source PDF checksums']}


def format_concept_choice(record):
    record['metadata']['question_type']='选择题'
    record['question']['text']=record['question']['text'].split(' Choose:')[0]
    record['question']['options']=[{'label':letter,'text':text} for letter,text in zip('ABCDE',['19/1','1/19','20/1','1/20','Unknown'])]
    record['answer']['final_answer']='E'


def write_reports(report):
    previous=(OUT/'README.md').read_text(encoding='utf-8')
    attribution=previous[previous.index('## Attribution and license'):]
    rows=''.join(f'| {s} | {n} |\n' for s,n in report['by_subject'].items())
    text=f'''# MIT 英文大学数学题库

截至2026-10-19，共 **{report['record_count']}条**，均有原材料配套解析。首批52条，第二批新增{len(report['batch2_record_ids'])}条；按大题保留全部小问。18.02SC练习15/16共用题干并求同一通量，合为一条保留两种方法。不代表MIT全量。

| 主学科 | 条数 |
|---|---:|
{rows}
覆盖18.01SC、18.02SC、18.06和18.05；本次优先使用已下载的练习汇总、统计推断练习、线代期末及概率统计期末。实际材料供给使本批概率统计较多，学科配额尚未达成。

- questions.jsonl：正式题答，沿用五个顶层字段。
- sources/与published_sources.json：{report['source_pdf_count']}份原始题答PDF、来源链接、校验和。
- data/images/MIT/：{report['question_figure_count']}张题图及{report['solution_figure_count']}张解析图。
- conversion_report.json：原题号、原PDF页码和课程/主学科对应，及暂缓收录项。
- editorial_changes.json：逐题勘误、补充条件和解释性修订依据。
- validation_report.json、mathematical_checks.json、batch2_mathematical_checks.json：结构检查和实际执行的数学检查。

题干为英文及LaTeX整理稿；解答基于已有原解析进行压缩、校正，不是原版官方解答逐字复制。不对缺解析题从零补写。本次采用PDF文字层提取、原页图文核对，未使用MinerU结果。

第二批以18.05 Exam 1 Long List为主，其他练习卷的重印题不另计；第41题与第26题共用原数据，未重复加入；第71题与第69题仅换CLT数值参数，未另计。精确文本去重不保证消除所有数学等价或跨语言变体。main、mini、kaoyan和既有训练/评测划分未改动。

'''+attribution
    (OUT/'README.md').write_bytes(text.encode('utf-8'))
    lines=['# MIT 收录报告','',f'正式记录：{report["record_count"]}。第二批新增{len(report["batch2_record_ids"])}条，原有52条核心记录保留。','',
      '| 主学科 | 数量 |','|---|---:|']+[f'| {s} | {n} |' for s,n in report['by_subject'].items()]
    lines+=['','## 本批范围','',
      '补齐18.02SC期末第2题、18.05考试1第1题、考试2第I.3题，包含两张必要题图。新增大学概率分布/变换、联合分布、CLT、估计、贝叶斯更新、检验、回归和微积分/线代题答。具体原题号及页码见conversion_report.json。',
      '','原卷笔误有明确勘误，涉及题干修订的记录尤其应参阅editorial_changes.json。未将条件矛盾或缺解析候选直接发布。','',
      '## 暂缓项','']
    lines += [f'- {d["course"]} {d["question"]}：{d["reason"]}' for d in report['deferred_selected_exam_questions']]
    lines+=['','## 校验','', '通过既有Schema、ID、精确文本去重、公式分隔符、资源路径及PDF页码范围检查。数学检查的实际覆盖见两个mathematical_checks文件；未声称所有题目和每一步推导已获独立二次审校。','',
      'MIT材料署名及非商业、相同方式共享许可说明见README。既有题库及划分保持不变。','']
    (OUT/'conversion_report.md').write_bytes('\n'.join(lines).encode('utf-8'))


if __name__=='__main__':main()
