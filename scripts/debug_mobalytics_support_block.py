from pathlib import Path
import re
from bs4 import BeautifulSoup

p = Path('data/fetched_pages/mobalytics_woolie_live.html')
html = p.read_text(encoding='utf-8')
soup = BeautifulSoup(html, 'html.parser')

# find heading
for h in soup.find_all(['h1','h2','h3','h4','p','div']):
    if 'support gem' in (h.get_text() or '').lower():
        print('--- HEADING TAG:', h.name, 'classes=', ' '.join(h.get('class') or []))
        parent = h.find_parent()
        print('\nParent text:\n', parent.get_text('\n', strip=True)[:1000])
        print('\nSiblings:')
        for sib in h.find_next_siblings():
            print('  sib:', sib.name, 'classes=', ' '.join(sib.get('class') or []), 'text=', (sib.get_text() or '')[:300])
        break

# Try to find the specific block we saw earlier
found = None
for div in soup.find_all('div'):
    t = (div.get_text(' ', strip=True) or '').lower()
    if 'support gem requirements' in t:
        found = div
        break

if found:
    txt = found.get_text(' ', strip=True)
    print('\nFound block text:\n', txt)
    # find numbered sequence patterns
    m = re.search(r'(?:\d+\s*[\)\.]?\s*[A-Za-z].+){2,}', txt)
    print('\nheuristic seq search match:', bool(m))
    # Try to extract the sequence like '1 mace strike 2 rolling slam 3 boneshatter'
    seq = re.findall(r'(?:\d+\s*[\)\.]?\s*)([A-Za-z][A-Za-z0-9\'\- ]+?)(?=(?:\s*\d+\s*[\)\.]?\s*)|$)', txt)
    print('\nseq entries:', seq)
    # Also try to find '1) Name (Primary)' patterns
    par = re.findall(r"\d+\s*[\)\.]?\s*(.+?)\s*\(\s*(.+?)\s*\)", txt)
    print('\nparen pairs:', par)
else:
    print('No block found')
