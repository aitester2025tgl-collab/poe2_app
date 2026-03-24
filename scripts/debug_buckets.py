import json
import sys
import re
from pathlib import Path
# Ensure project root is on sys.path so imports like `import config` work when running this script
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config

DATA_FILE = Path(config.BUILD_FILE)

def load_builds():
    if not DATA_FILE.exists():
        print(json.dumps({'error': 'build file not found', 'path': str(DATA_FILE)}))
        sys.exit(1)
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def normalize_build_levels(raw):
    buckets = {}
    if config.USE_ACT_BUCKETS:
        for act_label in config.ACT_LEVEL_BUCKETS.keys():
            buckets[act_label] = []

    def add_to_bucket(label, action_item):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(action_item)

    for step in raw.get('skill_tree_leveling', []):
        rng = step.get('level_range', 'Full Leveling')
        actions = []
        for action in step.get('actions', []):
            if action.get('type') == 'Skill':
                actions.append({
                    'skill_name': action.get('name', 'N/A'),
                    'required_level': action.get('level', 0),
                    'passives_acquired': action.get('passives', []) if isinstance(action.get('passives', []), list) else []
                })
        if not actions:
            continue

        placed = False
        act_nums = re.findall(r'Act\s*(\d+)', rng, flags=re.IGNORECASE)
        if act_nums:
            for n in act_nums:
                label = f"Act {int(n)}"
                for skill_item in actions:
                    add_to_bucket(label, skill_item)
            placed = True

        if not placed and config.USE_ACT_BUCKETS:
            m = re.search(r'(\d+)', rng)
            if m:
                lower = int(m.group(1))
                for act_label, (amin, amax) in config.ACT_LEVEL_BUCKETS.items():
                    if amin <= lower <= amax:
                        for skill_item in actions:
                            add_to_bucket(act_label, skill_item)
                        placed = True
                        break

        if not placed:
            for skill_item in actions:
                add_to_bucket(rng, skill_item)

    # Dedup and sort
    for label, skills in list(buckets.items()):
        seen = set()
        unique_skills = []
        for s in skills:
            key = (s.get('skill_name'), s.get('required_level'))
            if key in seen:
                continue
            seen.add(key)
            unique_skills.append(s)
        unique_skills.sort(key=lambda x: (x.get('required_level') or 0))
        buckets[label] = unique_skills

    return buckets

def main():
    cls = sys.argv[1] if len(sys.argv) > 1 else 'Warrior'
    builds = load_builds()
    build_list = builds.get(cls, [])
    if not build_list:
        print(json.dumps({'error': 'no build for class', 'class': cls}))
        return
    raw = build_list[0]
    buckets = normalize_build_levels(raw)
    print(json.dumps({'class': cls, 'buckets': buckets}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
