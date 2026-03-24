import json
from pathlib import Path

p = Path(__file__).parent.parent / 'data' / 'poe2_builds.json'
print('Reading', p)

data = json.loads(p.read_text(encoding='utf-8'))

for cls in ['Warrior','Monk','Ranger']:
    builds = data.get(cls, [])
    print('\nClass:', cls, 'builds:', len(builds))
    if not builds:
        continue
    b = builds[0]
    print('Build name:', b.get('build_name'))
    print('Step ranges:')
    for step in b.get('skill_tree_leveling', []):
        print(' -', repr(step.get('level_range')))
    
print('\nDone')
