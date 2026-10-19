"""Download public MIT OCW exam resources and preserve source provenance."""
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import pymupdf as fitz

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'datasets/MIT'
RAW = ROOT / 'workspace/extracted/MIT'
COURSES = {
    '1801sc': '18-01sc-single-variable-calculus-fall-2010',
    '1802sc': '18-02sc-multivariable-calculus-fall-2010',
    '1806': '18-06-linear-algebra-spring-2010',
    '1805': '18-05-introduction-to-probability-and-statistics-spring-2022',
}


def get(url):
    r = requests.get(url, timeout=90)
    r.raise_for_status()
    return r


def collect(course):
    slug = COURSES[course]
    base = f'https://ocw.mit.edu/courses/{slug}/'
    # The resources listing includes searchable descriptions and PDF URLs.
    url = base if course.endswith('sc') else base + ('resources/exams/' if course == '1805' else 'pages/exams/')
    soup = BeautifulSoup(get(url).text, 'html.parser')
    links = {}
    anchors = list(soup.select('main a[href]')) or list(soup.select('a[href]'))
    exam_pages = {urljoin(url,a['href']) for a in anchors if '/pages/' in a['href'] and re.search(r'exam',a.get_text(' ',strip=True),re.I)}
    for page_url in sorted(exam_pages):
        anchors.extend(BeautifulSoup(get(page_url).text,'html.parser').select('a[href]'))
    for a in anchors:
        href = urljoin(url, a['href'])
        title = a.get_text(' ', strip=True)
        if '/resources/' in href and href.rstrip('/') != url.rstrip('/'):
            if course == '1806' or re.search(r'exam|final|quiz|ex\d|exams|solutions', title + ' ' + href, re.I):
                links[href] = title
    return course, links


def download(item):
    course, url, title = item
    soup = BeautifulSoup(get(url).text, 'html.parser')
    pdfs = [urljoin(url, a['href']) for a in soup.select('a[href]') if '.pdf' in a['href'].lower()]
    if not pdfs:
        return None
    pdf_url = pdfs[0]
    filename = pdf_url.split('/')[-1]
    folder = RAW / course
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / filename
    if not path.exists():
        path.write_bytes(get(pdf_url).content)
    doc = fitz.open(path)
    pages = [p.get_text(sort=True) for p in doc]
    path.with_suffix('.txt').write_text('\n\n'.join(f'=== PAGE {i+1} ===\n{s}' for i,s in enumerate(pages)), encoding='utf-8')
    return {'course': course, 'title': title, 'resource_url': url, 'pdf_url': pdf_url,
            'local_pdf': str(path.relative_to(ROOT)).replace('\\','/'), 'pages': len(doc),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        inventory = dict(pool.map(collect, COURSES))
    (RAW / 'resource_links.json').write_text(json.dumps(inventory, indent=2), encoding='utf-8')
    jobs = [(c,u,t) for c,links in inventory.items() for u,t in links.items()]
    print('Exam resources:', {c:len(v) for c,v in inventory.items()}, flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        result = [r for r in pool.map(download,jobs) if r]
    (OUT / 'source_manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Downloaded',len(result),'PDFs;',sum(r['pages'] for r in result),'pages',flush=True)


if __name__ == '__main__':
    main()
