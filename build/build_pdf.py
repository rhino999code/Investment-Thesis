"""Markdown -> styled HTML -> PDF (Playwright/Chromium), with a two-pass TOC that carries page numbers.
Usage: python3 build_pdf.py report.md out.pdf
"""
import re, sys, os, subprocess, html
import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
src, out_pdf = sys.argv[1], sys.argv[2]
text = open(src, encoding="utf-8").read()

VERSION = "v6.1"
DATE = "2026년 9월 7일"

# ---------- markdown -> body html ----------
md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists", "toc"],
                       extension_configs={"toc": {"toc_depth": "2-2"}})
# adjacent "> " cards separated by a blank line must stay separate blockquotes
text = re.sub(r'\n\n(?=> \*\*\[)', '\n\n<!-- card -->\n\n', text)
body = md.convert(text)
body = body.replace('<!-- card -->', '')
# split blockquotes that python-markdown merged across the marker
body = re.sub(r'</blockquote>\s*<blockquote>', '</blockquote>\n<blockquote>', body)

# drop the title block (h1 + h2 + meta list + hr): the cover and sub-cover replace it
body = re.sub(r'^<h1[^>]*>.*?</h1>\s*<h2[^>]*>.*?</h2>\s*<ul>.*?</ul>\s*<hr\s*/?>', '', body, count=1, flags=re.S)
body = re.sub(r'<hr\s*/?>', '', body)

# ---------- chapter openers ----------
PART_SUB = {
    "2": "근거, 시기별 전개, 카테고리 표, 자본시장, 포트폴리오, 시그널.",
    "3": "숫자가 한 사람의 하루에서 어떻게 보이는가. 2030년 서울, 2035년 텍사스, 2040년 호치민.",
}
def chapter(m):
    attrs, inner = m.group(1), m.group(2)
    plain = re.sub(r'<[^>]+>', '', inner)
    mm = re.match(r'^PART (\d+)\.\s*(.+)$', plain)
    if mm:
        num, title = mm.groups()
        return (f'<section class="part"{attrs}><div class="part-kicker">PART {num}</div>'
                f'<h2 class="part-title">{html.escape(title)}</h2>' + (f'<div class="part-sub">{PART_SUB[num]}</div>' if num in PART_SUB else '') + '</section>')
    mm = re.match(r'^(\d+)\.\s*매크로 메가트렌드 (\d+):\s*(.+)$', plain)
    if mm:
        num, tnum, title = mm.groups()
        return (f'<section class="chapter mega"{attrs}><div class="kicker">{num}장 · 매크로 메가트렌드 {tnum}</div>'
                f'<h2 class="chapter-title">{html.escape(title)}</h2></section>')
    mm = re.match(r'^(\d+)\.\s*(.+)$', plain)
    if mm:
        num, title = mm.groups()
        return (f'<section class="chapter"{attrs}><div class="kicker">{num}장</div>'
                f'<h2 class="chapter-title">{html.escape(title)}</h2></section>')
    mm = re.match(r'^부록 ([A-Z])\.\s*(.+)$', plain)
    if mm:
        return (f'<section class="chapter"{attrs}><div class="kicker">부록 {mm.group(1)}</div>'
                f'<h2 class="chapter-title">{html.escape(mm.group(2))}</h2></section>')
    return f'<section class="chapter"{attrs}><h2 class="chapter-title">{inner}</h2></section>'

body = re.sub(r'<h2([^>]*)>(.*?)</h2>', chapter, body, flags=re.S)

# ---------- trend tags: **[트렌드 1 · …] text** -> pill + bold text ----------
body = re.sub(r'<strong>\[([^\]]+)\]\s*(.*?)</strong>',
              lambda m: f'<span class="tag">{m.group(1)}</span>' + (f' <strong>{m.group(2)}</strong>' if m.group(2).strip() else ''),
              body, flags=re.S)

# ---------- rating symbols in table cells ----------
RATING = {'◎': 'r-core', '○': 'r-up', '△': 'r-sel', '✕': 'r-avoid'}
def rate_cell(m):
    cell = m.group(2)
    stripped = re.sub(r'<[^>]+>', '', cell).strip()
    if stripped and stripped[0] in RATING:
        return f'<td class="rate {RATING[stripped[0]]}"{m.group(1)}>{cell}</td>'
    return m.group(0)
body = re.sub(r'<td([^>]*)>(.*?)</td>', rate_cell, body, flags=re.S)
def keep_short(m):
    plain = re.sub(r'<[^>]+>', '', m.group(1))
    return f'<blockquote class="keep">{m.group(1)}</blockquote>' if len(plain) < 420 else m.group(0)
body = re.sub(r'<blockquote>(.*?)</blockquote>', keep_short, body, flags=re.S)
body = re.sub(r'<td>(<strong>)?높음(</strong>)?( \([^)]*\))?</td>', lambda m: f'<td class="risk-high">높음{m.group(3) or ""}</td>', body)

# ---------- TOC (top level only) ----------
toc = md.toc
toc = re.sub(r'<li><a href="#[^"]*">2026[^<]*</a></li>\s*', '', toc, count=1)
toc = re.sub(r'매크로 메가트렌드 (\d):', r'매크로 메가트렌드 \1 ·', toc)
# the summary chapter shares its title with the PART divider: list it once
toc = re.sub(r'<li><a href="#[^"]*">Investment Thesis Summary</a></li>\s*', '', toc, count=1)

CSS = open(os.path.join(HERE, "report.css"), encoding="utf-8").read()
HEAD = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>과부하의 시대 — 2026–2037 투자 Thesis</title><style>{CSS}</style></head>"""

COVER = f"""
<section class="cover">
  <h1 class="cover-title">과부하의 시대</h1>
  <div class="cover-sub">The Age of Overload</div>
  <div class="cover-desc">2026–2037 투자 Thesis</div>
  <div class="cover-foot">
    <div class="org">AXE Corporation</div>
    <div>Writer: 한진우</div>
    <div>작성일 {DATE}</div>
  </div>
</section>
"""

SUBCOVER = f"""
<section class="subcover">
  <h2>과부하의 시대 (The Age of Overload)</h2>
  <div class="sc-sub">2026–2037 투자 Thesis: 5대 매크로 메가트렌드와 12년 카테고리 로드맵</div>
  <table>
    <tr><th>버전</th><td>{VERSION}</td></tr>
    <tr><th>작성일</th><td>{DATE}</td></tr>
    <tr><th>작성</th><td>한진우, AXE Corporation</td></tr>
    <tr><th>구성</th><td>PART 1 Investment Thesis Summary<br>PART 2 본문 (근거, 시기별 전개, 카테고리 표, 자본시장, 포트폴리오, 시그널)<br>PART 3 2030 · 2035 · 2040년의 하루</td></tr>
    <tr><th>지평</th><td>12년, 3년 단위 (2026–28 / 2029–31 / 2032–34 / 2035–37)</td></tr>
  </table>
  <div class="sc-note">이 리포트는 공개 자료를 바탕으로 한 구조적 분석이며 특정 종목의 매수·매도 권유가 아니다. 기업명은 카테고리를 설명하기 위한 예시다. 본문 숫자는 2026년 9월 4일 기준이며 일부는 2차 자료로, 투자 집행 전 원자료 확인이 필요하다.</div>
</section>
"""

def cover_html():
    return HEAD + f'<body class="cover-doc">{COVER}</body></html>'

def build_html(toc_html):
    return HEAD + f"""<body>{SUBCOVER}<section class="toc-page"><div class="kicker">차례</div><h2 class="chapter-title">목차</h2>{toc_html}</section>
<main>{body}</main></body></html>"""

def render(html_text, pdf_path, mode=""):
    hp = pdf_path[:-4] + ".html"
    open(hp, "w", encoding="utf-8").write(html_text)
    env = dict(os.environ, NODE_PATH="/opt/node22/lib/node_modules")
    subprocess.run(["node", os.path.join(HERE, "render.js"), hp, pdf_path, mode], check=True, env=env)

body_pdf = out_pdf[:-4] + "_body.pdf"
cover_pdf = out_pdf[:-4] + "_cover.pdf"

# pass 1
render(build_html(toc), body_pdf)

import pypdfium2 as pdfium
pdf = pdfium.PdfDocument(body_pdf)
pages = [re.sub(r'\s+', '', pdf[i].get_textpage().get_text_range()) for i in range(len(pdf))]
n_pages = len(pages)
start = 0
for i, t in enumerate(pages):
    if t.startswith('PART1'):
        start = i
        break
cursor = [start]

def find_page(title):
    key = re.sub(r'\s+', '', re.sub(r'<[^>]+>', '', title))
    key = re.sub(r'매크로메가트렌드(\d)·', r'매크로메가트렌드\1', key)
    stripped = re.sub(r'^(PART\d+\.|\d+\.|부록[A-Z]\.)', '', key)
    stripped = re.sub(r'^매크로메가트렌드\d', '', stripped)
    for probe in (key, key.replace('.', ''), stripped, stripped[:12], key[:12]):
        for i in range(cursor[0], n_pages):
            if probe and probe in pages[i]:
                cursor[0] = i
                return i + 1
    return None

def add_pages(m):
    href, title = m.group(1), m.group(2)
    p = find_page(title)
    pn = f'<span class="lead"></span><span class="pg">{p}</span>' if p else ''
    return f'<a href="{href}"><span class="t">{title}</span>{pn}</a>'

toc2 = re.sub(r'<a href="(#[^"]*)">(.*?)</a>', add_pages, toc)
render(build_html(toc2), body_pdf)
render(cover_html(), cover_pdf, "nofooter")

dest = pdfium.PdfDocument.new()
for p in (cover_pdf, body_pdf):
    dest.import_pages(pdfium.PdfDocument(p))
dest.save(out_pdf)
print("pages", len(pdfium.PdfDocument(out_pdf)))
