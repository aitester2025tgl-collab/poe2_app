# poe2_ground_truth_manager.py - GESTOR CENTRAL DO GROUND TRUTH (COM LÓGICA DE TRANSFERÊNCIA)
import json
import os
import logging
import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Set, Tuple, Union
from datetime import datetime
import re 

# Configuração de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('poe2_gt_manager')

# ===== CONFIGURAÇÕES GERAIS =====
REF_DATA_FILE = "poe2_ref_data.json"
BUILD_DATA_FILE = "poe2_builds.json"

# URLs de fontes confiáveis
SKILL_GEMS_URL = "https://poe2db.tw/us/Skill_Gems"
SUPPORT_GEMS_URL = "https://poe2db.tw/us/Support_Gems"

SKILL_KEY = "SKILL_GEMS_ACTIVE"
PASSIVE_KEY = "passives"
SUPPORT_KEY = "SUPPORT_GEMS" 

# Termos irrelevantes que devem ser ignorados
IRRELEVANT_PASSIVE_PHRASES = {
    "N/A", "n/a", "", "Passive Key", "Passive Tree", "Passive", 
    "Chave", "Passiva", "Nenhuma Passiva Chave", "Damage", "Life", 
    "Mana", "Increased", "More", "Less", "Reduced"
}

# ===== CONHECIMENTO MANUAL (BACKUP) =====
MANUAL_SKILLS = {
    # Warrior
    "Boneshatter", "Earthquake", "Shield Charge", "Sunder", "Hammer of the Gods",
    "Rolling Slam", "Armour Break", "Perfect Strike", "Stampede",
    
    # Ranger
    "Lightning Arrow", "Ice Shot", "Gas Arrow", "Vine Arrow", "Fragmentation Rounds",
    "Siege Cascade", "Toxic Growth", "Shockburst Rounds",
    
    # Monk
    "Ice Strike", "Killing Palm", "Tempest Bell", "Falling Thunder",
    "Glacial Cascade", "Wind Blast", "Herald of Ice",
    
    # Mercenary
    "Fragmenting Rounds", "High Velocity Rounds", "Plasma Blast",
    "Explosive Grenade", "Gas Grenade", "Oil Grenade", "Flash Grenade",
    
    # Sorceress
    "Spark", "Fireball", "Arc", "Ice Nova", "Freeze", "Frost Bolt",
    "Flame Wall", "Lightning Bolt", "Firewall", "Frost Bomb",
    
    # Witch
    "Bone Offering", "Raise Zombie", "Summon Skeletons", "Unearth",
    "Profane Ritual", "Detonate Dead", "Raise Spectre",
    
    # Huntress
    "Lightning Spear", "Whirling Assault", "Wind Dancer",
    "Tempest Flurry", "Scattershot", "Herald of Thunder",
    
    # Universal
    "Dash", "Flame Dash", "Frostblink", "Blink", "Portal"
}

MANUAL_PASSIVES = {
    "Resolute Technique", "Unwavering Stance", "Iron Grip", "Iron Reflexes",
    "Point Blank", "Far Shot", "Elemental Overload", "Ancestral Bond",
    "Pain Attunement", "Chaos Inoculation", "Eldritch Battery",
    "Mind Over Matter", "Acrobatics", "Phase Acrobatics",
    "Avatar of Fire", "Blood Magic", "Zealot's Oath",
    "Ghost Reaver", "Vaal Pact", "Perfect Agony"
}

# --- UTILITIES DE FICHEIROS ---
def load_json_file(file_path: str) -> Union[Dict[str, Any], List[Any]]:
    """Carrega dados de um ficheiro JSON, com gestão de erros."""
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        return {} if file_path != BUILD_DATA_FILE else []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            if not content:
                return {} if file_path != BUILD_DATA_FILE else []
            return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"❌ Erro ao analisar JSON em {file_path}: {e}")
        return {} if file_path != BUILD_DATA_FILE else []
    except Exception as e:
        logger.error(f"❌ Erro ao carregar {file_path}: {e}")
        return {} if file_path != BUILD_DATA_FILE else []

def save_json_file(data: Any, file_path: str):
    """Guarda dados num ficheiro JSON."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Ficheiro {file_path} guardado com sucesso.")
    except Exception as e:
        logger.error(f"❌ Erro ao guardar {file_path}: {e}")

# --- FUNÇÕES DE FETCH EXTERNO (poe2db) ---
def fetch_html_content(url: str) -> str:
    """Faz o fetch do conteúdo HTML da URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Erro ao fazer fetch da URL externa ({url}): {e}")
        return None

def extract_skill_names_from_poe2db(html_content: str) -> Set[str]:
    """Extrai nomes de skills da página poe2db usando BeautifulSoup."""
    soup = BeautifulSoup(html_content, 'html.parser')
    skills = set()
    
    # Estratégia: Procurar links e tabelas
    for link in soup.find_all('a'):
        text = link.get_text(strip=True)
        if text and len(text) > 3 and len(text) < 40 and text[0].isupper():
            skills.add(text)
    
    for table in soup.find_all('table'):
        for row in table.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            for cell in cells:
                text = cell.get_text(strip=True)
                if text and 3 < len(text) < 40 and text[0].isupper():
                    skills.add(text)
    
    return skills

def clean_skill_names(raw_names: Set[str]) -> Set[str]:
    """Limpa nomes de skills, removendo lixo."""
    blacklist = {
        'Skill Gems', 'Support Gems', 'Active', 'Support', 'Level', 'Mana Cost',
        'Requirements', 'Quality', 'Description', 'Tags', 'Type', 'View', 'Edit',
        'Home', 'Wiki', 'Page', 'Search', 'Login', 'More', 'Less', 'Increased'
    }
    
    cleaned = set()
    for name in raw_names:
        if name in blacklist or len(name) < 3 or len(name) > 40:
            continue
        # Remove números e strings que são apenas números
        if name[0].isdigit() or name.replace(' ', '').isdigit():
            continue
        
        cleaned.add(name)
    
    return cleaned

# --- FUNÇÕES DE APRENDIZAGEM DE BUILDS (Necessário para extrair passivas, etc.) ---
def load_builds() -> Dict[str, List[Dict[str, Any]]]:
    """Carrega as builds do ficheiro JSON."""
    data = load_json_file(BUILD_DATA_FILE)
    if isinstance(data, dict):
        return data
    return {}

def extract_unique_skills(all_builds: Dict[str, List[Dict[str, Any]]]) -> Set[str]:
    """Extrai todos os nomes únicos de skills das builds."""
    unique_skills: Set[str] = set()

    for class_name, builds in all_builds.items():
        for build in builds:
            if not isinstance(build, dict):
                continue

            for step in build.get('skill_tree_leveling', []):
                for action in step.get('actions', []):
                    skill_name = action.get("name")
                    
                    if action.get("type") == "Skill" and skill_name and isinstance(skill_name, str):
                        unique_skills.add(skill_name.strip())
    
    return unique_skills

def extract_unique_passives(all_builds: Dict[str, List[Dict[str, Any]]]) -> Set[str]:
    """Extrai todos os nomes únicos de passivas das builds."""
    unique_passives: Set[str] = set()

    for class_name, builds in all_builds.items():
        for build in builds:
            if not isinstance(build, dict):
                continue

            for step in build.get('skill_tree_leveling', []):
                for action in step.get('actions', []):
                    passive_list = action.get("passives", [])
                    
                    if isinstance(passive_list, list):
                        for p_name in passive_list:
                            if isinstance(p_name, str):
                                p_name = p_name.strip()
                                if p_name and p_name not in IRRELEVANT_PASSIVE_PHRASES:
                                    unique_passives.add(p_name)
                                
    return unique_passives

# --- FUNÇÕES DE FUSÃO/MERGE ---
def merge_skills(ref_data: Dict[str, Any], new_skills: Set[str]) -> Tuple[Dict[str, Any], int]:
    """Funde novas skills no Ground Truth."""
    
    if SKILL_KEY not in ref_data or not isinstance(ref_data[SKILL_KEY], dict):
        ref_data[SKILL_KEY] = {}
        
    existing_skills: Dict[str, int] = ref_data[SKILL_KEY]
    new_skills_added = 0
    
    for skill_name in new_skills:
        if skill_name not in existing_skills:
            existing_skills[skill_name] = 1 
            new_skills_added += 1
            
    return ref_data, new_skills_added

def merge_passives(ref_data: Dict[str, Any], new_passives: Set[str]) -> Tuple[Dict[str, Any], int]:
    """Funde novas passivas no Ground Truth."""

    if PASSIVE_KEY not in ref_data or not isinstance(ref_data.get(PASSIVE_KEY), list):
        ref_data[PASSIVE_KEY] = []
    
    current_passives_set = set(ref_data[PASSIVE_KEY])
    newly_added_count = 0
    
    for passive in new_passives:
        if passive not in current_passives_set:
            current_passives_set.add(passive)
            newly_added_count += 1
            
    ref_data[PASSIVE_KEY] = sorted(list(current_passives_set))
    
    return ref_data, newly_added_count

# --- FUNÇÃO PRINCIPAL DE ORQUESTRAÇÃO ---
def run_ground_truth_update(force_update: bool = False):
    """
    Executa o pipeline completo de atualização do Ground Truth, incluindo a reclassificação.
    """
    logger.info("=================================================================")
    logger.info("--- ⚙️ INÍCIO DO PIPELINE DE GESTÃO DO GROUND TRUTH ---")
    logger.info("=================================================================")
    
    # 1. OBTENÇÃO DE DADOS EXTERNOS (poe2db)
    logger.info(f"--- 1. Buscando skills de fontes externas ---")
    
    # Carregar dados atuais do GT para fusão (incluindo passivas existentes)
    ref_data = load_json_file(REF_DATA_FILE)
    if not isinstance(ref_data, dict): ref_data = {}
    if PASSIVE_KEY not in ref_data: ref_data[PASSIVE_KEY] = []

    # A. Fetch Skills (Active Gems)
    logger.info(f"   1.1. Buscando de {SKILL_GEMS_URL}")
    html_skills = fetch_html_content(SKILL_GEMS_URL)
    
    external_skills: Set[str] = set()
    if html_skills:
        raw_skills = extract_skill_names_from_poe2db(html_skills)
        external_skills = clean_skill_names(raw_skills)
        logger.info(f"   ✅ {len(external_skills)} Active skills limpas")
    
    # B. Fetch Support Gems (Filtro)
    logger.info(f"   1.2. Buscando de {SUPPORT_GEMS_URL}")
    html_supports = fetch_html_content(SUPPORT_GEMS_URL)
    
    clean_supports: Set[str] = set()
    if html_supports:
        raw_supports = extract_skill_names_from_poe2db(html_supports)
        clean_supports = clean_skill_names(raw_supports)
        logger.info(f"   ✅ {len(clean_supports)} support gems limpas")

    # C. Adicionar conhecimento manual (apenas Active Skills)
    external_skills.update(MANUAL_SKILLS)
    logger.info(f"   ✅ Total de Active Skills potenciais (com manual): {len(external_skills)}")
    
    # -------------------------------------------------------------------
    # ETAPA CRÍTICA: LÓGICA DE TRANSFERÊNCIA (Move-to-Passive)
    # -------------------------------------------------------------------
    
    # Itens a transferir: são Support Gems E estão na lista de Active Skills
    transfer_list = external_skills.intersection(clean_supports)
    skills_transferred_count = 0
    
    logger.info(f"   🔄 {len(transfer_list)} gemas encontradas na lista de Support e Active (Início da reclassificação).")
    
    all_current_passives = MANUAL_PASSIVES.union(set(ref_data.get(PASSIVE_KEY, [])))

    # Reclassificação
    for name in transfer_list:
        # 1. Remover de Active Skills
        if name in external_skills:
            external_skills.remove(name)
        
        # 2. Adicionar à lista de Passives
        if name not in all_current_passives:
            all_current_passives.add(name) 
            skills_transferred_count += 1
            
    logger.info(f"   ✅ {skills_transferred_count} Support Gems reclassificadas como Passives.")
    
    # 2. APRENDIZAGEM A PARTIR DE BUILDS
    logger.info(f"--- 2. A carregar builds de '{BUILD_DATA_FILE}' ---")
    all_builds = load_builds()
    
    learned_skills = extract_unique_skills(all_builds)
    learned_passives = extract_unique_passives(all_builds)
    logger.info(f"   ✅ {len(learned_skills)} Skills e {len(learned_passives)} Passivas extraídas das builds.")

    # 3. FUSÃO NO FICHEIRO DE REFERÊNCIA
    logger.info(f"--- 3. A fundir dados no Ground Truth '{REF_DATA_FILE}' ---")
    
    # A. Fundir SKILLS ATIVAS (Active Skills Reais + Aprendidas)
    all_new_skills = external_skills.union(learned_skills) 
    ref_data, skills_added = merge_skills(ref_data, all_new_skills)
    
    # B. Fundir PASSIVAS (Aprendidas + Manual + Reclassificadas)
    all_passives_to_merge = all_current_passives.union(learned_passives) 
    ref_data, passives_added = merge_passives(ref_data, all_passives_to_merge)
    
    # C. Fundir a lista pura de Support Gems (Para referência/filtro)
    current_support_set = set(ref_data.get(SUPPORT_KEY, []))
    support_added = 0
    for name in clean_supports:
        if name not in current_support_set:
            current_support_set.add(name)
            support_added += 1
    ref_data[SUPPORT_KEY] = sorted(list(current_support_set))

    # Adicionar metadata
    if 'metadata' not in ref_data:
        ref_data['metadata'] = {}
    
    ref_data['metadata']['last_updated'] = datetime.now().isoformat()
    ref_data['metadata']['source'] = 'poe2db.tw + builds + manual'
    ref_data['metadata']['total_skills'] = len(ref_data.get(SKILL_KEY, {}))
    ref_data['metadata']['total_passives'] = len(ref_data.get(PASSIVE_KEY, []))
    ref_data['metadata']['total_support_gems'] = len(ref_data.get(SUPPORT_KEY, []))
    
    # Salvar o Ground Truth final
    save_json_file(ref_data, REF_DATA_FILE)

    logger.info("=================================================================")
    logger.info(f"--- 🥳 PIPELINE CONCLUÍDO ---")
    logger.info(f"   Skills Ativas Reais adicionadas: {skills_added}")
    logger.info(f"   Itens reclassificados (Support->Passive): {skills_transferred_count}")
    logger.info(f"   Total de Active Skills no GT: {len(ref_data.get(SKILL_KEY, {}))}")
    logger.info(f"   Total de Passivas (incl. Supports) no GT: {len(ref_data.get(PASSIVE_KEY, []))}")
    logger.info("=================================================================")

# A execução principal pode ser mantida para testes isolados
if __name__ == '__main__':
    run_ground_truth_update()