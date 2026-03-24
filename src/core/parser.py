# poe2_parser.py - VERSÃO FINAL (FORMATO CONSISTENTE)
import json
import os
import logging
from typing import Dict, Any, List, Set, Tuple, Union 

# CONSTANTES CRÍTICAS - AJUSTADAS PARA PERMITIR MAIS BUILDS
MIN_CONFIDENCE_THRESHOLD = 0.40  # 40% - Reduzido de 50%
MIN_SKILLS_REQUIRED = 3  # Mínimo de 3 SKILLS - Reduzido de 5

# IMPORTAÇÕES CRUCIAIS: Importa as funções de validação e as listas de referência
try:
    from src.core.validator import load_reference_data, get_build_confidence
    load_reference_data() 
except ImportError:
    logging.warning("poe2_data_ref.py não encontrado. A validação de skills/passivas será ignorada.")
    
    def get_build_confidence(build: Dict[str, Any]) -> Tuple[float, int, int, int]: 
        """Fallbacks: 100% de confiança, 0 extraído, 0 total, 0 skills."""
        return 1.0, 0, 0, 0 
    
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_builds(file_path="poe2_builds.json") -> Dict[str, List[Dict[str, Any]]]:
    """
    Carrega todas as builds do ficheiro...
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"❌ Ficheiro {file_path} não encontrado.")
        return {}
    except json.JSONDecodeError:
        logger.error(f"❌ Erro ao decodificar JSON em {file_path}. Ficheiro corrompido.")
        return {}
    except Exception as e:
        logger.error(f"❌ Erro inesperado ao carregar builds: {e}")
        return {}


def is_build_valid(build: Dict[str, Any], verbose: bool = False) -> bool:
    """
    Verifica se uma build atende aos requisitos mínimos para ser apresentada.
    """
    confidence, _, _, unique_skill_count = get_build_confidence(build)
    
    is_valid = (
        unique_skill_count >= MIN_SKILLS_REQUIRED and
        confidence >= MIN_CONFIDENCE_THRESHOLD
    )
    
    if verbose and not is_valid:
        if unique_skill_count < MIN_SKILLS_REQUIRED:
            logger.error(f"  -> Falha: Apenas {unique_skill_count} skills únicas (Min: {MIN_SKILLS_REQUIRED})")
        if confidence < MIN_CONFIDENCE_THRESHOLD:
            logger.error(f"  -> Falha: Confiança de extração de {confidence:.1%} (Min: {MIN_CONFIDENCE_THRESHOLD:.1%})")

    return is_valid

# =======================================================
# 💥 FUNÇÃO CRÍTICA: CALCULAR O SCORE DE RECOMENDAÇÃO 💥
# =======================================================
def calculate_recommendation_score(build: Dict[str, Any]) -> Tuple[float, float, float]:
    """
    Calcula a Confiança (0.0 a 1.0) e um Score de Recomendação (0.0 a 100.0).
    
    Returns: (confidence, reputation_normalized, recommendation_score)
    """
    
    # 1. OBTER CONFIDÊNCIA DE DADOS
    # A confiança está entre 0.0 e 1.0
    confidence, _, _, _ = get_build_confidence(build)
    
    # 2. OBTER REPUTAÇÃO (Popularidade)
    # Assumimos que a reputação é um valor bruto (ex: 50000).
    reputation_raw = build.get('reputation', 0)
    
    # Normalização da Reputação (Ajuste o MAX_REPUTATION_VALUE conforme os dados reais)
    # Valor máximo usado para "normalizar" a reputação entre 0.0 e 1.0.
    MAX_REPUTATION_VALUE = 100000  
    
    # Evita divisão por zero. O valor é limitado a 1.0, mesmo que a reputação bruta seja superior.
    reputation_normalized = min(reputation_raw / MAX_REPUTATION_VALUE, 1.0) if MAX_REPUTATION_VALUE > 0 else 0.0
    
    # 3. CÁLCULO PONDERADO DO SCORE
    # Ponderação sugerida: 70% Confiança (Qualidade de Dados) + 30% Reputação (Popularidade)
    WEIGHT_CONFIDENCE = 0.7 
    WEIGHT_REPUTATION = 0.3
    
    recommendation_score = (
        (confidence * WEIGHT_CONFIDENCE) + 
        (reputation_normalized * WEIGHT_REPUTATION)
    ) * 100.0  # Multiplicamos por 100 para um score de 0 a 100.
    
    # Arredondamos para evitar números excessivamente longos no JSON
    return round(confidence, 4), round(reputation_normalized, 4), round(recommendation_score, 2)


# =======================================================
# EXECUÇÃO (MANTIDA)
# =======================================================
if __name__ == '__main__':
    # ... (Resto do código de teste)
    
    # Executa o teste de validação (mantido)
    builds_by_class = load_builds()
    total_count = 0
    valid_count = 0
    
    print(f"\n--- VALIDAÇÃO DE BUILDS (Min Confidence: {MIN_CONFIDENCE_THRESHOLD:.1%}) ---")

    for cls, builds in builds_by_class.items():
        for build in builds:
            total_count += 1
            build_name_display = build.get('build_name', build.get('name', 'N/A'))
            
            # 💥 NOVO: Calcular o score e mostrar no log de teste
            confidence, rep_norm, rec_score = calculate_recommendation_score(build)
            
            if is_build_valid(build, verbose=True):
                valid_count += 1
                logger.info(f"✅ Válida (Score: {rec_score:.2f} / Conf: {confidence:.1%}): {cls} - {build_name_display} (Rep: {build.get('reputation', 0)})")
            else:
                logger.error(f"❌ Inválida (Score: {rec_score:.2f} / Conf: {confidence:.1%}): {cls} - {build_name_display} (Rep: {build.get('reputation', 0)})")

    print(f"\n--- RESUMO DO TESTE ---")
    print(f"Total de Builds Analisadas: {total_count}")
    print(f"Total de Builds Válidas: {valid_count}")
    print("-----------------------")
    
    if total_count == 0:
        logger.error(f"❌ Não foi possível carregar nenhuma build. Verifique se o ficheiro poe2_builds.json existe e tem o formato correto.")
    elif valid_count > 0:
        # Encontra a primeira build válida para demonstrar a formatação
        for cls, builds in builds_by_class.items():
            for build in builds:
                if is_build_valid(build):
                    print("\n--- DETALHE DA PRIMEIRA BUILD VÁLIDA ---")
                    print(f"Nome: {build.get('build_name')}")
                    print(f"URL: {build.get('url')}")
                    print(f"Confiança: {build.get('confidence', confidence):.1%}") # Usa o valor do JSON se existir, senão o calculado
                    print(f"Score Recomendação: {rec_score:.2f}") # Usa o valor calculado
                    print("----------------------------------------")
                    break
            if valid_count > 0:
                break