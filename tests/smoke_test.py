import sys
from pathlib import Path

# Ensure project root is on sys.path so imports from repo root work when running
# this script from the tests/ directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import poe2_fetcher

print('IMPORTED poe2_fetcher OK')

sg = getattr(poe2_fetcher, 'search_google', None)
print('search_google found:', bool(sg))
if sg:
    try:
        res = sg('poe2 test', num=1)
        print('search_google result:', res)
    except Exception as e:
        print('search_google error:', type(e).__name__, e)

oc = getattr(poe2_fetcher, 'OLLAMA_CLIENT', None)
print('OLLAMA_CLIENT object:', oc)
if oc:
    try:
        print('Attempting OLLAMA_CLIENT.list()...')
        lst = oc.list()
        print('OLLAMA list result:', lst)
    except Exception as e:
        print('OLLAMA list error:', type(e).__name__, str(e))
else:
    print('OLLAMA client not available; skipping list()')
