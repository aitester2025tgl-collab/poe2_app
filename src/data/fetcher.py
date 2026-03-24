# poe2_fetcher.py - VERSÃO FINAL: SEGURA E OTIMIZADA
import json
import time
import requests 
import os
from bs4 import BeautifulSoup 
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError 
from typing import Dict, Optional, List, Any
import logging
from ollama import Client 
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== CONFIG (Credenciais e Constantes) =====
GOOGLE_SEARCH_API_KEY = os.getenv('GOOGLE_SEARCH_API_KEY')
GOOGLE_SEARCH_ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID')

# Configuração do LLM (Ollama)
OLLAMA_CLIENT = Client(timeout=120.0)
OLLAMA_MODEL = 'mistral' 
OLLAMA_TEMPERATURE = 0.1 
MAX_RETRIES = 3

POE2_CLASSES = [
    "Warrior", "Monk", "Mercenary", "Sorceress", "Witch", 
    "Ranger", "Huntress", "Druid", "Duelist", "Marauder", 
    "Shadow", "Templar"
]

# CLASSES PARA IGNORAR TEMPORARIAMENTE
CLASSES_TO_SKIP = [
    "Druid", 
    "Duelist", 
    "Marauder", 
    "Shadow", 
    "Templar"
]

JSON_FILE = "poe2_builds.json"
MAX_BUILDS_PER_CLASS = 10 
LLM_PROCESSING_LIMIT = 3 

# ===== UTILITIES =====
def load_existing_builds(file_path=JSON_FILE) -> Dict[str, List[Dict[str, Any]]]:
    """Carrega as builds do ficheiro JSON."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Garante que é um dicionário
            if isinstance(data, dict):
                return data
            else:
                logger.warning("Formato incorreto detectado. A converter para dicionário.")
                return {}
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"❌ Erro ao decodificar JSON em {file_path}: {e}")
        return {}

def save_builds(data, file_path=JSON_FILE):
    """Guarda as builds atualizadas no ficheiro JSON."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def search_google(query, num=5):
    """Executa a busca no Google Custom Search API."""
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
        logger.error("❌ Google API credentials não encontradas no .env")
        return []
        
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_SEARCH_API_KEY)
        res = service.cse().list(q=query, cx=GOOGLE_SEARCH_ENGINE_ID, num=num).execute() 
        
        results = []
        for item in res.get("items", []):
            results.append({"title": item.get("title"), "link": item.get("link")})
        return results
        
    except HttpError as e:
        logger.warning(f"⚠️ Erro HTTP na busca do Google (Status: {e.resp.status}). Retornando 0 links.")
        return []
    except Exception as e:
        logger.error(f"❌ Erro inesperado na busca do Google: {e}. Retornando 0 links.")
        return []

def get_page_content(link):
    """Obtém o conteúdo HTML completo de um link."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(link, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        main_content = soup.find('main') or soup.find('article') or soup.body
        
        text_content = main_content.get_text(separator=' ', strip=True) if main_content else soup.get_text(separator=' ', strip=True)
        
        return text_content, soup.find('title').text if soup.find('title') else "Build Desconhecido"

    except requests.exceptions.RequestException as e:
        logger.warning(f"   ❌ Falha ao aceder/analisar o link {link}: {e}")
        return None, "Erro de Acesso"


def extract_build_details_with_llm(build_text: str, class_name: str, url: str) -> Optional[Dict]:
    """
    Usa o LLM (Ollama) para extrair detalhes de build estruturados.
    """
    
    system_prompt = f"""
    Você é um bot de extração de dados altamente preciso. A sua tarefa é analisar o conteúdo de uma build de Path of Exile 2 e extrair informações cruciais APENAS no formato JSON fornecido.

    --- REGRAS DE EXTRAÇÃO OBRIGATÓRIAS ---
    1. ESTRUTURA: A saída DEVE ser um objeto JSON único e bem formado, começando com '{{' e terminando com '}}'.
    2. SKILLS (name): O valor DEVE ser o NOME CANÔNICO EXATO da Skill Ativa (ex: "Boneshatter", "Arc") ou Passiva Chave (ex: "Resolute Technique"). NUNCA use títulos de build, frases irrelevantes ou lixo.
    3. PASSIVES (Lista): O campo 'passives' deve ser uma lista de strings com os nomes exatos das Passivas Notáveis/Keystones. Se não houver, use uma lista vazia ([]).
    4. REQUIRED_LEVEL: O valor DEVE ser um número inteiro (e.g., 1, 12). Se o nível não for explicitamente mencionado, use o número 0.
    5. REPUTATION: Deve ser o número de visualizações/votos. Se não for encontrado, use um valor base de 50000.
    6. LEVEL_RANGE: Divida o nivelamento em fases (ex: '1-10', 'Act 1'). Se não houver informação, use 'Full Leveling'.
    
    A classe desta build é: {class_name}.
    
    Formato de Saída (DEVE ser JSON válido):
    {{
      "build_name": "Nome da Build",
      "class": "{class_name}",
      "version": "0.3",
      "reputation": 50000,
      "skill_tree_leveling": [
        {{
          "level_range": "1-10",
          "actions": [
            {{ "type": "Skill", "name": "Nome da Skill Exato", "level": 1, "passives": ["Passiva Chave 1"] }}
          ]
        }}
      ]
    }}

    TEXTO DA BUILD:
    ---
    {build_text[:8000]}
    ---

    Produz apenas o objeto JSON.
    """
    
    for attempt in range(MAX_RETRIES):
        try:
            response = OLLAMA_CLIENT.chat(
                model=OLLAMA_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extraia a build para a classe {class_name}"}
                ],
                format='json',
                options={'temperature': OLLAMA_TEMPERATURE}
            )
            
            json_str = response['message']['content'].strip()
            
            # Limpeza do output
            if json_str.startswith('```json'):
                json_str = json_str[7:-3].strip()
            elif json_str.startswith('```'):
                json_str = json_str[3:-3].strip()

            # Tentar analisar o JSON
            try:
                build_data = json.loads(json_str)
            except json.JSONDecodeError:
                logger.warning(f"   ⚠️ LLM (Tentativa {attempt+1}): JSON Inválido. Nova tentativa em 2s.")
                time.sleep(2)
                continue
            
            # Validar a estrutura básica
            if 'skill_tree_leveling' in build_data:
                build_data['reputation'] = int(build_data.get('reputation', 50000))
                build_data['class'] = class_name
                build_data['url'] = url
                
                return build_data
            else:
                logger.warning(f"   ⚠️ LLM (Tentativa {attempt+1}): Faltando 'skill_tree_leveling'. Nova tentativa em 2s.")
                time.sleep(2)
                continue
                
        except Exception as e:
            logger.error(f"❌ Erro na comunicação ou API do Ollama (Tentativa {attempt+1}): {e}. Nova tentativa em 5s.")
            time.sleep(5)
            continue

    logger.error(f"❌ Falha persistente na extração do LLM após {MAX_RETRIES} tentativas.")
    return None


def fetch_build_for_class(class_name, existing_builds: List[Dict]):
    logger.info(f"--- Processando {class_name} ---") 
    
    # Coletar URLs de builds que já foram processadas
    existing_urls = {build.get('url') for build in existing_builds if build.get('url')}

    query = f"Path of Exile 2 {class_name} best leveling build site:maxroll.gg OR site:mobalytics.gg"
    
    search_results = search_google(query, num=MAX_BUILDS_PER_CLASS)

    newly_extracted_builds: List[Dict] = []
    
    time.sleep(2) 
    
    if search_results:
        unprocessed_links = []
        
        # Filtrar: Encontrar links novos
        for result in search_results:
            link = result["link"]
            if link not in existing_urls:
                unprocessed_links.append(result)
        
        # Limitar: Processar apenas os top X links novos
        links_to_process = unprocessed_links[:LLM_PROCESSING_LIMIT]
        
        logger.info(f"   ✅ {len(search_results)} links encontrados. {len(existing_urls)} já processados. Processando {len(links_to_process)} novos.")

        if not links_to_process:
            logger.info(f"   ℹ️ Todos os links para {class_name} já foram processados.")
            return []

        for i, result in enumerate(links_to_process):
            link = result["link"]
            
            page_text, title = get_page_content(link)
            
            if page_text:
                build_data = extract_build_details_with_llm(page_text, class_name, link)
                
                if build_data:
                    newly_extracted_builds.append(build_data)
                    logger.info(f"   🎉 Build '{build_data.get('build_name', 'N/A')}' extraída com sucesso.")
                else:
                    logger.warning(f"   ❌ LLM falhou ao extrair dados para {link}.")

            time.sleep(5) 
            
    else:
        logger.warning(f"⚠️ Nenhuma busca retornou resultados para {class_name}.")
        
    return newly_extracted_builds

def update_all_builds():
    logger.info("INFO:__main__:Starting online build update...")
    data = load_existing_builds() 
    success_count = 0
    
    for cls in POE2_CLASSES:
        existing_builds = data.get(cls, [])
        
        # Filtro de classes
        if cls in CLASSES_TO_SKIP:
            logger.info(f"--- Pulando {cls} (Classe não lançada/baixa confiança) ---")
            if cls not in data:
                 data[cls] = []
            continue
        
        new_builds = fetch_build_for_class(cls, existing_builds) 
        
        # Merge: Fundir novas e antigas
        all_builds_dict = {build.get('url'): build for build in existing_builds}
        for build in new_builds:
             all_builds_dict[build.get('url')] = build
             
        combined_builds = list(all_builds_dict.values())
        
        # Ordenar pela reputação
        combined_builds.sort(key=lambda b: b.get('reputation', 0), reverse=True)
        
        # Manter apenas o Top 10
        final_builds = combined_builds[:MAX_BUILDS_PER_CLASS]
        
        data[cls] = final_builds 
        success_count += 1
        
    save_builds(data)
    logger.info(f"✅ Atualização do JSON terminada. {success_count}/{len(POE2_CLASSES)} classes processadas.")
    return True

if __name__ == "__main__":
    update_all_builds()