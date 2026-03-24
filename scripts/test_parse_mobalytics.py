import json
import requests
from bs4 import BeautifulSoup
import os

URL = 'https://mobalytics.gg/poe-2/builds/warrior-leveling-woolie#passive-tree-0'

os.makedirs('../data/fetched_pages', exist_ok=True)

resp = requests.get(URL, headers={'User-Agent': 'poe2-fetcher/1.0'})
html = resp.text
with open('../data/fetched_pages/mobalytics_test.html', 'w', encoding='utf-8') as f:
    f.write(html)

soup = BeautifulSoup(html, 'lxml')

import poe2_fetcher

res = poe2_fetcher.parse_mobalytics(soup, URL)
print(json.dumps(res, indent=2, ensure_ascii=False))
