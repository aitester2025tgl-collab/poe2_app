# learning_system.py - Sistema de Aprendizagem e Qualidade
import json
import os
import logging
from typing import Dict, Any, List, Set, Tuple
from collections import Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== FICHEIROS =====
BUILD_FILE = "poe2_builds.json"
GROUND_TRUTH_FILE = "poe2_ref_data.json"
LEARNING_STATS_FILE = "learning_stats.json"

# ===== GROUND TRUTH STRUCTURE =====
DEFAULT_GROUND_TRUTH = {
    "SKILL_GEMS_ACTIVE": {},  # {skill_name: min_level}
    "passives": [],           # [passive_name1, passive_name2, ...]
    "metadata": {
        "last_updated": "",
        "total_builds_analyzed": 0,
        "total_skills_learned": 0,
        "total_passives_learned": 0
    }
}

# ===== UTILITIES =====
def load_json_safe(file_path: str, default: Any = None) -> Any:
    """Carrega JSON com fallback seguro."""
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        return default if default is not None else {}
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"❌ Erro ao carregar {file_path}: {e}")
        return default if default is not None else {}

def save_json_safe(data: Any, file_path: str):
    """Salva JSON com segurança."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ {file_path} salvo com sucesso.")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar {file_path}: {e}")

# ===== EXTRACTION FUNCTIONS =====
def extract_skills_from_builds(builds_by_class: Dict[str, List[Dict]]) -> Set[str]:
    """Extrai todos os nomes de skills únicas das builds."""
    skills = set()
    
    for class_name, builds in builds_by_class.items():
        for build in builds:
            for tier in build.get('skill_tree_leveling', []):
                for action in tier.get('actions', []):
                    if action.get('type') == 'Skill':
                        skill_name = action.get('name', '').strip()
                        if skill_name and skill_name != 'N/A' and len(skill_name) > 3:
                            skills.add(skill_name)
    
    return skills

def extract_passives_from_builds(builds_by_class: Dict[str, List[Dict]]) -> Set[str]:
    """Extrai todos os nomes de passivas únicas das builds."""
    passives = set()
    
    for class_name, builds in builds_by_class.items():
        for build in builds:
            for tier in build.get('skill_tree_leveling', []):
                for action in tier.get('actions', []):
                    passive_list = action.get('passives', [])
                    if isinstance(passive_list, list):
                        for passive in passive_list:
                            passive = str(passive).strip()
                            if passive and passive != 'N/A' and len(passive) > 3:
                                passives.add(passive)
    
    return passives

def count_skill_frequency(builds_by_class: Dict[str, List[Dict]]) -> Counter:
    """Conta quantas vezes cada skill aparece."""
    skill_counter = Counter()
    
    for class_name, builds in builds_by_class.items():
        for build in builds:
            for tier in build.get('skill_tree_leveling', []):
                for action in tier.get('actions', []):
                    if action.get('type') == 'Skill':
                        skill_name = action.get('name', '').strip()
                        if skill_name and skill_name != 'N/A':
                            skill_counter[skill_name] += 1
    
    return skill_counter

# ===== LEARNING FUNCTIONS =====
def learn_from_builds():
    """
    Analisa todas as builds e atualiza o Ground Truth com novos conhecimentos.
    """
    logger.info("\n" + "="*60)
    logger.info("🧠 SISTEMA DE APRENDIZAGEM - INICIANDO")
    logger.info("="*60)
    
    # 1. Carregar builds
    logger.info("\n📚 1/5 - Carregando builds...")
    builds_by_class = load_json_safe(BUILD_FILE, {})
    
    total_builds = sum(len(builds) for builds in builds_by_class.values())
    logger.info(f"✅ {total_builds} builds carregadas de {len(builds_by_class)} classes.")
    
    if total_builds == 0:
        logger.warning("⚠️ Nenhuma build encontrada. Nada para aprender.")
        return
    
    # 2. Extrair skills e passivas
    logger.info("\n🔍 2/5 - Extraindo skills e passivas...")
    learned_skills = extract_skills_from_builds(builds_by_class)
    learned_passives = extract_passives_from_builds(builds_by_class)
    
    logger.info(f"✅ {len(learned_skills)} skills únicas encontradas.")
    logger.info(f"✅ {len(learned_passives)} passivas únicas encontradas.")
    
    # 3. Carregar Ground Truth existente
    logger.info("\n📖 3/5 - Carregando Ground Truth...")
    ground_truth = load_json_safe(GROUND_TRUTH_FILE, DEFAULT_GROUND_TRUTH.copy())
    
    # Garantir estrutura
    if 'SKILL_GEMS_ACTIVE' not in ground_truth:
        ground_truth['SKILL_GEMS_ACTIVE'] = {}
    if 'passives' not in ground_truth:
        ground_truth['passives'] = []
    if 'metadata' not in ground_truth:
        ground_truth['metadata'] = DEFAULT_GROUND_TRUTH['metadata'].copy()
    
    # 4. Merge: Adicionar novos conhecimentos
    logger.info("\n🔄 4/5 - Integrando novos conhecimentos...")
    
    # Skills
    existing_skills = set(ground_truth['SKILL_GEMS_ACTIVE'].keys())
    new_skills = learned_skills - existing_skills
    
    for skill in new_skills:
        ground_truth['SKILL_GEMS_ACTIVE'][skill] = 1  # Level placeholder
    
    logger.info(f"✅ {len(new_skills)} novas skills adicionadas ao Ground Truth.")
    
    # Passivas
    existing_passives = set(ground_truth['passives'])
    new_passives = learned_passives - existing_passives
    
    ground_truth['passives'].extend(list(new_passives))
    ground_truth['passives'] = sorted(list(set(ground_truth['passives'])))
    
    logger.info(f"✅ {len(new_passives)} novas passivas adicionadas ao Ground Truth.")
    
    # 5. Atualizar metadata
    from datetime import datetime
    ground_truth['metadata']['last_updated'] = datetime.now().isoformat()
    ground_truth['metadata']['total_builds_analyzed'] = total_builds
    ground_truth['metadata']['total_skills_learned'] = len(ground_truth['SKILL_GEMS_ACTIVE'])
    ground_truth['metadata']['total_passives_learned'] = len(ground_truth['passives'])
    
    # Salvar Ground Truth
    save_json_safe(ground_truth, GROUND_TRUTH_FILE)
    
    # 6. Estatísticas de aprendizagem
    logger.info("\n📊 5/5 - Gerando estatísticas...")
    skill_frequency = count_skill_frequency(builds_by_class)
    
    learning_stats = {
        "timestamp": datetime.now().isoformat(),
        "total_builds": total_builds,
        "total_skills": len(learned_skills),
        "total_passives": len(learned_passives),
        "new_skills_learned": len(new_skills),
        "new_passives_learned": len(new_passives),
        "top_10_skills": skill_frequency.most_common(10)
    }
    
    save_json_safe(learning_stats, LEARNING_STATS_FILE)
    
    # Mostrar top skills
    logger.info("\n🏆 TOP 10 SKILLS MAIS USADAS:")
    for i, (skill, count) in enumerate(learning_stats['top_10_skills'], 1):
        logger.info(f"  {i}. {skill} ({count} builds)")
    
    logger.info("\n" + "="*60)
    logger.info("✅ APRENDIZAGEM CONCLUÍDA COM SUCESSO!")
    logger.info("="*60)
    logger.info(f"📊 Ground Truth: {len(ground_truth['SKILL_GEMS_ACTIVE'])} skills, {len(ground_truth['passives'])} passivas")
    logger.info(f"📈 Novos conhecimentos: +{len(new_skills)} skills, +{len(new_passives)} passivas")
    logger.info("="*60 + "\n")

def show_ground_truth_stats():
    """Mostra estatísticas do Ground Truth atual."""
    ground_truth = load_json_safe(GROUND_TRUTH_FILE, DEFAULT_GROUND_TRUTH.copy())
    
    print("\n" + "="*60)
    print("📊 ESTATÍSTICAS DO GROUND TRUTH")
    print("="*60)
    
    metadata = ground_truth.get('metadata', {})
    print(f"\n📅 Última atualização: {metadata.get('last_updated', 'Nunca')}")
    print(f"📚 Builds analisadas: {metadata.get('total_builds_analyzed', 0)}")
    print(f"⚔️  Skills conhecidas: {len(ground_truth.get('SKILL_GEMS_ACTIVE', {}))}")
    print(f"🌳 Passivas conhecidas: {len(ground_truth.get('passives', []))}")
    
    # Mostrar algumas skills
    skills = list(ground_truth.get('SKILL_GEMS_ACTIVE', {}).keys())
    if skills:
        print(f"\n🎯 Exemplos de Skills (primeiras 20):")
        for skill in sorted(skills)[:20]:
            print(f"  • {skill}")
    
    # Mostrar algumas passivas
    passives = ground_truth.get('passives', [])
    if passives:
        print(f"\n🌳 Exemplos de Passivas (primeiras 20):")
        for passive in sorted(passives)[:20]:
            print(f"  • {passive}")
    
    print("\n" + "="*60 + "\n")

def validate_build_quality(build: Dict[str, Any]) -> Tuple[bool, float, Dict[str, Any]]:
    """
    Valida a qualidade de uma build contra o Ground Truth.
    
    Returns:
        (is_valid, confidence_score, details)
    """
    ground_truth = load_json_safe(GROUND_TRUTH_FILE, DEFAULT_GROUND_TRUTH.copy())
    known_skills = set(ground_truth.get('SKILL_GEMS_ACTIVE', {}).keys())
    known_passives = set(ground_truth.get('passives', []))
    
    # Extrair skills da build
    build_skills = set()
    build_passives = set()
    
    for tier in build.get('skill_tree_leveling', []):
        for action in tier.get('actions', []):
            if action.get('type') == 'Skill':
                skill_name = action.get('name', '').strip()
                if skill_name and skill_name != 'N/A':
                    build_skills.add(skill_name)
                
                for passive in action.get('passives', []):
                    passive = str(passive).strip()
                    if passive and passive != 'N/A':
                        build_passives.add(passive)
    
    # Calcular confiança
    total_items = len(build_skills) + len(build_passives)
    if total_items == 0:
        return False, 0.0, {"reason": "No skills or passives found"}
    
    known_items = len(build_skills & known_skills) + len(build_passives & known_passives)
    confidence = known_items / total_items
    
    # Critérios de validação
    min_skills = 3
    min_confidence = 0.4
    
    is_valid = (
        len(build_skills) >= min_skills and
        confidence >= min_confidence
    )
    
    details = {
        "total_skills": len(build_skills),
        "known_skills": len(build_skills & known_skills),
        "total_passives": len(build_passives),
        "known_passives": len(build_passives & known_passives),
        "confidence": confidence,
        "unknown_skills": list(build_skills - known_skills)[:5],  # Primeiras 5
        "unknown_passives": list(build_passives - known_passives)[:5]
    }
    
    return is_valid, confidence, details

# ===== MAIN =====
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "learn":
            learn_from_builds()
        elif command == "stats":
            show_ground_truth_stats()
        else:
            print(f"❌ Comando desconhecido: {command}")
            print("\nComandos disponíveis:")
            print("  python learning_system.py learn   - Aprende com as builds existentes")
            print("  python learning_system.py stats   - Mostra estatísticas do Ground Truth")
    else:
        # Default: Executar ambos
        learn_from_builds()
        show_ground_truth_stats()