# poe2_passive_learner.py - VERSÃO ROBUSTA (Suporta formatos Lista OU Dicionário)

import json
import os
import logging
from typing import Set, Dict, Any, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

JSON_BUILD_FILE = "poe2_builds.json"
OUTPUT_FILE = "extracted_passive_names.json"

def load_builds(file_path: str = JSON_BUILD_FILE) -> List[Dict[str, Any]]:
    """
    Carrega as builds do ficheiro JSON, suportando a estrutura de Lista ou Dicionário.
    Retorna sempre uma lista plana de builds.
    """
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        return []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar builds de {file_path}: {e}")
        return []
    
    all_builds: List[Dict[str, Any]] = []

    if isinstance(data, list):
        # Formato 1: Lista direta de builds
        all_builds = data
    elif isinstance(data, dict):
        # Formato 2: Dicionário onde as chaves são as classes
        for class_builds in data.values():
            if isinstance(class_builds, list):
                all_builds.extend(class_builds)
    
    # Filtra quaisquer entradas não-dicionário
    return [b for b in all_builds if isinstance(b, dict)]

def extract_passive_names(builds: List[Dict[str, Any]]) -> Set[str]:
    """
    Percorre todas as builds na lista plana e extrai nomes únicos de passivas chave.
    """
    unique_passive_names: Set[str] = set()
    total_passive_count = 0
    
    # Termos irrelevantes que o LLM pode ter deixado escapar
    irrelevant_phrases = {"N/A", "n/a", "", "Passiva Chave", "Passiva de Árvore", "None", "passives"}
    
    for build in builds:
        # A nova estrutura usa 'skill_tree_leveling' como lista
        leveling_steps = build.get('skill_tree_leveling', [])
        
        for step in leveling_steps:
            actions = step.get('actions', [])
            
            for action in actions:
                # O campo 'passives' é uma lista dentro de cada ação
                passive_list = action.get("passives", [])
                
                if isinstance(passive_list, list):
                    for p_name_raw in passive_list:
                        if isinstance(p_name_raw, str):
                            p_name = p_name_raw.strip()
                            total_passive_count += 1
                            
                            if p_name and p_name not in irrelevant_phrases:
                                unique_passive_names.add(p_name)
                                
    logger.info(f"✅ Extração concluída. Total de passivas analisadas: {total_passive_count}.")
    return unique_passive_names

def save_names(names: Set[str], file_path: str):
    """Guarda os nomes únicos extraídos num ficheiro JSON."""
    try:
        # Garante que a lista está ordenada para consistência
        sorted_names = sorted(list(names)) 
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(sorted_names, f, indent=4, ensure_ascii=False)
        logger.info(f"✅ {len(names)} nomes únicos de passivas guardados em '{file_path}'.")
    except Exception as e:
        logger.error(f"Erro ao guardar nomes de passivas: {e}")

if __name__ == '__main__':
    logger.info("--- 🧠 A analisar builds para aprender novas passivas chave ---")
    
    # 1. Carregar builds (agora de forma robusta)
    build_data = load_builds(JSON_BUILD_FILE)
    if not build_data:
        logger.error(f"❌ Não foi possível carregar dados de builds de '{JSON_BUILD_FILE}'. A abortar.")
    else:
        # 2. Extrair nomes de passivas
        unique_passives = extract_passive_names(build_data)
        
        # 3. Guardar nomes
        save_names(unique_passives, OUTPUT_FILE)
