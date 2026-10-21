"""Reviewed training cleanup. Stage first; publish only after reviewing the candidate.

Input is a canonical JSONL snapshot; explicit record overrides accompany this file.
No downloads, generated IDs, exclusions, or rubric regeneration are performed.
"""
from __future__ import annotations

import argparse
import ast
import copy
import json
import re
from pathlib import Path
import sympy as sp
from sympy.printing.latex import LatexPrinter

ROOT = Path(__file__).resolve().parents[3]
COMMANDS = ('Leftrightarrow', 'overrightarrow', 'leqslant', 'geqslant', 'therefore',
            'Rightarrow', 'triangle', 'because', 'lambda', 'alpha', 'theta', 'Delta',
            'angle', 'times', 'cdot', 'cong', 'neq', 'sim', 'bot', 'sin', 'cos', 'tan', 'pm', 'pi')


def clean_text(text: str) -> str:
    for bad, good in [('三棱雉','三棱锥'),('圆雉','圆锥'),('四棱雉','四棱锥'),
                      ('答客','答案'),('答家','答案'),('羊解','解析')]:
        text = text.replace(bad,good)
    text = re.sub(r'(【[^】\n]+】)\s*\}',r'\1',text)
    text = re.sub(r'\\square(?=\s*A\s*B\s*C)',r'\\triangle',text)
    text=text.replace('^{2+}','^{2}+').replace('^{2-}','^{2}-')
    text=re.sub(r'a\s+\\operatorname\{acsin\}',lambda m:r'a c\sin',text)
    for bad,good in {'cost':r'\cos t','lnc':r'\ln c','lnk':r'\ln k','lgn':r'\lg n',
                     'tant':r'\tan t','lgx':r'\lg x','lnt':r'\ln t','In':r'\ln',
                     'acos':r'a\cos','accos':r'a c\cos','acsin':r'a c\sin',
                     'csin':r'c\sin','aln':r'a\ln'}.items():
        text=text.replace('\\operatorname{'+bad+'}',good)
    protected=set(COMMANDS)|{'cdots','ldots','dots','simeq','triangleq','pmod','sinh','cosh','tanh'}
    def separate(m):
        token=m[1]
        if token in protected:return m[0]
        for cmd in COMMANDS:
            if token.startswith(cmd):return '\\'+cmd+' '+token[len(cmd):]
        return m[0]
    text=re.sub(r'\\([A-Za-z]+)',separate,text)
    return text


def math_expression(text: str) -> str:
    """Whitelist AST conversion: no eval, SymPy parser, or arbitrary calls."""
    node=ast.parse(text.replace('^','**').strip(),mode='eval').body
    def value(n):
        if isinstance(n,ast.Constant) and type(n.value) in (int,float):return sp.sympify(str(n.value))
        if isinstance(n,ast.Name):
            return {'pi':sp.pi,'oo':sp.oo,'alpha':sp.Symbol('alpha'),'pm':sp.Symbol('PM')}.get(n.id,sp.Symbol(n.id))
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.UAdd,ast.USub)):
            return value(n.operand) if isinstance(n.op,ast.UAdd) else -value(n.operand)
        if isinstance(n,ast.BinOp):
            a,b=value(n.left),value(n.right)
            if isinstance(n.op,ast.Add):return sp.Add(a,b,evaluate=False)
            if isinstance(n.op,ast.Sub):return sp.Add(a,-b,evaluate=False)
            if isinstance(n.op,ast.Mult):return sp.Mul(a,b,evaluate=False)
            if isinstance(n.op,ast.Div):return sp.Mul(a,sp.Pow(b,-1,evaluate=False),evaluate=False)
            if isinstance(n.op,ast.Pow):return sp.Pow(a,b,evaluate=False)
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and len(n.args)==1 and not n.keywords:
            fn={'sqrt':sp.sqrt,'Cos':sp.cos,'Sin':sp.sin}.get(n.func.id)
            if fn:return fn(value(n.args[0]))
        raise ValueError(f'Unsupported math AST: {ast.dump(n)}')
    class Printer(LatexPrinter):
        def _print_Mul(self, expr):
            pm=sp.Symbol('PM')
            if expr.has(pm) and expr.subs(pm,0)==0:
                return r'\pm '+self._print(expr.subs(pm,1))
            return super()._print_Mul(expr)
        def _print_Symbol(self, expr):
            return r'\pm' if expr.name=='PM' else super()._print_Symbol(expr)
    return Printer().doprint(value(node))


def conic_answer(text: str) -> str:
    text=text.strip()
    if '$' in text or '\\' in text or re.search('[\u4e00-\u9fff]',text):return text
    # Explicit DSL translations and interval unions preserve set/point semantics.
    text=re.sub(r'ApplyUnit\((\d+),\s*degree\)',r'\1DEG',text)
    text=text.replace('LineSegmentOf(F1,F2)',r'\overline{F_1F_2}')
    text=text.replace('Negation(y=0)','y!=0').replace('Negation(x = 0)','x!=0')
    def split_top(t, sep):
        level=0;parts=[];last=0
        for i,c in enumerate(t):
            if c in '([{':level+=1
            elif c in ')]}':level-=1
            elif c==sep and level==0:parts.append(t[last:i]);last=i+1
        parts.append(t[last:]);return parts
    def format_part(t):
        t=t.strip()
        if t.startswith('\\'):return t
        if '\n' in t:return r'\ ;\ '.join(format_part(v) for v in t.splitlines())
        if t.startswith('{') and t.endswith('}'):
            inner=t[1:-1]
            if any('oo' in x for x in split_top(inner,',')):return format_part(inner)
            return r'\{'+', '.join(format_part(v) for v in split_top(inner,','))+r'\}'
        parts=split_top(t,'&')
        if len(parts)>1:return r',\quad '.join(format_part(v) for v in parts)
        if re.search(r'[)\]]\s*\+\s*[(\[]',t):
            return r'\cup'.join(format_part(v) for v in re.split(r'(?<=[)\]])\s*\+\s*(?=[(\[])',t))
        if len(t)>1 and t[0] in '([' and t[-1] in ')]':
            parts=split_top(t[1:-1],',')
            if len(parts)>1:return t[0]+', '.join(format_part(v) for v in parts)+t[-1]
            return format_part(t[1:-1])
        parts=split_top(t,',')
        if len(parts)>1:return ', '.join(format_part(v) for v in parts)
        if '!=' in t:return r'\ne'.join(format_part(v) for v in t.split('!='))
        if '=' in t:return '='.join(format_part(v) for v in t.split('='))
        if re.fullmatch(r'\d+DEG',t):return t[:-3]+r'^\circ'
        for rel in ('<','>'):
            if rel in t:return rel.join(format_part(v) for v in t.split(rel))
        return math_expression(t)
    return '$'+format_part(text)+'$'


def conic_solution(text: str) -> str:
    text=clean_text(text)
    # These literal powers were verified in their individual equation contexts.
    text=re.sub(r'(?<![A-Za-z])([abcmxy])([23])(?![\d.])',r'\1^{\2}',text)
    text=text.replace('v2','y^{2}')
    # Preserve already delimited solutions; most original Conic10K solutions are raw LaTeX.
    if '$' in text:return text
    pieces=re.split(r'([\u4e00-\u9fff，。；：、【】]+)',text)
    def wrap(t):
        if not t or re.fullmatch(r'[\u4e00-\u9fff，。；：、【】]+',t):return t
        stripped=t.strip()
        if re.search(r'[A-Za-z0-9\\]',stripped):return '$'+stripped+'$'
        return t
    return ''.join(wrap(p) for p in pieces)


def curate(record: dict, overrides: dict) -> dict:
    r=copy.deepcopy(record)
    r['question']['text']=clean_text(r['question']['text'])
    for key in ('final_answer','solution'):r['answer'][key]=clean_text(r['answer'][key])
    if r['source']=='conic10k':
        if 'answer.final_answer' not in overrides.get(r['id'],{}):
            r['answer']['final_answer']=conic_answer(r['answer']['final_answer'])
        r['answer']['solution']=conic_solution(r['answer']['solution'])
    elif r['metadata']['question_type']=='解答题':
        # The old final_answer holds the detailed worked solution; retain it there.
        reviewed_final=overrides.get(r['id'],{}).get('answer.final_answer')
        if isinstance(reviewed_final,str):reviewed_final=clean_text(reviewed_final)
        if r['answer']['final_answer']!=reviewed_final:
            r['answer']['solution']=r['answer']['final_answer']
    else:
        r['answer']['final_answer']=re.sub(r'\s*[。．.]\s*$','',r['answer']['final_answer']).strip()
        r['answer']['final_answer']=re.sub(r'(?<=\d)\.\s+(?=\d)', '.',r['answer']['final_answer'])
    for path,text in overrides.get(r['id'],{}).items():
        group,field=path.split('.')
        r[group][field]=clean_text(text) if isinstance(text,str) else text
    return r


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.input.resolve()==a.output.resolve():raise ValueError('Use a separate staging output.')
    changes=json.loads(Path(__file__).with_name('overrides.json').read_text(encoding='utf-8'))
    rows=[json.loads(l) for l in a.input.read_text(encoding='utf-8-sig').splitlines() if l.strip()]
    assert set(changes)<=set(r['id'] for r in rows)
    fixed=[curate(r,changes) for r in rows]
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes((''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in fixed)).encode('utf-8'))
    print(json.dumps({'records':len(fixed),'changed':sum(a!=b for a,b in zip(rows,fixed))}))

if __name__=='__main__':main()
