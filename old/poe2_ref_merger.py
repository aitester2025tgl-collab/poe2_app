# poe2_ref_merger.py - VERSÃO CORRIGIDA (Usa a chave SKILL_GEMS_ACTIVE)

import json
import os
import logging
from typing import Dict, Any, List, Set

# Configurações de Ficheiros
EXTRACTED_SKILLS_FILE = "extracted_skill_names.json"
REFERENCE_DATA_FILE = "poe2_ref_data.json"

# CHAVE CORRETA para as Skills no ficheiro poe2_ref_data.json
SKILL_KEY = "SKILL_GEMS_ACTIVE"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_json_file(file_path: str) -> Any:
    """Carrega dados de um ficheiro JSON, com gestão de erros."""
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            if not content:
                return {}
            return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"❌ Erro ao analisar JSON em {file_path}: {e}")
        return {}
    except Exception as e:
        logger.error(f"❌ Erro ao carregar {file_path}: {e}")
        return {}

def merge_skills_into_reference():
    """
    Carrega as skills extraídas e o Ground Truth existente, 
    e atualiza o Ground Truth com novas skills.
    """
    # 1. Carregar novas skills (do LLM)
    extracted_data = load_json_file(EXTRACTED_SKILLS_FILE)
    newly_extracted_skills = set(extracted_data.get("skill_names", []))
    
    if not newly_extracted_skills:
        logger.info("⚠️ Não há novas skills para integrar.")
        return

    logger.info(f"✅ {len(newly_extracted_skills)} skills aprendidas para integrar.")
    
    # 2. Carregar Ground Truth
    ref_data = load_json_file(REFERENCE_DATA_FILE)
    
    # Cria Ground Truth se não existir
    if not ref_data:
        logger.info("⚠️ Ficheiro de referência inexistente ou vazio. A criar estrutura nova.")
        ref_data = {SKILL_KEY: {}, "ALL_PASSIVE_NAMES": []}

    # As skills do Ground Truth (Dict: {nome: nível})
    # ❗ CORREÇÃO CRÍTICA: Usar a chave SKILL_KEY
    existing_skills: Dict[str, int] = ref_data.get(SKILL_KEY, {})
    
    initial_skill_count = len(existing_skills)
    new_skills_added = 0
    
    # 3. Integrar novas skills
    for skill_name in newly_extracted_skills:
        # Verifica se a skill já existe
        if skill_name not in existing_skills:
            # Adiciona a nova skill com um nível mínimo simulado de 1.
            existing_skills[skill_name] = 1 
            new_skills_added += 1
            
    # Atualiza o dicionário no ref_data
    ref_data[SKILL_KEY] = existing_skills

    # 4. Salvar Ground Truth expandido
    try:
        with open(REFERENCE_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(ref_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"✅ Fusão concluída. Adicionadas {new_skills_added} novas skills ao Ground Truth.")
        logger.info(f"✅ O Ground Truth agora tem um total de {len(existing_skills)} skills conhecidas. (Antes: {initial_skill_count})")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar o ficheiro {REFERENCE_DATA_FILE}: {e}")

if __name__ == '__main__':
    merge_skills_into_reference()