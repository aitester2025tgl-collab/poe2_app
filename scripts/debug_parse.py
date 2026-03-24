from bs4 import BeautifulSoup

html = open('data/fetched_pages/ee701091eda8.html','r',encoding='utf-8').read()
soup = BeautifulSoup(html,'lxml')
print('HEADINGS:')
for h in soup.find_all(['h2','h3','h4']):
    print('TAG', h.name, 'ID', h.get('id'), 'TEXT', (h.get_text() or '').strip()[:60])

print('\nSAMPLE LIST ITEMS (first 20):')
count = 0
for li in soup.find_all('li'):
    txt = li.get_text(separator=' ', strip=True)[:200]
    item_spans = [s.get_text() for s in li.find_all('span', class_=lambda c: c and 'poe2-item' in c)]
    passive_spans = [p.get_text() for p in li.find_all('span', class_=lambda c: c and 'poe2-passive' in c)]
    print('-', txt)
    if item_spans:
        print('  poe2-item spans:', item_spans)
    if passive_spans:
        print('  poe2-passive spans:', passive_spans)
    count += 1
    if count >= 20:
        break
