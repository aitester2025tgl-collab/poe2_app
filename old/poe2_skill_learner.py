# poe2_skill_learner.py - VERSÃO ROBUSTA (Suporta formatos Lista OU Dicionário e usa a chave 'name')

import json
import os
import logging
from typing import Dict, Any, List, Set

# Configurações de Ficheiros
BUILD_FILE = "poe2_builds.json"
OUTPUT_FILE = "extracted_skill_names.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_builds(file_path: str = BUILD_FILE) -> List[Dict[str, Any]]:
    """
    Carrega as builds do ficheiro JSON, suportando a estrutura de Lista (llm_extractor)
    ou Dicionário de Classes (poe2_fetcher). Retorna sempre uma lista plana de builds.
    """
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        logger.warning(f"❌ Ficheiro {file_path} não encontrado ou vazio.")
        return []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"❌ Erro ao carregar builds: {e}")
        return []
    
    all_builds: List[Dict[str, Any]] = []

    if isinstance(data, list):
        # Formato 1: Lista direta de builds (gerado pelo llm_extractor)
        all_builds = data
    elif isinstance(data, dict):
        # Formato 2: Dicionário onde as chaves são as classes (gerado pelo poe2_fetcher)
        for class_builds in data.values():
            if isinstance(class_builds, list):
                all_builds.extend(class_builds)
    
    # Filtra quaisquer entradas não-dicionário
    return [b for b in all_builds if isinstance(b, dict)]


def extract_and_save_unique_skills():
    """
    Extrai todos os nomes únicos de 'name' (a skill) de todas as builds
    e guarda-os num novo ficheiro JSON.
    """
    logger.info("--- 🧠 A analisar builds para aprender novas skills chave ---")
    
    all_builds = load_builds()
    
    if not all_builds:
        logger.warning("⚠️ Não foram carregadas builds válidas. A extração de skills falhou.")
        return
        
    unique_skills: Set[str] = set()
    total_skills_analyzed = 0
    
    for build in all_builds:
        # A nova estrutura usa 'skill_tree_leveling' como lista
        leveling_steps = build.get('skill_tree_leveling', [])
        
        for step in leveling_steps:
            actions = step.get('actions', [])
            
            for action in actions:
                # ❗ CORREÇÃO CRÍTICA: O nome da skill está agora na chave 'name'
                skill_name = action.get("name") 
                
                # Verifica se a ação é do tipo 'Skill' e se o nome é uma string válida
                if action.get("type") == "Skill" and skill_name and isinstance(skill_name, str):
                    # Adiciona à lista de únicos e remove espaços desnecessários
                    unique_skills.add(skill_name.strip())
                    total_skills_analyzed += 1

    # Converter o set de skills para uma lista e ordenar
    skills_list = sorted(list(unique_skills))
    
    # Estrutura para o ficheiro de output
    output_data = {
        "description": "Lista de todos os nomes únicos de skills extraídos das builds (para Ground Truth/Learning do LLM).",
        "total_unique_skills": len(skills_list),
        "skill_names": skills_list
    }

    # Salvar para o ficheiro
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Extração concluída. Total de skills analisadas: {total_skills_analyzed}.")
        logger.info(f"✅ {len(skills_list)} nomes únicos de skills guardados em '{OUTPUT_FILE}'.")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar o ficheiro {OUTPUT_FILE}: {e}")


if __name__ == '__main__':
    extract_and_save_unique_skills()
