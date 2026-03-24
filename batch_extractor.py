# batch_extractor.py - Extração em Lote de Builds
import time
import logging
from typing import List, Dict
# Importação da função de score
from poe2_parser import calculate_recommendation_score 
from llm_extractor_v2 import fetch_build_article, extract_build_with_llm, save_build_to_file, validate_extracted_build

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== LISTA DE BUILDS PARA EXTRAIR (Mantida) =====
BUILD_URLS = [
    # Warrior
    {"url": "https://mobalytics.gg/poe-2/builds/earthquake-leveling-guide", "class": "Warrior"},
    {"url": "https://maxroll.gg/poe2/build-guides/boneshatter-warrior-leveling-guide", "class": "Warrior"},
    
    # Ranger
    {"url": "https://mobalytics.gg/poe-2/builds/lightning-arrow-ranger-leveling-guide", "class": "Ranger"},
    {"url": "https://mobalytics.gg/poe-2/builds/gas-arrow-pathfinder-leveling", "class": "Ranger"},
    
    # Monk
    {"url": "https://mobalytics.gg/poe-2/builds/ice-strike-monk-leveling-guide", "class": "Monk"},
    {"url": "https://maxroll.gg/poe2/build-guides/monk-leveling-guide", "class": "Monk"},
    
    # Sorceress
    {"url": "https://maxroll.gg/poe2/build-guides/sorceress-leveling-guide", "class": "Sorceress"},
    
    # Exemplo com reputation=0
    {"url": "https://site-aleatorio.com/build-nao-popular", "class": "Witch"},
]

def batch_extract_builds(urls: List[Dict[str, str]], delay: int = 5):
    """
    Executa a extração, validação e salvamento de builds para uma lista de URLs.
    """
    total = len(urls)
    success_count = 0
    failed_urls = []
    
    logger.info(f"--- INICIANDO EXTRAÇÃO DE {total} BUILDS EM LOTE ---")
    
    for i, build_info in enumerate(urls, 1):
        url = build_info['url']
        class_name = build_info['class']
        
        logger.info(f"\n--- ({i}/{total}) Processando {class_name}: {url} ---")

        try:
            # 1. Fetch
            article_text = fetch_build_article(url)
            
            if not article_text:
                logger.warning("⚠️ Artigo vazio ou não acessível. Pulando.")
                failed_urls.append({"url": url, "class": class_name, "reason": "Artigo não acessível/vazio"})
                continue
            
            # 2. Extract
            logger.info("🤖 Extraindo com LLM...")
            build_data = extract_build_with_llm(article_text, class_name, url)
            
            if not build_data:
                logger.warning("⚠️ LLM não conseguiu extrair dados válidos. Pulando.")
                failed_urls.append({"url": url, "class": class_name, "reason": "Extração LLM falhou"})
                continue

            # 3. VALIDAÇÃO E CÁLCULO DE SCORE
            # Utilizamos a função do poe2_parser.py
            confidence, rep_norm, rec_score = calculate_recommendation_score(build_data)

            # 💥 INJETAR NOVOS CAMPOS NO JSON 💥
            build_data['confidence'] = confidence
            build_data['reputation_normalized'] = rep_norm # Opcional, para debug
            build_data['recommendation_score'] = rec_score
            
            # Verificação final de validade antes de salvar (opcional, mas seguro)
            if not validate_extracted_build(build_data):
                logger.warning("⚠️ Build não atinge requisitos mínimos (Skills ou Confiança). Não será salva.")
                failed_urls.append({"url": url, "class": class_name, "reason": "Falha na validação final"})
                continue
            
            # 4. Save
            logger.info("💾 Salvando build...")
            save_build_to_file(build_data) 
            
            success_count += 1
            
            # Mostrar resumo (Atualizado com Score)
            total_skills = sum(
                len([a for a in tier.get('actions', []) if a.get('type') == 'Skill'])
                for tier in build_data.get('skill_tree_leveling', [])
            )
            
            logger.info(f"✅ SUCESSO! Build: {build_data.get('build_name', 'N/A')[:50]}")
            logger.info(f"   Skills extraídas: {total_skills}")
            logger.info(f"   Score de Recomendação: {rec_score:.2f} / 100.00") 
            
        except Exception as e:
            logger.error(f"❌ ERRO FATAL ao processar {url}: {e}")
            failed_urls.append({"url": url, "class": class_name, "reason": str(e)})
        
        # Delay entre requisições
        if i < total:
            logger.info(f"\n⏳ Aguardando {delay}s antes da próxima extração...")
            time.sleep(delay)
    
    # Resumo Final
    logger.info("\n" + "="*70)
    logger.info("📊 RESUMO DA EXTRAÇÃO EM LOTE")
    logger.info("="*70)
    logger.info(f"✅ Sucessos: {success_count}/{total}")
    logger.info(f"❌ Falhas: {len(failed_urls)}/{total}")
    
    if failed_urls:
        logger.info("\n❌ URLs que falharam:")
        for failed in failed_urls:
            logger.info(f"   • {failed['class']}: {failed['url']}")
            logger.info(f"     Razão: {failed['reason']}")
    
    logger.info("\n" + "="*70)
    logger.info(f"🎉 Extração concluída! {success_count} builds adicionadas ao sistema.")
    logger.info("="*70 + "\n")
    
    return success_count, failed_urls

if __name__ == '__main__':
    import sys
    
    # Permitir customizar o delay via argumento
    delay = 5
    if len(sys.argv) > 1:
        try:
            delay = int(sys.argv[1])
        except ValueError:
            logger.error("Argumento inválido. Usando delay padrão de 5s.")
            
    batch_extract_builds(BUILD_URLS, delay=delay)