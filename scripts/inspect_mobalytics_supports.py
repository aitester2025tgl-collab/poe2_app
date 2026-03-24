import requests
from bs4 import BeautifulSoup
from pathlib import Path

URL = 'https://mobalytics.gg/poe-2/builds/warrior-leveling-woolie#passive-tree-0'
print('Fetching', URL)
resp = requests.get(URL, headers={'User-Agent':'Mozilla/5.0'}, timeout=20)
resp.raise_for_status()
html = resp.text
soup = BeautifulSoup(html, 'html.parser')

candidates = []
for el in soup.find_all(True):
    txt = (el.get_text(separator=' ', strip=True) or '').lower()
    if 'support' in txt and len(txt) < 200:
        candidates.append((el.name, ' '.join(el.get('class') or []), txt[:200], str(el)[:400]))

print('Found', len(candidates), 'small elements containing "support"')
for i, (name, classes, txt, snippet) in enumerate(candidates[:30], 1):
    print(f"\n{i}) <{name}> class='{classes}'\n  text: {txt}\n  snippet-start: {snippet}\n")

# Also find headings that include 'Support Gem'
print('\nHeadings containing "support":')
for h in soup.find_all(['h1','h2','h3','h4','h5','strong','b']):
    if 'support' in (h.get_text() or '').lower():
        print(h.name, 'class=' , ' '.join(h.get('class') or []), 'text=', h.get_text()[:200])

# Save fetched HTML to data/fetched_pages for reproducibility
outdir = Path(__file__).resolve().parent.parent / 'data' / 'fetched_pages'
outdir.mkdir(parents=True, exist_ok=True)
filename = outdir / 'mobalytics_woolie_live.html'
filename.write_text(html, encoding='utf-8')
print('\nSaved live HTML to', filename)
