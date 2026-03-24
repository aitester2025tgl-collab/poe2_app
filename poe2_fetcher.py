# poe2_fetcher.py - VERSÃO FINAL: SEGURA E OTIMIZADA
import json
import time
import requests 
import os
from bs4 import BeautifulSoup 
import hashlib
from pathlib import Path
import re
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except Exception:
    # Allow module import even if googleapiclient isn't installed in the current env.
    build = None
    class HttpError(Exception):
        pass
from typing import Dict, Optional, List, Any
import logging
try:
    from ollama import Client
except Exception:
    Client = None
from dotenv import load_dotenv
import difflib
try:
    import json5
except Exception:
    json5 = None

# Ground-truth skills for canonicalization
try:
    from poe2_data_ref import KNOWN_SKILLS
except Exception:
    KNOWN_SKILLS = set()

# Try to reuse shared utilities and configuration from src.data.fetcher to avoid
# duplicating constants and LLM client setup. Fall back to local defaults if import fails.
try:
    from src.data.fetcher import (
        search_google,
        get_page_content,
        load_existing_builds,
        save_builds,
        OLLAMA_CLIENT,
        OLLAMA_MODEL,
        MAX_RETRIES,
        LLM_PROCESSING_LIMIT,
        MAX_BUILDS_PER_CLASS,
        POE2_CLASSES,
        CLASSES_TO_SKIP,
        logger,
    )
except Exception:
    # Minimal fallbacks so this module remains importable in isolation
    try:
        from src.data.fetcher import search_google, get_page_content
    except Exception:
        def search_google(q, num=5):
            return []
        def get_page_content(link):
            return None, None, None

    # local defaults
    OLLAMA_CLIENT = None
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'mistral')
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    LLM_PROCESSING_LIMIT = int(os.getenv('LLM_PROCESSING_LIMIT', '3'))
    MAX_BUILDS_PER_CLASS = int(os.getenv('MAX_BUILDS_PER_CLASS', '10'))
    POE2_CLASSES = ["Warrior", "Monk", "Mercenary", "Sorceress", "Witch", "Ranger", "Huntress", "Druid", "Duelist", "Marauder", "Shadow", "Templar"]
    CLASSES_TO_SKIP = []
    # basic logger
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Ollama temperature (may be provided by src.data.fetcher or config)
try:
    from src.data.fetcher import OLLAMA_TEMPERATURE
except Exception:
    OLLAMA_TEMPERATURE = float(os.getenv('OLLAMA_TEMPERATURE', '0.1'))
# Directories for persisted LLM I/O
try:
    from config import DATA_DIR
    LLM_INPUTS_DIR = Path(DATA_DIR) / 'llm_inputs'
    LLM_RESPONSES_DIR = Path(DATA_DIR) / 'llm_responses'
except Exception:
    LLM_INPUTS_DIR = Path('data') / 'llm_inputs'
    LLM_RESPONSES_DIR = Path('data') / 'llm_responses'

LLM_INPUTS_DIR.mkdir(parents=True, exist_ok=True)
LLM_RESPONSES_DIR.mkdir(parents=True, exist_ok=True)

# Directory to persist discovered support maps for manual review
SUPPORT_MAP_DIR = Path('data') / 'support_maps'
SUPPORT_MAP_DIR.mkdir(parents=True, exist_ok=True)



def extract_leveling_section(soup: BeautifulSoup) -> str:
    """
    Extract only the leveling-relevant DOM regions from a parsed BeautifulSoup page.
    The function collects headings (h2-h4) that mention leveling/level/skill and
    includes the following paragraphs/lists/tables until the next heading of the
    same or higher level. Returns a trimmed string suitable for LLM input.
    """
    if soup is None:
        return ''

    KEYWORDS = ['level', 'leveling', 'level-up', 'lvl', 'skill', 'skills', 'gems', 'act']
    parts = []

    # Look for headings that likely introduce leveling sections
    for h in soup.find_all(['h2', 'h3', 'h4']):
        txt = (h.get_text() or '').lower()
        if any(k in txt for k in KEYWORDS) or re.search(r'\b1[-– to]{1,3}\d+\b', txt):
            # include the heading text
            parts.append(h.get_text(separator=' ', strip=True))

            # walk following siblings until next heading of same/higher level
            for sib in h.find_next_siblings():
                if sib.name and sib.name.startswith('h') and len(sib.name) <= len(h.name):
                    # stop at next heading of same or higher level
                    break

                if sib.name in ('p', 'ul', 'ol', 'div', 'table'):
                    text = sib.get_text(separator=' ', strip=True)
                    # keep only siblings that look relevant: contain digits, level keywords or skill-like words
                    if not text:
                        continue
                    low = text.lower()
                    if (re.search(r'\b\d{1,3}\b', text) or any(k in low for k in KEYWORDS) or re.search(r'[A-Z][a-z]{2,}', text)):
                        parts.append(text)
                else:
                    # also pick inline lists/paragraph-like content
                    text = sib.get_text(separator=' ', strip=True)
                    if text and (any(k in text.lower() for k in KEYWORDS) or re.search(r'\b\d{1,3}\b', text)):
                        parts.append(text)

    # Fallback: if nothing explicitly matched, try scanning for ordered lists that contain 'level' or numbered steps
    if not parts:
        for ol in soup.find_all(['ol', 'ul']):
            txt = ol.get_text(separator=' ', strip=True)
            if 'level' in txt.lower() or re.search(r'\b1\.|\b1\)', txt):
                parts.append(txt)
                # limit to first few lists
                if len(parts) >= 3:
                    break

    trimmed = '\n\n'.join(parts).strip()
    # Keep the trimmed input reasonably bounded
    if len(trimmed) > 16000:
        return trimmed[:16000]
    return trimmed


def extract_build_details_with_llm(build_text: str, class_name: str, url: str) -> Optional[Dict]:
    """
    Usa o LLM (Ollama) para extrair detalhes de build estruturados.
    """
    
    system_prompt = f"""
    Você é um bot de extração de dados altamente preciso. A sua tarefa é analisar o conteúdo de uma build de Path of Exile 2 e extrair informações cruciais APENAS no formato JSON fornecido.

    --- REGRAS DE EXTRAÇÃO OBRIGATÓRIAS ---
    1. ESTRUTURA: A saída DEVE ser um objeto JSON único e bem formado, começando com '{{' e terminando com '}}'.
    2. SKILLS (name): O valor DEVE ser o NOME CANÔNICO EXATO da Skill Ativa (ex: "Boneshatter", "Arc") ou Passiva Chave (ex: "Resolute Technique"). NUNCA use títulos de build, frases irrelevantes ou lixo.
    3. PASSIVES (Lista): O campo 'passives' deve ser uma lista de strings com os nomes exatos das Passivas Notáveis/Keystones. Se não houver, use uma lista vazia ([]).
    4. REQUIRED_LEVEL: O valor DEVE ser um número inteiro (e.g., 1, 12). Se o nível não for explicitamente mencionado, use o número 0.
    5. REPUTATION: Deve ser o número de visualizações/votos. Se não for encontrado, use um valor base de 50000.
    6. LEVEL_RANGE: Divida o nivelamento em fases (ex: '1-10', 'Act 1'). Se não houver informação, use 'Full Leveling'.
    
    A classe desta build é: {class_name}.
    
    Formato de Saída (DEVE ser JSON válido):
    {{
      "build_name": "Nome da Build",
      "class": "{class_name}",
      "version": "0.3",
      "reputation": 50000,
      "skill_tree_leveling": [
        {{
          "level_range": "1-10",
          "actions": [
            {{ "type": "Skill", "name": "Nome da Skill Exato", "level": 1, "passives": ["Passiva Chave 1"] }}
          ]
        }}
      ]
    }}

    TEXTO DA BUILD:
    ---
    {build_text[:8000]}
    ---

    Produz apenas o objeto JSON.
    """
    
    # Persist the exact input we send to the model for debugging
    try:
        input_hash = hashlib.sha1((url + class_name + build_text[:5000]).encode('utf-8')).hexdigest()[:12]
        input_path = LLM_INPUTS_DIR / f"{input_hash}.input.txt"
        input_path.write_text(build_text[:16000], encoding='utf-8')
    except Exception:
        input_hash = None

    for attempt in range(MAX_RETRIES):
        try:
            response = OLLAMA_CLIENT.chat(
                model=OLLAMA_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extraia a build para a classe {class_name}"}
                ],
                format='json',
                options={'temperature': OLLAMA_TEMPERATURE}
            )
            
            json_str = response['message']['content'].strip()
            # Save raw response for inspection
            try:
                if input_hash:
                    resp_path = LLM_RESPONSES_DIR / f"{input_hash}.response.txt"
                    resp_path.write_text(json_str, encoding='utf-8')
            except Exception:
                pass
            
            # Limpeza do output
            if json_str.startswith('```json'):
                json_str = json_str[7:-3].strip()
            elif json_str.startswith('```'):
                json_str = json_str[3:-3].strip()

            # Tentar analisar o JSON
            try:
                build_data = json.loads(json_str)
            except json.JSONDecodeError:
                logger.warning(f"   ⚠️ LLM (Tentativa {attempt+1}): JSON Inválido. Nova tentativa em 2s.")
                time.sleep(2)
                continue
            
            # Validar a estrutura básica
            if 'skill_tree_leveling' in build_data:
                build_data['reputation'] = int(build_data.get('reputation', 50000))
                build_data['class'] = class_name
                build_data['url'] = url
                
                return build_data
            else:
                logger.warning(f"   ⚠️ LLM (Tentativa {attempt+1}): Faltando 'skill_tree_leveling'. Nova tentativa em 2s.")
                time.sleep(2)
                continue
                
        except Exception as e:
            logger.error(f"❌ Erro na comunicação ou API do Ollama (Tentativa {attempt+1}): {e}. Nova tentativa em 5s.")
            time.sleep(5)
            continue

    logger.error(f"❌ Falha persistente na extração do LLM após {MAX_RETRIES} tentativas.")
    return None


def parse_maxroll(soup, url) -> Optional[Dict]:
    """Try to parse Maxroll guide pages for leveling sections.
    Returns a partial build dict or None if parsing failed.
    """
    try:
        # Prefer explicit 'leveling' sections
        candidates = []
        for h in soup.find_all(['h2', 'h3', 'h4']):
            txt = (h.get_text() or '').lower()
            hid = (h.get('id') or '').lower()
            # Prefer headings that mention level/leveling or explicit Act headers
            if ('level' in txt or 'leveling' in txt or 'act' in txt
                    or re.search(r'\b1-\d+\b', txt)
                    or re.search(r'act-?\d', hid)):
                candidates.append(h)

        steps = []
        for h in candidates:
            # collect siblings until the next heading
            for sib in h.find_next_siblings():
                if sib.name and sib.name.startswith('h'):
                    break
                if sib.name in ('ul', 'ol'):
                    for li in sib.find_all('li'):
                        # prefer semantic poe2-item / poe2-passive spans when present
                        item_spans = li.find_all('span', class_=lambda c: c and 'poe2-item' in c)
                        passive_spans = li.find_all('span', class_=lambda c: c and 'poe2-passive' in c)
                        if item_spans:
                            names = [s.get_text(separator=' ', strip=True) for s in item_spans]
                            steps.append(' | '.join(names))
                        elif passive_spans:
                            names = [p.get_text(separator=' ', strip=True) for p in passive_spans]
                            steps.append(' | '.join(names))
                        else:
                            text = li.get_text(separator=' ', strip=True)
                            if text:
                                steps.append(text)
                elif sib.name in ('p', 'div'):
                    text = sib.get_text(separator=' ', strip=True)
                    if text:
                        steps.append(text)

        # Fallback: if nothing found, try to pick ordered lists that contain numbers or 'level'
        if not steps:
            for ol in soup.find_all(['ol', 'ul']):
                txt = ol.get_text(separator=' ', strip=True)
                if 'level' in txt.lower() or re.search(r'\b1\.|\b1\)', txt):
                    for li in ol.find_all('li'):
                        t = li.get_text(separator=' ', strip=True)
                        if t:
                            steps.append(t)
                    if steps:
                        break

        if not steps:
            return None

        # Helper: canonicalize skill names using KNOWN_SKILLS with fuzzy matching
        def canonicalize_skill(name: str) -> str:
            name = name.strip()
            if not name:
                return ''
            # quick exact match
            if name in KNOWN_SKILLS:
                return name
            # try case-insensitive exact
            for s in KNOWN_SKILLS:
                if s.lower() == name.lower():
                    return s
            # fuzzy match on short normalized forms
            norm = re.sub(r'[^a-z0-9]', '', name.lower())
            candidates = []
            for s in KNOWN_SKILLS:
                s_norm = re.sub(r'[^a-z0-9]', '', s.lower())
                candidates.append((s, difflib.SequenceMatcher(None, norm, s_norm).ratio()))
            candidates.sort(key=lambda x: x[1], reverse=True)
            if candidates and candidates[0][1] > 0.8:
                return candidates[0][0]
            return name

        # persist discovered support maps for manual inspection (non-fatal)
        try:
            map_hash = hashlib.sha1((url or '').encode('utf-8')).hexdigest()[:10]
            out_path = SUPPORT_MAP_DIR / f"{map_hash}.json"
            json.dump({'url': url, 'embedded': embedded_map, 'heuristic': heur_map}, out_path.open('w', encoding='utf-8'), ensure_ascii=False, indent=2)
        except Exception:
            pass

        actions = []
        for s in steps:
            # Try explicit patterns: 'Level 6: Use X' or 'At level 6 use X'
            m = re.search(r'level\s*(?:is\s*)?(\d{1,3})', s, flags=re.I)
            level = int(m.group(1)) if m else 0

            # Extract candidate skill names from the text: look for quoted names or capitalized phrases
            # Prefer quoted or parentheses content first
            found = []
            q = re.findall(r'"([^"]{2,60})"', s)
            if q:
                found.extend(q)
            par = re.findall(r"\(([A-Za-z0-9 '\-]{2,60})\)", s)
            if par:
                found.extend(par)

            if not found:
                caps = re.findall(r'([A-Z][a-z][a-zA-Z0-9\'\- ]{1,40})', s)
                if caps:
                    found.extend(caps[:2])

            for name in found[:3]:
                cname = canonicalize_skill(name)
                actions.append({'type': 'Skill', 'name': cname, 'level': level, 'passives': []})

        if not actions:
            return None

        return {
            'build_name': soup.find('title').get_text() if soup.find('title') else 'Maxroll Build',
            'class': '',
            'version': '0.2',
            'reputation': 50000,
            'skill_tree_leveling': [
                {'level_range': '1-10', 'actions': actions}
            ],
            'url': url
        }
    except Exception:
        return None


def parse_mobalytics(soup, url, attach_supports: str = 'embedded') -> Optional[Dict]:
    """Try to parse Mobalytics guide pages for leveling sections.
    Returns a partial build dict or None.
    """
    try:
        # Quick textual check to avoid heavy parsing when irrelevant
        text = (soup.get_text(separator=' ', strip=True) or '')
        if 'leveling' not in text.lower() and 'level' not in text.lower():
            return None

        # Collect candidate containers: div/section/article/ol/ul that mention 'level' or contain numbered lists
        candidates = []
        for tag in soup.find_all(['div', 'section', 'article', 'ol', 'ul']):
            tag_text = (tag.get_text(separator=' ', strip=True) or '').lower()
            cls = ' '.join(tag.get('class') or [])
            if 'level' in tag_text or 'level' in cls.lower() or re.search(r'\b1\.|\b1\)', tag_text):
                candidates.append(tag)

        steps = []
        for c in candidates:
            for li in c.find_all('li'):
                t = li.get_text(separator=' ', strip=True)
                if t and len(t) > 3:
                    steps.append(t)
            for p in c.find_all('p'):
                t = p.get_text(separator=' ', strip=True)
                if t and len(t) > 3:
                    steps.append(t)

        # Fallback: scan whole page for useful list items
        if not steps:
            for li in soup.find_all('li'):
                t = li.get_text(separator=' ', strip=True)
                if t and len(t) > 3 and ('level' in t.lower() or re.search(r'\b1\.|\b1\)', t)):
                    steps.append(t)
                if len(steps) >= 30:
                    break

        if not steps:
            return None

        # Internal canonicalization helper (same logic as in parse_maxroll)
        def canonicalize_skill(name: str) -> str:
            name = (name or '').strip()
            if not name:
                return ''
            if name in KNOWN_SKILLS:
                return name
            for s in KNOWN_SKILLS:
                if s.lower() == name.lower():
                    return s
            norm = re.sub(r'[^a-z0-9]', '', name.lower())
            candidates2 = []
            for s in KNOWN_SKILLS:
                s_norm = re.sub(r'[^a-z0-9]', '', s.lower())
                candidates2.append((s, difflib.SequenceMatcher(None, norm, s_norm).ratio()))
            candidates2.sort(key=lambda x: x[1], reverse=True)
            # Use a stricter threshold for mobalytics matching to avoid false positives
            if candidates2 and candidates2[0][1] > 0.86:
                return candidates2[0][0]
            return name

        # First, try to detect a 'Support Gem' section that maps support gems to primary skills
        # We separate embedded (explicit) mappings from heuristic (inferred via regex/tables)
        embedded_map = {}  # primary_skill_name -> [support_names] (from embedded payload)
        heur_map = {}      # primary_skill_name -> [support_names] (from regex heuristics)
        try:
            # Fast path: Mobalytics often embeds a JSON-like document in the page containing
            # 'skillGems' structures. Try to locate and parse that before using brittle regexes.
            page_text = soup.prettify() if soup else ''

            def _try_parse_json_candidate(candidate: str) -> Optional[dict]:
                # Try strict JSON first, then json5 (if available), then a naive sanitizer
                try:
                    return json.loads(candidate)
                except Exception:
                    pass

                if json5 is not None:
                    try:
                        return json5.loads(candidate)
                    except Exception:
                        pass

                # Sanitize common JS-to-JSON issues: single quotes -> double, remove trailing commas,
                # quote unquoted object keys (very naive), then try json.loads again.
                try:
                    s = candidate
                    # remove newlines that might break simple heuristics
                    s = re.sub(r"\\n", " ", s)
                    # remove JS comments
                    s = re.sub(r"//.*?$", "", s, flags=re.MULTILINE)
                    s = re.sub(r"/\*.*?\*/", "", s, flags=re.DOTALL)
                    # convert single-quoted strings to double-quoted
                    s = re.sub(r"'([^'\\]*(?:\\.[^'\\]*)*)'", r'"\1"', s)
                    # remove trailing commas before } or ]
                    s = re.sub(r",\s*([}\]])", r"\1", s)
                    # attempt to quote unquoted keys: { key:  -> { "key":
                    s = re.sub(r"([,{\s])([a-zA-Z0-9_\-]+)\s*:\s*", r'\1"\2": ', s)
                    return json.loads(s)
                except Exception:
                    return None


            def _extract_json_object_around_key(text: str, key: str) -> Optional[dict]:
                # Look for the key and then expand to a balanced-brace JSON object
                idx = text.find(f'"{key}"')
                if idx == -1:
                    idx = text.find(key)
                if idx == -1:
                    return None

                # Walk backward to find the opening brace '{'
                start = text.rfind('{', 0, idx)
                if start == -1:
                    return None

                # Now walk forward to find the matching closing brace
                depth = 0
                end = None
                for i in range(start, len(text)):
                    if text[i] == '{':
                        depth += 1
                    elif text[i] == '}':
                        depth -= 1
                        if depth == 0:
                            end = i + 1
                            break
                if end is None:
                    return None

                candidate = text[start:end]
                # Try to clean and parse the candidate JSON with tolerant logic
                parsed = _try_parse_json_candidate(candidate)
                if parsed is not None:
                    return parsed

                # If that fails, try a smaller window around the key and attempt tolerant parsing
                try:
                    sub_start = max(start, idx - 2000)
                    sub_end = min(len(text), idx + 2000)
                    sub = text[sub_start:sub_end]
                    s2 = sub.find('{')
                    e2 = sub.rfind('}')
                    if s2 != -1 and e2 != -1 and e2 > s2:
                        return _try_parse_json_candidate(sub[s2:e2+1])
                except Exception:
                    return None
                return None

            parsed_embedded = _extract_json_object_around_key(page_text, 'skillGems')
            # If the quick balanced-braces search didn't find a parsable object,
            # try scanning <script> tags which often contain embedded JSON/JS payloads.
            if not parsed_embedded:
                for script in soup.find_all('script'):
                    try:
                        txt = script.string or script.get_text() or ''
                    except Exception:
                        txt = script.get_text() if script else ''
                    if not txt or 'skillGems' not in txt:
                        continue
                    parsed_embedded = _extract_json_object_around_key(txt, 'skillGems')
                    if parsed_embedded:
                        break

            if parsed_embedded:
                # Drill down to skillGems if present
                def _build_map_from_embedded(doc: dict):
                    local_map = {}
                    try:
                        # Recursive search for gem-slot-like structures inside variable payload shapes.
                        def find_slots(obj):
                            slots = []
                            if isinstance(obj, dict):
                                # heuristics: a slot often has 'activeSkill' or 'active' and optional 'subSkills' or 'gems'
                                if ('activeSkill' in obj or 'active' in obj) and ('subSkills' in obj or 'gems' in obj):
                                    slots.append(obj)
                                for v in obj.values():
                                    slots.extend(find_slots(v))
                            elif isinstance(obj, list):
                                for item in obj:
                                    slots.extend(find_slots(item))
                            return slots

                        slots = find_slots(doc)
                        for slot in slots:
                            try:
                                active = slot.get('activeSkill') or slot.get('active') or slot.get('activeSkillName') or {}
                                active_name = None
                                if isinstance(active, dict):
                                    active_name = active.get('name') or active.get('label') or active.get('gemName')
                                elif isinstance(active, str):
                                    active_name = active
                                if not active_name:
                                    # try top-level fields
                                    active_name = slot.get('name') or slot.get('label') or slot.get('gemName')
                                if not active_name:
                                    continue
                                subs = slot.get('subSkills') or slot.get('sub') or []
                                supports = []
                                if isinstance(subs, list):
                                    for s in subs:
                                        if isinstance(s, dict):
                                            sname = s.get('name') or s.get('label') or s.get('gemName')
                                        else:
                                            sname = s
                                        if sname:
                                            supports.append(sname)
                                # Some payloads embed supports as strings in other fields
                                if not supports:
                                    for k in ('supports','supportGems','support'):
                                        if k in slot:
                                            val = slot.get(k)
                                            if isinstance(val, list):
                                                for s in val:
                                                    supports.append(s if isinstance(s, str) else (s.get('name') if isinstance(s, dict) else None))
                                if supports:
                                    local_map[active_name] = [s for s in supports if s]
                            except Exception:
                                continue
                        return local_map
                    except Exception:
                        return {}

                try:
                    emb_map = _build_map_from_embedded(parsed_embedded)
                    # canonicalize names using existing helper and populate embedded_map
                    for prim, sups in emb_map.items():
                        prim_c = prim
                        try:
                            prim_c = re.sub(r'\s+', ' ', prim).strip()
                            prim_c = canonicalize_skill(prim_c)
                        except Exception:
                            pass
                        embedded_map.setdefault(prim_c, [])
                        for s in sups:
                            try:
                                sc = re.sub(r'\s+', ' ', s).strip()
                                sc = canonicalize_skill(sc)
                            except Exception:
                                sc = s
                            if sc and sc not in embedded_map[prim_c]:
                                embedded_map[prim_c].append(sc)
                except Exception:
                    pass
                # Debug: log the discovered embedded_map (small sample)
            try:
                if embedded_map:
                    logger.info(f"   ℹ️ Mobalytics embedded support keys: {list(embedded_map.keys())[:12]}")
            except Exception:
                pass

            # Fallback: if we still have no embedded_map, try a direct regex scan on the raw HTML
            # for patterns like '1) Concentrated Area ( Mace Strike )' or 'SUPPORT GEM ORDER:' blocks.
            try:
                if not embedded_map:
                    raw_html = str(soup)
                    low = raw_html.lower()
                    search_terms = ['support gem order', 'support gem', 'support gems', 'support gem order:']
                    idx = -1
                    for term in search_terms:
                        idx = low.find(term)
                        if idx != -1:
                            break
                    if idx != -1:
                        snippet = raw_html[max(0, idx-400): idx+3000]
                        # find parenthesized pairs: 'SupportName (PrimarySkill)'
                        pairs = re.findall(r"([A-Za-z0-9\- '&]+?)\s*\(\s*([A-Za-z0-9\- '&]+?)\s*\)", snippet)
                        if pairs:
                            for sup_name, prim_name in pairs:
                                try:
                                    prim_c = canonicalize_skill(prim_name.strip())
                                    sup_c = canonicalize_skill(sup_name.strip())
                                    if prim_c and sup_c:
                                        heur_map.setdefault(prim_c, []).append(sup_c)
                                except Exception:
                                    continue
            except Exception:
                pass

            # If we didn't find an embedded doc above, continue with existing heuristics below
            # Look for headings or bold text that mention 'support' or 'SUPPORT GEM'
            support_headers = []
            for h in soup.find_all(['h2', 'h3', 'h4', 'strong', 'b']):
                t = (h.get_text() or '').lower()
                if 'support gem' in t or 'support gems' in t or 'support gem order' in t or 'support' == t.strip().lower():
                    support_headers.append(h)

            # For each candidate header try to read the following list items
            for h in support_headers:
                # find sibling lists or numbered paragraphs
                # Prefer searching in the header's parent block (site-specific heuristic for Mobalytics)
                parent = h.find_parent()
                search_blocks = []
                if parent is not None:
                    search_blocks.append(parent)
                    # also include a few levels up if available
                    gp = parent.find_parent()
                    if gp is not None:
                        search_blocks.append(gp)

                # Fallback to checking immediate siblings
                search_blocks.extend(h.find_next_siblings(limit=6))

                for sib in search_blocks:
                    if sib.name in ('ol', 'ul'):
                        for li in sib.find_all('li'):
                            text = li.get_text(separator=' ', strip=True)
                            # Pattern like: '1) Concentrated Area (Mace Strike)'
                            m = re.match(r'\s*\d+\s*[\)\.]?\s*(.+?)\s*\(\s*(.+?)\s*\)\s*$', text)
                            if m:
                                support_name = m.group(1).strip()
                                primary = m.group(2).strip()
                                primary_c = canonicalize_skill(primary)
                                support_c = canonicalize_skill(support_name)
                                heur_map.setdefault(primary_c, []).append(support_c)
                    # also consider paragraphs containing 'SUPPORT GEM ORDER' and following plain text numbering
                    if sib.name == 'p' or sib.name == 'div':
                        txt = sib.get_text(separator=' ', strip=True)
                        # split by lines and attempt to parse numbered entries with parentheses first
                        for line in txt.splitlines():
                            # pattern: '1) SupportName (PrimarySkill)'
                            m2 = re.match(r'\s*\d+\s*[\)\.]?\s*(.+?)\s*\(\s*(.+?)\s*\)\s*$', line)
                            if m2:
                                support_name = m2.group(1).strip()
                                primary = m2.group(2).strip()
                                primary_c = canonicalize_skill(primary)
                                support_c = canonicalize_skill(support_name)
                                heur_map.setdefault(primary_c, []).append(support_c)
                                continue
                            # fallback: pattern like '1 mace strike 2 rolling slam 3 boneshatter'
                            seq_matches = re.findall(r'\d+\s*\)?\s*([A-Za-z][A-Za-z0-9\'\- ]+?)(?=(?:\s*\d+\s*\)?\s*)|$)', line)
                            if seq_matches:
                                # seq_matches contains candidate names; try to see if any have parentheses
                                for entry in seq_matches:
                                    entry = entry.strip()
                                    # if entry contains parentheses, split
                                    par = re.match(r'(.+?)\s*\((.+?)\)', entry)
                                    if par:
                                        maybe_support = par.group(1).strip()
                                        maybe_primary = par.group(2).strip()
                                        primary_c = canonicalize_skill(maybe_primary)
                                        support_c = canonicalize_skill(maybe_support)
                                        heur_map.setdefault(primary_c, []).append(support_c)
                                    else:
                                        # if the entry fuzzily matches a known skill, mark as primary with no explicit support
                                        cand = canonicalize_skill(entry)
                                        if cand in KNOWN_SKILLS:
                                            heur_map.setdefault(cand, [])
            # Heuristic: also look for tables where the first column is a support and the second column notes the primary skill
            for table in soup.find_all('table'):
                try:
                    rows = table.find_all('tr')
                    for r in rows:
                        cols = [c.get_text(separator=' ', strip=True) for c in r.find_all(['td','th'])]
                        if len(cols) >= 2:
                            left, right = cols[0], cols[1]
                            # If left mentions 'support' keywords or right contains a known skill
                            if 'support' in left.lower() or any(k in left.lower() for k in ('support gem','support')):
                                # try to extract primary skill name from right (parentheses or capitalized phrase)
                                par = re.findall(r"\(([A-Za-z0-9 '\-]{2,80})\)", right)
                                primary = par[0] if par else right
                                primary_c = canonicalize_skill(primary)
                                support_c = canonicalize_skill(left)
                                heur_map.setdefault(primary_c, []).append(support_c)
                except Exception:
                    pass
        except Exception:
            # non-fatal: if support parsing fails, continue with best-effort steps
            embedded_map = {}
            heur_map = {}

        actions = []
        for s in steps:
            # Extract explicit level if present
            m = re.search(r'level\s*(?:is\s*)?(\d{1,3})', s, flags=re.I)
            level = int(m.group(1)) if m else 0

            # If the LI contains semantic spans, prefer them
            # We may have saved steps as 'name1 | name2' when spans were present
            parts = [p.strip() for p in s.split('|')] if '|' in s else [s]
            for part in parts:
                # try to extract quoted/parenthesized names first
                found = []
                q = re.findall(r'"([^\"]{2,60})"', part)
                if q:
                    found.extend(q)
                par = re.findall(r"\(([A-Za-z0-9 '\-]{2,60})\)", part)
                if par:
                    found.extend(par)

                # Also capture sequences like 'use X & Y' or 'weave in A + B'
                if not found:
                    amp = re.split(r'\s*[&+]\s*| and |, ', part)
                    if len(amp) > 1:
                        found.extend([a.strip() for a in amp if a.strip()])

                if not found:
                    caps = re.findall(r"([A-Z][a-z][a-zA-Z0-9'\- ]{1,40})", part)
                    if caps:
                        found.extend(caps[:3])

                for name in found[:3]:
                    cname = canonicalize_skill(name)
                    # attach supports conservatively depending on attach_supports
                    attached_supports = []
                    try:
                        if attach_supports == 'embedded':
                            attached_supports = embedded_map.get(cname, [])
                        elif attach_supports == 'heuristic':
                            attached_supports = heur_map.get(cname, [])
                        elif attach_supports in (True, 'both'):
                            # merge embedded + heuristic (deduplicated)
                            attached_supports = list(dict.fromkeys((embedded_map.get(cname, []) or []) + (heur_map.get(cname, []) or [])))
                    except Exception:
                        attached_supports = []

                    # Also attempt to detect inline supports in the same LI (e.g., 'Use Earthquake + Fist of War I')
                    # Inline detection is treated as heuristic — only enabled when heuristics are allowed
                    inline_supports = []
                    if attach_supports != 'embedded':
                        try:
                            # look for patterns like 'Skill (Support A, Support B)' or 'Skill + Support'
                            par_inline = re.findall(r"\(([^\)]+support[^\)]*)\)", s, flags=re.I)
                            for pi in par_inline:
                                # split by commas/and/&
                                for sp in re.split(r',| and |&|\+', pi):
                                    spn = sp.strip()
                                    if spn:
                                        inline_supports.append(canonicalize_skill(spn))
                        except Exception:
                            pass

                    supports = list(dict.fromkeys((attached_supports or []) + inline_supports))
                    actions.append({'type': 'Skill', 'name': cname, 'level': level, 'passives': supports})

        if not actions:
            return None

        return {
            'build_name': soup.find('title').get_text() if soup.find('title') else 'Mobalytics Build',
            'class': '',
            'version': '0.2',
            'reputation': 50000,
            'skill_tree_leveling': [
                {'level_range': '1-10', 'actions': actions}
            ],
            'url': url
        }
    except Exception:
        return None


def fetch_build_for_class(class_name, existing_builds: List[Dict]):
    logger.info(f"--- Processando {class_name} ---") 
    
    # Coletar URLs de builds que já foram processadas
    existing_urls = {build.get('url') for build in existing_builds if build.get('url')}

    query = f"Path of Exile 2 {class_name} best leveling build site:maxroll.gg OR site:mobalytics.gg"
    
    search_results = search_google(query, num=MAX_BUILDS_PER_CLASS)

    newly_extracted_builds: List[Dict] = []
    
    time.sleep(2) 
    
    if search_results:
        unprocessed_links = []

        # Filtrar: Encontrar links novos e evitar páginas de índice/listagem
        def is_listing_result(item):
            title = (item.get('title') or '').lower()
            link = (item.get('link') or '').lower()
            # Common words that indicate an index or collection page
            listing_terms = ['builds', 'starter', 'guides', 'best builds', 'build list']
            if any(term in title for term in listing_terms):
                return True
            # Specific path heuristic: direct '/builds' pages or shallow '/builds/' paths
            if link.endswith('/builds'):
                return True
            if '/builds/' in link and link.count('/') <= 4:
                return True
            return False

        # Filtrar: Encontrar links novos
        for result in search_results:
            link = result["link"]
            if link in existing_urls:
                continue
            if is_listing_result(result):
                logger.info(f"   ℹ️ Skip listing/index page: {link}")
                continue
            unprocessed_links.append(result)
        
        # Limitar: Processar apenas os top X links novos
        links_to_process = unprocessed_links[:LLM_PROCESSING_LIMIT]
        
        logger.info(f"   ✅ {len(search_results)} links encontrados. {len(existing_urls)} já processados. Processando {len(links_to_process)} novos.")

        if not links_to_process:
            logger.info(f"   ℹ️ Todos os links para {class_name} já foram processados.")
            return []

        for i, result in enumerate(links_to_process):
            link = result["link"]

            page_text, title, soup = get_page_content(link)

            build_data = None
            # Try site-specific deterministic parsers first
            try:
                if 'maxroll.gg' in link and soup is not None:
                    build_data = parse_maxroll(soup, link)
                elif 'mobalytics.gg' in link and soup is not None:
                    build_data = parse_mobalytics(soup, link)
            except Exception as e:
                logger.debug(f"   ℹ️ site-parser error for {link}: {e}")

            if build_data:
                newly_extracted_builds.append(build_data)
                logger.info(f"   🎉 (parser) Build '{build_data.get('build_name', 'N/A')}' extraída com sucesso.")
            else:
                # Fall back to LLM extraction. Trim the page to the leveling-relevant region
                if page_text and soup is not None:
                    try:
                        trimmed = extract_leveling_section(soup)
                        use_text = trimmed if trimmed and len(trimmed) > 120 else page_text
                    except Exception:
                        use_text = page_text

                    build_data = extract_build_details_with_llm(use_text, class_name, link)
                    if build_data:
                        newly_extracted_builds.append(build_data)
                        logger.info(f"   🎉 (LLM) Build '{build_data.get('build_name', 'N/A')}' extraída com sucesso.")
                    else:
                        logger.warning(f"   ❌ LLM falhou ao extrair dados para {link}.")

            time.sleep(5) 
            
    else:
        logger.warning(f"⚠️ Nenhuma busca retornou resultados para {class_name}.")
        
    return newly_extracted_builds

def update_all_builds():
    logger.info("INFO:__main__:Starting online build update...")
    data = load_existing_builds() 
    success_count = 0
    
    for cls in POE2_CLASSES:
        existing_builds = data.get(cls, [])
        
        # Filtro de classes
        if cls in CLASSES_TO_SKIP:
            logger.info(f"--- Pulando {cls} (Classe não lançada/baixa confiança) ---")
            if cls not in data:
                 data[cls] = []
            continue
        
        new_builds = fetch_build_for_class(cls, existing_builds) 
        
        # Merge: Fundir novas e antigas
        all_builds_dict = {build.get('url'): build for build in existing_builds}
        for build in new_builds:
             all_builds_dict[build.get('url')] = build
             
        combined_builds = list(all_builds_dict.values())
        
        # Ordenar pela reputação
        combined_builds.sort(key=lambda b: b.get('reputation', 0), reverse=True)
        
        # Manter apenas o Top 10
        final_builds = combined_builds[:MAX_BUILDS_PER_CLASS]
        
        data[cls] = final_builds 
        success_count += 1
        
    save_builds(data)
    logger.info(f"✅ Atualização do JSON terminada. {success_count}/{len(POE2_CLASSES)} classes processadas.")
    return True

if __name__ == "__main__":
    update_all_builds()