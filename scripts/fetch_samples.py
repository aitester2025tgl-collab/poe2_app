import json
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import hashlib

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / 'data' / 'poe2_builds.json'
OUT_DIR = ROOT / 'data' / 'fetched_pages_manual'
OUT_DIR.mkdir(parents=True, exist_ok=True)

def save_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None

    h = hashlib.sha1(url.encode('utf-8')).hexdigest()[:12]
    path = OUT_DIR / f"{h}.html"
    path.write_bytes(r.content)

    soup = BeautifulSoup(r.content, 'html.parser')
    title = soup.find('title').text.strip() if soup.find('title') else ''
    text = (soup.find('main') or soup.find('article') or soup.body).get_text(separator=' ', strip=True)[:2000]

    # Simple heuristics
    has_levels = any(s in text.lower() for s in ['level', '1-10', 'act', 'leveling', '1-5', '11-20', '1-10'])
    has_skills = any(s in text for s in ['Skill', 'skill', 'Boneshatter', 'Earthquake', 'Firebrand'])

    return {'url': url, 'file': str(path), 'title': title, 'has_levels': has_levels, 'has_skills': has_skills}

def main():
    data = json.loads(DATA_FILE.read_text(encoding='utf-8'))
    classes = ['Warrior', 'Monk', 'Ranger']
    results = {}
    for cls in classes:
        builds = data.get(cls, [])
        results[cls] = []
        for b in builds[:3]:
            url = b.get('url')
            if not url:
                results[cls].append({'url': None, 'error': 'no url in data'})
                continue
            info = save_url(url)
            if info is None:
                results[cls].append({'url': url, 'error': 'fetch failed'})
            else:
                results[cls].append(info)

    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
