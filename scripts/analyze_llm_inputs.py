import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / 'data' / 'llm_inputs'

def analyze():
    files = sorted(IN_DIR.glob('*.txt'))
    if not files:
        print('No llm input files found in', IN_DIR)
        return

    lengths = []
    has_level = 0
    has_skill = 0
    samples = []

    for f in files:
        txt = f.read_text(encoding='utf-8', errors='ignore')
        L = len(txt)
        lengths.append(L)
        if 'level' in txt.lower():
            has_level += 1
        if 'skill' in txt.lower() or 'skills' in txt.lower():
            has_skill += 1
        if len(samples) < 5:
            samples.append({'file': f.name, 'len': L, 'snippet': txt[:400].replace('\n',' ')})

    print('Files:', len(files))
    print('Min/Max/Mean/Median len:', min(lengths), max(lengths), int(statistics.mean(lengths)), int(statistics.median(lengths)))
    print('Contain "level":', has_level, f'({has_level/len(files):.1%})')
    print('Contain "skill":', has_skill, f'({has_skill/len(files):.1%})')
    print('\nSamples:')
    for s in samples:
        print('-', s['file'], 'len', s['len'])
        print('  ', s['snippet'])
        print()

if __name__ == '__main__':
    analyze()
