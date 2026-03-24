from pathlib import Path
import re
import difflib

# Try to import known skills from project reference
try:
    from poe2_data_ref import KNOWN_SKILLS
except Exception:
    KNOWN_SKILLS = set()

p = Path('data/fetched_pages/mobalytics_woolie_live.html')
if not p.exists():
    print('Saved Mobalytics HTML not found at', p)
    raise SystemExit(1)

html = p.read_text(encoding='utf-8')

# Extract the block around 'Support Gem Order' or 'Support Gem Requirements'
m = re.search(r'(SUPPORT GEM ORDER:.*?$|Support Gem Requirements:.*?$)', html, flags=re.I | re.S | re.M)
block = None
if m:
    # take a larger window around the match
    start = max(0, m.start() - 2000)
    end = min(len(html), m.end() + 2000)
    block = html[start:end]
else:
    # fallback: read entire HTML
    block = html

text = re.sub(r'<[^>]+>', ' ', block)
text = re.sub(r'\s+', ' ', text).strip()

print('--- Extracted support-block snippet ---')
print(text[:2000])

# Find parenthesized mappings: 'Name (Primary)'
paren_pairs = re.findall(r"\d+\s*[\)\.]?\s*([^\(\)]+?)\s*\(\s*([^\)]+?)\s*\)", text)
# Also find simple numbered sequence entries like '1 Mace Strike 2 Rolling Slam 3 Boneshatter'
seq_entries = re.findall(r'(?:\d+\s*[\)\.]?\s*)([A-Za-z][A-Za-z0-9\'\- ]+?)(?=(?:\s*\d+\s*[\)\.]?\s*)|$)', text)

print('\nparen pairs found:', paren_pairs)
print('\nseq entries found (sample):', seq_entries[:20])

# canonicalize helper
def canonicalize(name: str) -> str:
    name = (name or '').strip()
    if not name:
        return ''
    if name in KNOWN_SKILLS:
        return name
    for s in KNOWN_SKILLS:
        if s.lower() == name.lower():
            return s
    norm = re.sub(r'[^a-z0-9]', '', name.lower())
    candidates = []
    for s in KNOWN_SKILLS:
        s_norm = re.sub(r'[^a-z0-9]', '', s.lower())
        candidates.append((s, difflib.SequenceMatcher(None, norm, s_norm).ratio()))
    candidates.sort(key=lambda x: x[1], reverse=True)
    if candidates and candidates[0][1] > 0.86:
        return candidates[0][0]
    return name

support_map = {}
for sup, prim in paren_pairs:
    sup_n = sup.strip()
    prim_n = prim.strip()
    prim_c = canonicalize(prim_n)
    sup_c = sup_n
    support_map.setdefault(prim_c, []).append(sup_c)

# If no paren mappings, try to pair seq entries by adjacent pairs (assume alternating primary vs support per format)
if not support_map and seq_entries:
    # The page appears to list skills as sequence where each number corresponds to primary skill name.
    # In many guides the mapping is "1) Mace Strike 2) Rolling Slam 3) Boneshatter ..." which are primaries.
    # For our use, we will print seq entries as candidate primaries in order.
    for i, entry in enumerate(seq_entries):
        entry = entry.strip()
        cand = canonicalize(entry)
        support_map.setdefault(cand, [])

print('\n--- Final support map ---')
for k, v in support_map.items():
    print(f"{k} -> {v}")

if not support_map:
    print('\nNo clear support->primary mappings detected by the heuristic. Consider using the LLM fallback to parse the "SUPPORT GEM ORDER" block.')
