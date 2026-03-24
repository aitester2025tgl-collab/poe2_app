# update_builds_online.py - VERSÃO AUTOMATIZADA CORRIGIDA (3 PASSOS)
import os
import json
import logging
from datetime import datetime, timedelta
import argparse

# 💥 PASSO 0: Importa a lógica de GESTÃO E LIMPEZA DO GROUND TRUTH
from poe2_ground_truth_manager import run_ground_truth_update 

# PASSO 1: Importa a lógica de busca e atualização do fetcher
from poe2_fetcher import update_all_builds 

# PASSO 2: Importa a lógica de aprendizagem do Ground Truth
from learning_system import learn_from_builds 

# O MÓDULO 'poe2_ref_merger' FOI REMOVIDO PARA CORRIGIR O ERRO DE IMPORTAÇÃO.
# Assumimos que 'learn_from_builds' faz a fusão e salva o resultado final.

# ----------------- CONFIG (MANTIDAS) -----------------
BUILD_FILE = "poe2_builds.json"
LAST_FETCH_FILE = "last_fetch.txt"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------- UTILITIES (MANTIDAS) -----------------
def get_last_fetch_time():
    if not os.path.exists(LAST_FETCH_FILE):
        return None
    with open(LAST_FETCH_FILE, "r") as f:
        try:
            return datetime.fromisoformat(f.read().strip())
        except Exception:
            return None

def set_last_fetch_time():
    with open(LAST_FETCH_FILE, "w") as f:
        f.write(datetime.now().isoformat())

# ----------------- UPDATE LOGIC (MODIFICADA) -----------------
def update_builds(force=False):
    last_fetch = get_last_fetch_time()
    
    # Lógica de verificação diária
    if not force and last_fetch and datetime.now() - last_fetch < timedelta(hours=24):
        logger.info("Already fetched builds in the last 24h. Skipping.")
        return

    logger.info("--- ⚙️ INICIANDO CADEIA DE ATUALIZAÇÃO COMPLETA ---")
    
    # PASSO 1: ATUALIZAÇÃO E LIMPEZA DO GROUND TRUTH (PRIMEIRO PASSO)
    logger.info("1/3: Atualizando e limpando o Ground Truth (Transferência de Support Gems)...")
    # Executa o fetch externo, identifica Support Gems e as MOVE para Passives, salvando o poe2_ref_data.json limpo.
    run_ground_truth_update(force_update=force) 
    
    # PASSO 2: BUSCAR BUILDS ONLINE (poe2_fetcher)
    logger.info("2/3: Buscando e extraindo builds online...")
    success = update_all_builds() 
    
    if success:
        
        # PASSO 3: APRENDER E INTEGRAR NOVAS SKILLS (learning_system)
        logger.info("3/3: Aprendendo novas skills e fundindo no Ground Truth...")
        # 'learn_from_builds()' deve agora salvar o resultado final no poe2_ref_data.json
        learn_from_builds() 
        
        # Finaliza
        set_last_fetch_time()
        logger.info("✅ Cadeia de atualização completa. Builds e Ground Truth atualizados com sucesso.")
        
    else:
        logger.error("❌ Falha na busca online. A manter os dados JSON existentes.")

# ----------------- MAIN EXECUTION (MANTIDA) -----------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Atualiza as builds do PoE 2 online.")
    parser.add_argument("--force", "-f", action="store_true", help="Força a atualização, ignorando a verificação de 24h.")
    args = parser.parse_args()
    update_builds(force=args.force)