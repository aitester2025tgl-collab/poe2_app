# poe2_assistente.py - VERSÃO ATUALIZADA (FORMATO CONSISTENTE)
import logging
from poe2_parser import load_builds, is_build_valid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

POE2_CLASSES = [
    "Warrior", "Monk", "Mercenary", "Sorceress", "Witch", 
    "Ranger", "Huntress", "Druid", "Duelist", "Marauder", 
    "Shadow", "Templar"
]

def get_valid_builds_for_class(cls):
    """
    Reads builds from JSON.
    Returns a LIST of ALL valid builds for a specific class.
    """
    # builds_data é o dicionário de todas as classes
    builds_data = load_builds() 
    
    # raw_builds é a lista de builds para a classe específica
    raw_builds = builds_data.get(cls, [])
    
    valid_builds = []
    # Itera sobre a lista de builds para encontrar todos os válidos
    for build in raw_builds:
        if is_build_valid(build):
            # Garante que a classe está presente
            build["class"] = cls 
            valid_builds.append(build)
            
    return valid_builds

def get_all_classes_with_builds():
    """
    Retorna uma lista de classes que têm pelo menos uma build válida.
    """
    builds_data = load_builds()
    classes_with_builds = []
    
    for cls in POE2_CLASSES:
        if cls in builds_data and builds_data[cls]:
            # Verifica se há pelo menos uma build válida
            valid_builds = get_valid_builds_for_class(cls)
            if valid_builds:
                classes_with_builds.append(cls)
    
    return classes_with_builds

def get_build_count_by_class():
    """
    Retorna um dicionário com a contagem de builds por classe.
    """
    builds_data = load_builds()
    counts = {}
    
    for cls in POE2_CLASSES:
        valid_builds = get_valid_builds_for_class(cls)
        counts[cls] = len(valid_builds)
    
    return counts