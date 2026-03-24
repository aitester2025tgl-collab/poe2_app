import sys
from pathlib import Path

# Ensure project root on path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    import poe2_fetcher
except Exception as e:
    print('Failed to import poe2_fetcher:', e)
    raise

from bs4 import BeautifulSoup

SAVED = ROOT / 'data' / 'fetched_pages_manual'
if not SAVED.exists():
    print('No saved pages at', SAVED)
    sys.exit(1)

files = list(SAVED.glob('*.html'))
print('Found', len(files), 'saved pages')

results = []
for f in files:
    print('Processing', f.name)
    content = f.read_bytes()
    soup = BeautifulSoup(content, 'html.parser')
    main = soup.find('main') or soup.find('article') or soup.body
    text = main.get_text(separator=' ', strip=True) if main else soup.get_text(separator=' ', strip=True)
    url = f'file://{f.resolve()}'
    try:
        res = poe2_fetcher.extract_build_details_with_llm(text, 'Warrior', url)
        results.append({'file': f.name, 'result': 'ok' if res else 'none', 'build_name': res.get('build_name') if res else None})
        print(' ->', 'ok' if res else 'no data')
    except Exception as e:
        results.append({'file': f.name, 'result': 'error', 'error': str(e)})
        print(' -> ERROR', e)

print('\nSummary:')
for r in results:
    print(r)

print('\nDone')
