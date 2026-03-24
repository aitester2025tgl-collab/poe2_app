import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF_FILE = ROOT / 'data' / 'poe2_ref_data.json'
OUT_ACTIVE = ROOT / 'data' / 'active_skills.txt'
OUT_PASSIVE = ROOT / 'data' / 'passive_skills.txt'

def main():
    if not REF_FILE.exists():
        print('Reference file not found:', REF_FILE)
        return
    data = json.loads(REF_FILE.read_text(encoding='utf-8'))
    skills = data.get('SKILL_GEMS_ACTIVE', {})
    passives = data.get('passives', [])

    with open(OUT_ACTIVE, 'w', encoding='utf-8') as f:
        for s in sorted(skills.keys()):
            f.write(s + '\n')

    with open(OUT_PASSIVE, 'w', encoding='utf-8') as f:
        # passives may be object list or strings
        if passives and isinstance(passives[0], dict):
            for p in passives:
                name = p.get('name')
                if name:
                    f.write(name + '\n')
        else:
            for p in passives:
                f.write(str(p) + '\n')

    print('Exported', OUT_ACTIVE, 'and', OUT_PASSIVE)

if __name__ == '__main__':
    main()
