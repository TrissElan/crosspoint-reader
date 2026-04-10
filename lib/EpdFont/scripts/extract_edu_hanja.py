"""Extract 한문교육용 기초한자 1800자 from namu.wiki and save codepoints."""
import urllib.request
import re
import sys

url = 'https://namu.wiki/w/%ED%95%9C%EB%AC%B8%20%EA%B5%90%EC%9C%A1%EC%9A%A9%20%EA%B8%B0%EC%B4%88%20%ED%95%9C%EC%9E%90'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})
resp = urllib.request.urlopen(req)
html = resp.read().decode('utf-8')

# Find section 3 (목록) and section 4 (추가자·제외자) boundaries
sec3_idx = html.find('section=3')
sec4_idx = html.find('section=4')
print(f"Section 3 at: {sec3_idx}, Section 4 at: {sec4_idx}")

if sec3_idx < 0 or sec4_idx < 0:
    print("ERROR: Could not find section markers")
    sys.exit(1)

table_section = html[sec3_idx:sec4_idx]

# Extract CJK characters
table_cjk = set()
for ch in table_section:
    cp = ord(ch)
    if 0x4E00 <= cp <= 0x9FFF:
        table_cjk.add(cp)
    elif 0x3400 <= cp <= 0x4DBF:
        table_cjk.add(cp)
    elif 0x20000 <= cp <= 0x2FA1F:
        table_cjk.add(cp)

print(f'CJK in section 3: {len(table_cjk)}')

sorted_cps = sorted(table_cjk)
with open('edu_hanja_1800.txt', 'w', encoding='utf-8') as f:
    for cp in sorted_cps:
        f.write(f'U+{cp:04X}\n')

print(f'Written {len(sorted_cps)} codepoints to edu_hanja_1800.txt')
print('First 10:', ', '.join(f'U+{cp:04X}({chr(cp)})' for cp in sorted_cps[:10]))
print('Last 10:', ', '.join(f'U+{cp:04X}({chr(cp)})' for cp in sorted_cps[-10:]))
