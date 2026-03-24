from pathlib import Path
import sys
import requests
from bs4 import BeautifulSoup
import json

# Ensure repo root on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from poe2_fetcher import parse_mobalytics

URL = 'https://mobalytics.gg/poe-2/builds/warrior-leveling-woolie#passive-tree-0'

print('Fetching', URL)
headers = {'User-Agent': 'Mozilla/5.0'}
resp = requests.get(URL, headers=headers, timeout=20)
resp.raise_for_status()
html = resp.text
soup = BeautifulSoup(html, 'html.parser')

print('Running parse_mobalytics...')
out = parse_mobalytics(soup, URL)
print(json.dumps(out, indent=2, ensure_ascii=False))
