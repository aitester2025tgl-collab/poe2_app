# poe2_data_ref.py - Ground Truth (GT) e Lógica de Validação de Qualidade
import json
import os
import logging
from typing import Set, Dict, Any, List, Tuple

logger = logging.getLogger('poe2_data_ref')
logger.setLevel(logging.INFO) 

# --- CONFIGURAÇÃO CRÍTICA DO CAMINHO DO FICHEIRO ---\r\n
# Este ficheiro DEVE ser o que é ATUALIZADO pelo 'poe2_ref_passive_merger.py' e 'poe2_ref_merger.py'.
REFERENCE_FILE = "poe2_ref_data.json" 

# Variáveis de cache para as listas de Ground Truth
KNOWN_SKILLS: Set[str] = set()
KNOWN_PASSIVES: Set[str] = set()
ALL_REF_DATA: Dict[str, Any] = {}

# --- UTILIDADES DE CARREGAMENTO DE DADOS GT ---\r\n

def extract_passive_names(passives_list: List[Any]) -> Set[str]:
    """
    Extrai nomes de passivas, sendo robusto a dois formatos possíveis:
    1. Lista de objetos com a chave 'name' (formato original).
    2. Lista de strings (formato provável após a fusão/aprendizagem).
    """
    if not passives_list:
        return set()

    # Verifica o tipo do primeiro elemento para inferir o formato
    first_element = passives_list[0]
    
    if isinstance(first_element, dict):
        return {p.get('name', '').strip() for p in passives_list if p.get('name')}
    
    # Assume que é uma lista de strings
    return {str(p).strip() for p in passives_list if p}


def load_reference_data(file_path: str = REFERENCE_FILE):
    """Carrega os dados de referência das Skills e Passivas."""
    global KNOWN_SKILLS, KNOWN_PASSIVES, ALL_REF_DATA
    
    if not os.path.exists(file_path):
        logger.warning(f"⚠️ FICHEIRO CRÍTICO NÃO ENCONTRADO: {file_path}. A validação será ignorada (sets vazios).")
        return
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            ALL_REF_DATA = json.load(f)
            
        # 1. Carregar SKILLS (chave: SKILL_GEMS_ACTIVE)
        # O ficheiro de referência deve ter um dicionário {nome_skill: nível_minimo}
        skills_dict = ALL_REF_DATA.get('SKILL_GEMS_ACTIVE', {})
        KNOWN_SKILLS = {s.strip() for s in skills_dict.keys()}
        
        # 2. Carregar PASSIVAS (chave: passives)
        # O ficheiro de referência deve ter uma lista de nomes de passivas
        passives_list = ALL_REF_DATA.get('passives', [])
        KNOWN_PASSIVES = extract_passive_names(passives_list)
        
        logger.info(f"✅ Dados de referência carregados: {len(KNOWN_SKILLS)} Skills e {len(KNOWN_PASSIVES)} Passivas.")

    except Exception as e:
        logger.error(f"❌ Erro ao carregar dados de referência: {e}")
        # Em caso de falha, garante que os sets estão vazios para desativar a validação
        KNOWN_SKILLS = set()
        KNOWN_PASSIVES = set()

# --- FUNÇÕES DE VALIDAÇÃO DE REFERÊNCIA SIMPLES ---

def is_skill_valid(skill_name: str, required_level: int) -> bool:
    """Verifica se o nome da skill está no Ground Truth (GT)."""
    return skill_name.strip() in KNOWN_SKILLS

def is_passive_name_valid(passive_name: str) -> bool:
    """Verifica se o nome da passiva está no Ground Truth (GT)."""
    return passive_name.strip() in KNOWN_PASSIVES

# --- FUNÇÕES DE EXTRAÇÃO DE DADOS DA BUILD (MOVIDAS DO PARSER) ---

def get_all_extracted_passives(build: Dict[str, Any]) -> Set[str]:
    """Retorna um Set com todos os nomes de passivas extraídos da build."""
    passives: Set[str] = set()
    leveling_steps = build.get('skill_tree_leveling', [])
    for step in leveling_steps:
        for action in step.get('actions', []):
            # O nome da build está agora na chave 'name' e as passivas em 'passives'
            for p_name in action.get('passives', []):
                if isinstance(p_name, str) and p_name.strip():
                    passives.add(p_name.strip())
    return passives

def get_all_extracted_skills(build: Dict[str, Any]) -> Set[str]:
    """Retorna um Set com todos os nomes de skills extraídos da build."""
    skills: Set[str] = set()
    leveling_steps = build.get('skill_tree_leveling', [])
    for step in leveling_steps:
        for action in step.get('actions', []):
            if action.get('type') == 'Skill':
                skill_name = action.get('name')
                if isinstance(skill_name, str) and skill_name.strip():
                    skills.add(skill_name.strip())
    return skills

def get_build_confidence(build: Dict[str, Any]) -> Tuple[float, int, int, int]:
    """
    Calcula o nível de confiança e o número de skills.
    Retorna: (Confiança (float), Total de Nomes Extraídos Conhecidos (int), Total de Nomes Extraídos (int), Total de Skills Únicas (int))
    """
    # 1. Obter todos os nomes de skills e passivas extraídos
    extracted_skills = get_all_extracted_skills(build)
    extracted_passives = get_all_extracted_passives(build)
    
    # Combinar todos os nomes a serem validados
    all_extracted_names: Set[str] = extracted_skills.union(extracted_passives)
    total_extracted_count = len(all_extracted_names)
    
    # 2. Contar quantos destes nomes estão no Ground Truth (KNOWN_SKILLS/KNOWN_PASSIVES)
    known_extracted_count = 0
    
    for name in all_extracted_names:
        # Verifica se o nome é uma skill OU uma passiva
        is_known = is_skill_valid(name, 1) or is_passive_name_valid(name)
        if is_known:
            known_extracted_count += 1
            
    # 3. Calcular Confiança
    # Se nada foi extraído, a confiança é 0.0 para evitar ZeroDivisionError
    confidence = known_extracted_count / total_extracted_count if total_extracted_count > 0 else 0.0
    
    # Os resultados são usados em poe2_parser.py na função is_build_valid
    return (confidence, known_extracted_count, total_extracted_count, len(extracted_skills))


# Carregar os dados de referência quando o módulo é importado
load_reference_data()
