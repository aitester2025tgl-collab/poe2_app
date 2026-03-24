# llm_extractor_v2.py - VERSÃO MELHORADA COM VALIDAÇÃO RIGOROSA
import requests
import json
import os
import logging
import time
from ollama import Client 
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup 
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== CONFIGURAÇÕES =====
OLLAMA_MODEL = 'mistral' 
OLLAMA_TEMPERATURE = 0.1 
BUILD_DATA_FILE = "poe2_builds.json"
MAX_LLM_RETRIES = 3
MIN_SKILLS_FOR_VALID_BUILD = 3  # Mínimo absoluto

# Inicializa o Cliente Ollama
try:
    OLLAMA_CLIENT = Client(timeout=120.0)
    OLLAMA_CLIENT.list()
    logger.info("✅ Ollama conectado com sucesso.")
except Exception as e:
    logger.error(f"❌ ERRO FATAL: Não foi possível conectar ao Ollama: {e}")
    exit(1)

# ===== LISTA DE SKILLS CONHECIDAS (Ground Truth Inicial) =====
KNOWN_SKILLS = {
    # Warrior Skills
    "Boneshatter", "Earthquake", "Shield Charge", "Sunder", "Hammer of the Gods",
    "Rolling Slam", "Armour Break", "Perfect Strike",
    
    # Ranger Skills  
    "Lightning Arrow", "Ice Shot", "Gas Arrow", "Fragmentation Rounds", 
    "Vine Arrow", "Siege Cascade",
    
    # Monk Skills
    "Ice Strike", "Killing Palm", "Tempest Bell", "Falling Thunder",
    "Glacial Cascade", "Wind Blast",
    
    # Mercenary Skills
    "Fragmenting Rounds", "High Velocity Rounds", "Plasma Blast",
    "Explosive Grenade", "Gas Grenade", "Oil Grenade",
    
    # Sorceress Skills
    "Spark", "Fireball", "Arc", "Ice Nova", "Freeze",
    "Frost Bolt", "Flame Wall", "Lightning Bolt",
    
    # Witch Skills
    "Bone Offering", "Raise Zombie", "Summon Skeletons", "Unearth",
    "Profane Ritual", "Detonate Dead",
    
    # Huntress Skills
    "Lightning Spear", "Whirling Assault", "Wind Dancer",
    "Tempest Flurry", "Scattershot",
}

KNOWN_PASSIVES = {
    "Resolute Technique", "Unwavering Stance", "Pain Attunement",
    "Iron Grip", "Point Blank", "Far Shot", "Elemental Overload",
    "Critical Strike", "Life Regeneration", "Mana Regeneration",
}

# ===== UTILITIES =====
def fetch_build_article(url: str) -> Optional[str]:
    """Busca o conteúdo HTML do URL e extrai o texto relevante."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove scripts e styles
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        
        # Tenta encontrar o artigo principal
        article = soup.find('article') or soup.find('main') or soup.find('div', class_='build-guide')
        
        if not article:
            logger.warning("⚠️ Não foi possível encontrar a secção principal do artigo.")
            article = soup.body
            
        if not article:
            return None
            
        text_content = article.get_text(separator=' ', strip=True)
        
        # Limitar o texto
        return text_content[:30000]
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Erro de rede ao buscar {url}: {e}")
        return None

def create_improved_prompt(article_text: str, class_name: str) -> str:
    """Cria um prompt melhorado e mais explícito para o LLM."""
    
    prompt = f"""Você é um especialista em Path of Exile 2 com a tarefa de extrair APENAS informação de LEVELING (níveis 1-40) de guias de build.

=== MISSÃO CRÍTICA ===
Extraia APENAS as Skills Ativas (Skill Gems) que o jogador deve usar DURANTE O LEVELING, organizadas por fases de níveis.

=== O QUE EXTRAIR ===
1. **build_name**: Título completo do guia (ex: "Earthquake Warrior Leveling Guide")
2. **class**: A classe do personagem: "{class_name}"
3. **version**: Versão do patch (ex: "0.3.0", "0.3.1")
4. **reputation**: SEMPRE use 50000 como placeholder
5. **skill_tree_leveling**: Lista de fases de leveling

=== ESTRUTURA DAS FASES ===
Cada fase deve ter:
- **level_range**: Ex: "1-10", "11-20", "21-30", "31-40"
- **actions**: Lista de skills adquiridas nessa fase

=== ESTRUTURA DE CADA SKILL ===
{{
  "type": "Skill",
  "name": "NOME EXATO DA SKILL GEM",
  "passives": ["Passive Name 1", "Passive Name 2", "Passive Name 3"]
}}

NOTA IMPORTANTE:
- O campo "level" NÃO é obrigatório. Omita-o se não souber o nível exato.
- "passives" é uma lista de NOMES de passivas da skill tree (Keystones, Notables).
- Se não houver passivas relacionadas, use lista vazia: []

=== REGRAS RIGOROSAS ===
1. **APENAS Skills Ativas**: Boneshatter, Earthquake, Lightning Arrow, etc.
2. **NUNCA extraia**: Títulos de build, descrições, nomes de secções
3. **Skills conhecidas para referência**: {', '.join(list(KNOWN_SKILLS)[:20])}...
4. **Se não encontrar pelo menos 3 skills de leveling, retorne lista vazia**
5. **Passivas devem ser NOMES da passive tree**: "Resolute Technique", "Iron Grip", "Point Blank"
6. **NÃO invente passivas genéricas**: Evite "Damage", "Life", "Mana" sozinhos

=== EXEMPLO DE OUTPUT CORRETO ===
{{
  "build_name": "Earthquake Titan Leveling Guide",
  "class": "{class_name}",
  "version": "0.3.0",
  "reputation": 50000,
  "skill_tree_leveling": [
    {{
      "level_range": "1-10",
      "actions": [
        {{
          "type": "Skill",
          "name": "Boneshatter",
          "passives": ["Mace Damage", "Area Damage", "Stun Mastery"]
        }},
        {{
          "type": "Skill",
          "name": "Earthquake",
          "passives": []
        }}
      ]
    }},
    {{
      "level_range": "11-20",
      "actions": [
        {{
          "type": "Skill",
          "name": "Hammer of the Gods",
          "passives": ["Stun Duration", "Mace Critical Strike"]
        }},
        {{
          "type": "Skill",
          "name": "Shield Charge",
          "passives": ["Shield Block", "Armour"]
        }}
      ]
    }}
  ]
}}

=== ARTIGO PARA ANÁLISE ===
{article_text}

=== IMPORTANTE ===
- Responda APENAS com o objeto JSON
- Se não encontrar dados de leveling claros, retorne skill_tree_leveling como lista vazia []
- NÃO invente informação
- NÃO use placeholder names como "Skill 1", "Skill 2"
- Foque em extrair o máximo de skills possível (5-15 é o ideal para um guia completo)
"""
    return prompt

def validate_extracted_build(build_data: Dict[str, Any]) -> bool:
    """Valida se a build extraída tem qualidade mínima."""
    
    # 1. Verificar estrutura básica
    if not isinstance(build_data, dict):
        logger.warning("⚠️ Build não é um dicionário.")
        return False
        
    if 'skill_tree_leveling' not in build_data:
        logger.warning("⚠️ Falta 'skill_tree_leveling'.")
        return False
        
    if not isinstance(build_data['skill_tree_leveling'], list):
        logger.warning("⚠️ 'skill_tree_leveling' não é uma lista.")
        return False
    
    # 2. Contar skills extraídas
    total_skills = 0
    valid_skill_names = 0
    
    for tier in build_data['skill_tree_leveling']:
        for action in tier.get('actions', []):
            if action.get('type') == 'Skill':
                skill_name = action.get('name', '')
                total_skills += 1
                
                # Verificar se o nome parece válido
                if (len(skill_name) > 3 and 
                    skill_name != 'N/A' and 
                    not skill_name.startswith('Skill ') and
                    skill_name[0].isupper()):
                    valid_skill_names += 1
    
    # 3. Validação: Mínimo de skills
    if total_skills < MIN_SKILLS_FOR_VALID_BUILD:
        logger.warning(f"⚠️ Build tem apenas {total_skills} skills (mínimo: {MIN_SKILLS_FOR_VALID_BUILD}).")
        return False
    
    # 4. Validação: Pelo menos 50% das skills devem ter nomes válidos
    if total_skills > 0:
        validity_ratio = valid_skill_names / total_skills
        if validity_ratio < 0.5:
            logger.warning(f"⚠️ Apenas {validity_ratio:.0%} das skills têm nomes válidos.")
            return False
    
    logger.info(f"✅ Build válida: {total_skills} skills, {valid_skill_names} com nomes válidos.")
    return True

def extract_build_with_llm(article_text: str, class_name: str, url: str) -> Optional[Dict[str, Any]]:
    """Usa o LLM para extrair dados da build com retry e validação."""
    
    prompt = create_improved_prompt(article_text, class_name)
    
    for attempt in range(MAX_LLM_RETRIES):
        try:
            logger.info(f"🤖 Tentativa {attempt + 1}/{MAX_LLM_RETRIES} de extração LLM...")
            
            response = OLLAMA_CLIENT.generate(
                model=OLLAMA_MODEL,
                prompt=prompt,
                options={'temperature': OLLAMA_TEMPERATURE},
                format='json'
            )
            
            json_str = response['response'].strip()
            
            # Limpeza do output
            if json_str.startswith('```json'):
                json_str = json_str[7:].strip()
            if json_str.endswith('```'):
                json_str = json_str[:-3].strip()
            if json_str.startswith('```'):
                json_str = json_str[3:].strip()

            # Tentar analisar o JSON
            try:
                build_data = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ JSON inválido na tentativa {attempt + 1}: {e}")
                time.sleep(2)
                continue
            
            # Validar a build extraída
            if validate_extracted_build(build_data):
                # Adicionar metadata
                build_data['url'] = url
                build_data['class'] = class_name
                return build_data
            else:
                logger.warning(f"⚠️ Build extraída não passou na validação (tentativa {attempt + 1}).")
                time.sleep(2)
                continue
                
        except Exception as e:
            logger.error(f"❌ Erro na tentativa {attempt + 1}: {e}")
            time.sleep(3)
            continue

    logger.error(f"❌ Falha em todas as {MAX_LLM_RETRIES} tentativas de extração.")
    return None

def save_build_to_file(build_data: Dict[str, Any]):
    """Salva a build no ficheiro JSON (formato de dicionário por classe)."""
    
    # 1. Carregar builds existentes
    builds_by_class = {}
    if os.path.exists(BUILD_DATA_FILE) and os.path.getsize(BUILD_DATA_FILE) > 0:
        try:
            with open(BUILD_DATA_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                if content:
                    builds_by_class = json.loads(content)
                    if not isinstance(builds_by_class, dict):
                        builds_by_class = {}
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar builds existentes: {e}")
    
    # 2. Adicionar a nova build à classe correspondente
    class_name = build_data.get('class', 'Unknown')
    if class_name not in builds_by_class:
        builds_by_class[class_name] = []
    
    # Remover build duplicada (mesmo URL)
    new_url = build_data['url']
    builds_by_class[class_name] = [
        b for b in builds_by_class[class_name] 
        if b.get('url') != new_url
    ]
    
    # Adicionar nova build
    builds_by_class[class_name].append(build_data)
    
    # Ordenar por reputação
    builds_by_class[class_name].sort(key=lambda b: b.get('reputation', 0), reverse=True)
    
    # Limitar a 10 builds por classe
    builds_by_class[class_name] = builds_by_class[class_name][:10]
    
    # 3. Salvar
    with open(BUILD_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(builds_by_class, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ Build salva: {class_name} - {build_data.get('build_name', 'N/A')}")

def test_single_url(url: str, class_name: str):
    """Testa a extração de uma única URL."""
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🎯 TESTANDO EXTRAÇÃO DE BUILD")
    logger.info(f"URL: {url}")
    logger.info(f"Classe: {class_name}")
    logger.info(f"{'='*60}\n")
    
    # 1. Fetch do artigo
    logger.info("📥 1/3 - Buscando artigo...")
    article_text = fetch_build_article(url)
    
    if not article_text:
        logger.error("❌ Falha ao buscar artigo.")
        return None
    
    logger.info(f"✅ Artigo obtido ({len(article_text)} caracteres).")
    
    # 2. Extração LLM
    logger.info("\n🤖 2/3 - Extraindo dados com LLM...")
    build_data = extract_build_with_llm(article_text, class_name, url)
    
    if not build_data:
        logger.error("❌ Falha na extração LLM.")
        return None
    
    logger.info(f"✅ Extração concluída.")
    
    # 3. Salvar
    logger.info("\n💾 3/3 - Salvando build...")
    save_build_to_file(build_data)
    
    # 4. Mostrar resumo
    logger.info(f"\n{'='*60}")
    logger.info("📊 RESUMO DA BUILD EXTRAÍDA")
    logger.info(f"{'='*60}")
    logger.info(f"Nome: {build_data.get('build_name', 'N/A')}")
    logger.info(f"Classe: {build_data.get('class', 'N/A')}")
    logger.info(f"Versão: {build_data.get('version', 'N/A')}")
    
    total_skills = sum(
        len([a for a in tier.get('actions', []) if a.get('type') == 'Skill'])
        for tier in build_data.get('skill_tree_leveling', [])
    )
    logger.info(f"Total de Skills: {total_skills}")
    
    logger.info(f"\n✅ Build extraída e salva com sucesso!")
    logger.info(f"{'='*60}\n")
    
    return build_data

# ===== MAIN =====
if __name__ == '__main__':
    # URLs de teste para diferentes classes
    TEST_BUILDS = [
        {
            "url": "https://mobalytics.gg/poe-2/builds/earthquake-leveling-guide",
            "class": "Warrior"
        },
        {
            "url": "https://maxroll.gg/poe2/build-guides/lightning-arrow-deadeye-leveling",
            "class": "Ranger"
        }
    ]
    
    print("\n🚀 LLM EXTRACTOR V2 - Sistema de Extração Melhorado")
    print("="*60)
    
    for build_info in TEST_BUILDS:
        result = test_single_url(build_info["url"], build_info["class"])
        if result:
            # Mostrar preview das primeiras skills
            print("\n📋 Preview das Skills Extraídas:")
            for tier in result.get('skill_tree_leveling', [])[:2]:  # Primeiras 2 fases
                print(f"\n  {tier.get('level_range', 'N/A')}:")
                for action in tier.get('actions', [])[:3]:  # Primeiras 3 skills
                    if action.get('type') == 'Skill':
                        skill_name = action.get('name', 'N/A')
                        passives = action.get('passives', [])
                        print(f"    • {skill_name}")
                        if passives:
                            print(f"      Passives: {', '.join(passives[:3])}")
        
        print("\n" + "="*60 + "\n")
        time.sleep(3)  # Pausa entre extrações