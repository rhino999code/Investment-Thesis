"""Markdown -> styled HTML -> PDF (Playwright/Chromium), with a two-pass TOC that carries page numbers.
Usage: python3 build_pdf.py report.md out.pdf
"""
import re, sys, os, subprocess, html
import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
src, out_pdf = sys.argv[1], sys.argv[2]
text = open(src, encoding="utf-8").read()

# ---------- markdown -> body html ----------
md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists", "toc"],
                       extension_configs={"toc": {"toc_depth": "2-3"}})
body = md.convert(text)

# drop the title block (h1 + h2 + meta list + hr) — the cover replaces it
body = re.sub(r'^<h1[^>]*>.*?</h1>\s*<h2[^>]*>.*?</h2>\s*<ul>.*?</ul>\s*<hr\s*/?>', '', body, count=1, flags=re.S)
# remove remaining <hr> separators (each h2 already starts a new page)
body = re.sub(r'<hr\s*/?>', '', body)

# ---------- chapter openers ----------
def chapter(m):
    attrs, inner = m.group(1), m.group(2)
    plain = re.sub(r'<[^>]+>', '', inner)
    mm = re.match(r'^PART (\d+)\.\s*(.+)$', plain)
    if mm:
        num, title = mm.groups()
        sub = {"1": "먼저 읽는 부분. 결론, 로드맵, 시기별로 사야 할 것과 피할 것.",
               "2": "근거, 시기별 전개, 카테고리 표, 자본시장, 포트폴리오, 시그널."}.get(num, "")
        return (f'<section class="part"{attrs}><div class="part-kicker">PART {num}</div>'
                f'<h2 class="part-title">{html.escape(title)}</h2><div class="part-sub">{sub}</div></section>')
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

# ---------- rating symbols in table cells ----------
RATING = {'◎': 'r-core', '○': 'r-up', '△': 'r-sel', '✕': 'r-avoid'}
def rate_cell(m):
    cell = m.group(2)
    stripped = re.sub(r'<[^>]+>', '', cell).strip()
    if stripped and stripped[0] in RATING:
        cls = RATING[stripped[0]]
        return f'<td class="rate {cls}"{m.group(1)}>{cell}</td>'
    return m.group(0)
body = re.sub(r'<td([^>]*)>(.*?)</td>', rate_cell, body, flags=re.S)

# highlight risk words in last column
body = re.sub(r'<td>(<strong>)?높음(</strong>)?( \([^)]*\))?</td>', lambda m: f'<td class="risk-high">높음{m.group(3) or ""}</td>', body)

# ---------- TOC ----------
toc = md.toc
toc = re.sub(r'<li><a href="#[^"]*">2026[^<]*</a></li>\s*', '', toc, count=1)  # subtitle
toc = re.sub(r'<li><a href="#[^"]*">이 리포트를 읽는 법</a>(<ul>.*?</ul>)?</li>\s*', '', toc, count=1, flags=re.S)
# strip "N. 매크로 메가트렌드 k:" to shorter "N. 매크로 메가트렌드 k · title"
toc = toc.replace('매크로 메가트렌드 1:', '매크로 메가트렌드 1 ·').replace('매크로 메가트렌드 2:', '매크로 메가트렌드 2 ·') \
         .replace('매크로 메가트렌드 3:', '매크로 메가트렌드 3 ·').replace('매크로 메가트렌드 4:', '매크로 메가트렌드 4 ·') \
         .replace('매크로 메가트렌드 5:', '매크로 메가트렌드 5 ·')

CSS = open(os.path.join(HERE, "report.css"), encoding="utf-8").read()

COVER = """
<section class="cover">
  <div class="cover-kicker">INVESTMENT THESIS · v4.0</div>
  <h1 class="cover-title">과부하의 시대</h1>
  <div class="cover-sub">The Age of Overload</div>
  <div class="cover-desc">2026–2037 투자 Thesis<br>5대 매크로 메가트렌드와 12년 카테고리 로드맵</div>
  <div class="cover-trends">
    <div><span>1</span>AI 연산 수요와 에너지 제약</div>
    <div><span>2</span>노동을 대체하는 자본</div>
    <div><span>3</span>쪼개지는 세계와 재무장</div>
    <div><span>4</span>일상이 된 물리적 위험</div>
    <div><span>5</span>재정의 한계와 분배의 정치</div>
  </div>
  <div class="cover-meta">
    <div>작성일 2026년 9월 7일</div>
    <div>12년 지평 · 3년 단위 4개 시기 · 큰 흐름에서 세부 카테고리까지</div>
    <div>글로벌(미국 중심) + 한국 시사점</div>
  </div>
</section>
"""

HEAD = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>과부하의 시대 — 2026–2037 투자 Thesis</title><style>{CSS}</style></head>"""

def cover_html():
    return HEAD + f'<body class="cover-doc">{COVER}</body></html>'

def build_html(toc_html):
    return HEAD + f"""<body><section class="toc-page"><div class="kicker">차례</div><h2 class="chapter-title">목차</h2>{toc_html}</section>
<main>{body}</main></body></html>"""

def render(html_text, pdf_path, mode=""):
    hp = pdf_path[:-4] + ".html"
    open(hp, "w", encoding="utf-8").write(html_text)
    env = dict(os.environ, NODE_PATH="/opt/node22/lib/node_modules")
    subprocess.run(["node", os.path.join(HERE, "render.js"), hp, pdf_path, mode], check=True, env=env)

body_pdf = out_pdf[:-4] + "_body.pdf"
cover_pdf = out_pdf[:-4] + "_cover.pdf"

# pass 1 (body only; printed page numbers = index + 1)
render(build_html(toc), body_pdf)

import pypdfium2 as pdfium
pdf = pdfium.PdfDocument(body_pdf)
pages = [re.sub(r'\s+', '', pdf[i].get_textpage().get_text_range()) for i in range(len(pdf))]
n_pages = len(pages)
# body starts at the first page that is not a TOC page: the first PART divider, else first page without '목차'
start = 0
for i, t in enumerate(pages):
    if t.startswith('PART1') or t.startswith('PART1.'):
        start = i
        break
else:
    while start < n_pages and '목차' in pages[start][:60]:
        start += 1

cursor = [start]  # headings appear in document order, so never look backwards

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

# merge cover + body
dest = pdfium.PdfDocument.new()
for p in (cover_pdf, body_pdf):
    src = pdfium.PdfDocument(p)
    dest.import_pages(src)
dest.save(out_pdf)
print("pages", len(pdfium.PdfDocument(out_pdf)))
