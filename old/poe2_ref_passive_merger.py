# poe2_ref_passive_merger.py - Funde passivas aprendidas no Ground Truth
import json
import os
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ficheiros de dados
EXTRACTED_PASSIVE_FILE = "extracted_passive_names.json"
REF_DATA_FILE = "poe2_ref_data.json"

def load_json(file_path: str) -> Any:
    """Carrega dados de um ficheiro JSON."""
    if not os.path.exists(file_path):
        return [] if 'passive_names' in file_path else {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar {file_path}: {e}")
        return [] if 'passive_names' in file_path else {}

def save_json(data: Any, file_path: str):
    """Guarda dados num ficheiro JSON."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Erro ao guardar {file_path}: {e}")

def merge_passive_data():
    """Carrega passivas aprendidas e funde-as no Ground Truth."""
    logger.info("--- 🔄 A iniciar fusão de novas passivas no Ground Truth ---")
    
    # 1. Carregar novas passivas aprendidas
    new_passives: List[str] = load_json(EXTRACTED_PASSIVE_FILE)
    if not new_passives:
        logger.warning(f"⚠️ Não há novas passivas para integrar em '{EXTRACTED_PASSIVE_FILE}'. A terminar.")
        return

    logger.info(f"✅ {len(new_passives)} passivas aprendidas para integrar.")

    # 2. Carregar o ficheiro de referência (Ground Truth)
    ref_data: Dict[str, Any] = load_json(REF_DATA_FILE)
    
    # Certificar-se de que a chave existe e é uma lista
    if 'passive_names' not in ref_data or not isinstance(ref_data['passive_names'], list):
        ref_data['passive_names'] = []
    
    current_passives_set = set(ref_data['passive_names'])
    initial_count = len(current_passives_set)
    
    # 3. Fusão
    newly_added_count = 0
    for passive in new_passives:
        if passive not in current_passives_set:
            current_passives_set.add(passive)
            newly_added_count += 1
            
    # Atualizar o Ground Truth (ordenado)
    ref_data['passive_names'] = sorted(list(current_passives_set))
    final_count = len(ref_data['passive_names'])

    # 4. Guardar o Ground Truth atualizado
    save_json(ref_data, REF_DATA_FILE)

    logger.info(f"✅ Fusão concluída. Adicionadas {newly_added_count} novas passivas ao Ground Truth.")
    logger.info(f"✅ O Ground Truth de passivas agora tem um total de {final_count} passivas conhecidas. (Antes: {initial_count})")
    
if __name__ == '__main__':
    merge_passive_data()