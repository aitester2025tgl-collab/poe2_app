from pathlib import Path
import re
import difflib
import poe2_data_ref
from bs4 import BeautifulSoup

p = Path('data/fetched_pages/mobalytics_woolie_live.html')
html = p.read_text(encoding='utf-8')
soup = BeautifulSoup(html, 'html.parser')

KNOWN_SKILLS = set()
try:
    from poe2_data_ref import KNOWN_SKILLS as KS
n    
except Exception:
    KS = set()

KNOWN_SKILLS = KS

support_map = {}

for h in soup.find_all(['h2','h3','h4','strong','b']):
    t = (h.get_text() or '').lower()
    if 'support gem' in t or 'support gem order' in t or 'support gem requirements' in t:
        parent = h.find_parent()
        blocks = [parent] if parent is not None else []
        blocks.extend(h.find_next_siblings(limit=6))
        for sib in blocks:
            txt = sib.get_text(separator=' ', strip=True)
            # find paren mappings
            for m in re.findall(r"\d+\s*[\)\.]?\s*(.+?)\s*\(\s*(.+?)\s*\)", txt):
                support_name = m[0].strip()
                primary = m[1].strip()
                # canonicalize primary by fuzzy match against KNOWN_SKILLS
                def canonicalize(name):
                    name = name.strip()
                    if not name:
                        return ''
                    if name in KNOWN_SKILLS:
                        return name
                    for s in KNOWN_SKILLS:
                        if s.lower() == name.lower():
                            return s
                    norm = re.sub(r'[^a-z0-9]', '', name.lower())
                    cands = []
                    for s in KNOWN_SKILLS:
                        s_norm = re.sub(r'[^a-z0-9]', '', s.lower())
                        cands.append((s, difflib.SequenceMatcher(None, norm, s_norm).ratio()))
                    cands.sort(key=lambda x: x[1], reverse=True)
                    if cands and cands[0][1] > 0.86:
                        return cands[0][0]
                    return name
                primary_c = canonicalize(primary)
                support_map.setdefault(primary_c, []).append(support_name)

print('Support map extracted (from saved HTML):')
for k,v in support_map.items():
    print(k, '->', v)
