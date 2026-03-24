from pathlib import Path
import json
import sys
from bs4 import BeautifulSoup

# Ensure repo root on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from poe2_fetcher import parse_maxroll, parse_mobalytics

DATA_DIR = PROJECT_ROOT / 'data' / 'fetched_pages'

def run():
    if not DATA_DIR.exists():
        print('No fetched_pages directory found at', DATA_DIR)
        return

    files = list(DATA_DIR.glob('*.html'))
    if not files:
        print('No HTML files found in', DATA_DIR)
        return

    for f in files:
        print('\n--- Parsing', f.name, '---')
        html = f.read_text(encoding='utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        url = f.name
        # Try Maxroll then Mobalytics
        out = None
        if 'maxroll' in f.name.lower():
            out = parse_maxroll(soup, url)
        elif 'mobalytics' in f.name.lower():
            out = parse_mobalytics(soup, url)
        else:
            # try both
            out = parse_maxroll(soup, url) or parse_mobalytics(soup, url)

        print(json.dumps(out, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    run()
