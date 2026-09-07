"""Concatenate part files, normalise list spacing, and replace 1기~4기 with year ranges."""
import re, sys
out = sys.argv[1]
parts = sys.argv[2:]
s = "".join(open(p, encoding="utf-8").read() for p in parts)

# lists directly after a bold line need a blank line for python-markdown
s = re.sub(r'(^\*\*[^\n]+\*\*)\n(- )', r'\1\n\n\2', s, flags=re.M)

YEARS = {"1": "2026–28", "2": "2029–31", "3": "2032–34", "4": "2035–37"}
# "1기 26–28", "1기(2026–28)", "1기 2026–28" -> "2026–28"
for k, y in YEARS.items():
    short = y[2:]  # 26–28
    s = re.sub(rf'{k}기\s*\(?\s*(?:20)?{re.escape(short)}\s*\)?년?', y, s)
# remaining bare "N기" (not part of another word like "장기", "단기", "초기", "분기")
def bare(m):
    return YEARS[m.group(1)] + "년"
s = re.sub(r'(?<![가-힣0-9])([1-4])기(?![가-힣])', bare, s)
# table headers that now read "2026–28년" inside header rows: keep year form without 년 in |-delimited headers
s = re.sub(r'\|\s*(20\d\d–\d\d)년\s*(?=\|)', r'| \1 ', s)

open(out, "w", encoding="utf-8").write(s)
print("md bytes", len(s.encode()))
left = re.findall(r'[1-4]기(?![가-힣])', s)
print("remaining N기:", len(left))
