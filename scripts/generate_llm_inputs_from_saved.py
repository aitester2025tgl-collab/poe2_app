import sys
from pathlib import Path
import hashlib
import re

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
SAVED_DIRS = [DATA_DIR / 'fetched_pages_manual', DATA_DIR / 'fetched_pages']
OUT_DIR = DATA_DIR / 'llm_inputs'
OUT_DIR.mkdir(parents=True, exist_ok=True)

def extract_text_from_html(path: Path) -> str:
    try:
        from bs4 import BeautifulSoup
    except Exception:
        return path.read_text(encoding='utf-8', errors='ignore')
    content = path.read_bytes()
    soup = BeautifulSoup(content, 'html.parser')
    main = soup.find('main') or soup.find('article') or soup.body
    text = main.get_text(separator=' ', strip=True) if main else soup.get_text(separator=' ', strip=True)
    return text

def make_prompt(text: str, class_name: str = 'Warrior', url: str = '') -> str:
    header = f"You are a bot of extraction. Extract a JSON build for class {class_name}.\n\nTEXT:\n" \
             
    return header + text[:16000]

def main():
    files = []
    for d in SAVED_DIRS:
        if not d.exists():
            continue
        for f in d.glob('*.html'):
            files.append(f)

    if not files:
        print('No saved HTML pages found in', SAVED_DIRS)
        return

    for f in files:
        text = extract_text_from_html(f)
        url_hash = f.stem
        prompt = make_prompt(text)
        out_path = OUT_DIR / f"{url_hash}.input.txt"
        out_path.write_text(prompt, encoding='utf-8')
        print('Wrote', out_path, 'len', len(prompt))

if __name__ == '__main__':
    main()
