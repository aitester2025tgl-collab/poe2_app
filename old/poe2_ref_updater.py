# poe2_ref_updater.py (VERSÃO HÍBRIDA: BS4 para EXTRAÇÃO, LLM para LIMPEZA)

import json
import requests
import os
import logging
from ollama import Client 
from typing import Dict, Any, Optional, List, Set, Tuple
from bs4 import BeautifulSoup 

# Logging em INFO para mostrar os passos principais
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== CONFIGURAÇÕES GERAIS =====
OLLAMA_MODEL = 'mistral' 
OLLAMA_TEMPERATURE = 0.1 
REF_DATA_FILE = "poe2_ref_data.json"

# FOCO ÚNICO: URL do Game8 (Mantido por ter HTML estático)
SINGLE_SOURCE_URL = "https://game8.co/games/Path-of-Exile-2/archives/487605" 
SOURCE_NAME = "game8.co"

# Inicializa o Cliente Ollama
try:
    OLLAMA_CLIENT = Client(timeout=120.0)
    OLLAMA_CLIENT.list()
    logger.info("✅ Ollama Client conectado.")
except Exception as e:
    logger.error(f"❌ ERRO FATAL: Não foi possível conectar ao Ollama. Certifique-se que o servidor Ollama está a correr. Erro: {e}")
    exit(1)


# ===== UTILITIES DE REDE E FICHEIROS =====
def fetch_wiki_html(url: str) -> Optional[str]:
    """Busca o conteúdo HTML da URL."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        html_content = response.text
        logger.info(f"   -> HTML Fetch: {url}. Tamanho: {len(html_content)} bytes.")
        
        return html_content
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Erro ao buscar HTML de {url}: {e}")
        return None

def load_current_reference_data() -> Dict[str, Any]:
    """Carrega o Ground Truth existente ou retorna um objeto vazio, com a estrutura mínima."""
    default_data = {
        "SKILL_GEMS_ACTIVE": {},
        "SKILL_GEMS_SPIRIT": {},
        "ALL_PASSIVE_NAMES": set()
    }
    if not os.path.exists(REF_DATA_FILE):
        return default_data
    try:
        with open(REF_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            data["SKILL_GEMS_ACTIVE"] = data.get("SKILL_GEMS_ACTIVE", data.pop("ACTIVE_SKILL_GEMS", {}))
            data["SKILL_GEMS_SPIRIT"] = data.get("SKILL_GEMS_SPIRIT", {})
            data["ALL_PASSIVE_NAMES"] = set(data.get("ALL_PASSIVE_NAMES", []))
            return data
            
    except Exception as e:
        logger.warning(f"⚠️ Erro ao carregar {REF_DATA_FILE}: {e}. A usar estrutura vazia.")
        return default_data

def save_reference_data(data: Dict[str, Any]):
    """Salva o Ground Truth, convertendo o Set de passivas de volta para uma Lista."""
    data["ALL_PASSIVE_NAMES"] = sorted(list(data.get("ALL_PASSIVE_NAMES", []))) 
    
    with open(REF_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ===== PASSO 1.1: EXTRAÇÃO BRUTA COM BS4 (NOVO) =====
def extract_raw_names_with_bs4(html_content: str) -> Optional[List[str]]:
    """Usa Beautiful Soup para extrair nomes de skills com seletor robusto."""
    
    logger.info("   -> A extrair Nomes Brutos usando Beautiful Soup (Pré-limpeza)...")
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Seletor: o div que contém o corpo do artigo
    main_content = soup.find('div', class_='g8-container__main') or soup.find('article')
    if not main_content:
        logger.warning("   ⚠️ Não foi possível encontrar o contentor principal. Usando a página inteira.")
        main_content = soup
    
    # Tentativa de extração: procurar links <a> dentro de células de tabela <td>
    extracted_items = main_content.find_all(['td', 'a'])
    
    raw_names = []
    
    for item in extracted_items:
        text = item.get_text(strip=True)
        # Se for um link e o texto tiver tamanho razoável (provavelmente um nome)
        if item.name == 'a' and 'href' in item.attrs and 4 < len(text) < 40:
            raw_names.append(text)
        # Se for uma célula de tabela, tem de começar com letra maiúscula (nome próprio)
        elif item.name == 'td' and 4 < len(text) < 40 and text[0].isupper():
            raw_names.append(text)
        
    final_names = list(set(raw_names))
    
    # Diagnóstico de BS4
    logger.info(f"   -> BS4 extraiu {len(final_names)} nomes brutos. (Ex: {final_names[:5] if final_names else 'Nenhum'})")
    
    if not final_names:
        logger.warning("   ⚠️ Beautiful Soup falhou na extração. Tentativa de LLM ignorada.")
        return None
        
    return final_names

# ===== PASSO 1.2: LIMPEZA E FORMATAÇÃO COM LLM (ADAPTADO) =====
def clean_names_with_llm(raw_names: List[str]) -> Optional[List[str]]:
    """Usa o LLM para limpar a lista bruta de nomes extraída pelo BS4."""
    
    logger.info(f"   -> A limpar {len(raw_names)} nomes brutos usando o LLM...")

    # Fornece a lista bruta como string simples
    raw_names_str = ", ".join(raw_names)

    prompt = f"""
    A sua tarefa é limpar e validar esta lista bruta de nomes de Skills e Habilidades extraídos de uma wiki.

    **LISTA BRUTA DE NOMES:**
    ---
    {raw_names_str}
    ---

    **REGRAS DE LIMPEZA E VALIDAÇÃO CRUCIAIS:**
    1.  **Validade:** Mantenha apenas nomes que são claramente nomes de Skills Ativas (e.g., 'Fireball', 'Sunder', 'Summon Wolf').
    2.  **Remover:** Exclua nomes que sejam Passivas, Atributos, títulos de secções, ou lixo.
    3.  **Limpeza:** Garanta que cada nome está limpo (sem números, parênteses ou texto adicional).

    **Formato de Saída OBRIGATÓRIO (JSON):**
    {{
      "ALL_SKILL_NAMES": [
        "Spark",
        "Sunder",
        "Summon Wolf"
      ]
    }}
    """
    
    schema = {
        "type": "object",
        "properties": {
            "ALL_SKILL_NAMES": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Uma lista de todos os nomes únicos de Skills Ativas limpos e validados."
            }
        },
        "required": ["ALL_SKILL_NAMES"]
    }

    try:
        response = OLLAMA_CLIENT.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
            format='json',
            options={'temperature': OLLAMA_TEMPERATURE}
        )
        
        json_output = response['response'].strip()
        if json_output.startswith('```json'):
            json_output = json_output[7:-3].strip()
        elif json_output.startswith('```'):
            json_output = json_output[3:-3].strip()

        extracted_data = json.loads(json_output)
        clean_names = [name.strip() for name in extracted_data.get("ALL_SKILL_NAMES", []) if name.strip()]
        
        logger.info(f"   ✅ Limpeza de nomes com LLM concluída. {len(clean_names)} nomes finais validados.")
        return clean_names
        
    except json.JSONDecodeError as e:
        logger.error(f"   ❌ Erro de JSONDecode (Fonte: {SOURCE_NAME}): O LLM não devolveu JSON válido na limpeza. Erro: {e}")
        logger.error(f"   ❌ CONTEÚDO BRUTO DO LLM QUE FALHOU A ANÁLISE (500 chars): {json_output[:500]}...")
        return None
    except Exception as e:
        logger.error(f"   ❌ Erro durante a limpeza do Ollama: {e}")
        return None


# ===== FUNÇÃO PRINCIPAL: COLEÇÃO E SALVAMENTO =====
def update_reference_data():
    """Função principal para atualizar o ficheiro de referência a partir da fonte única."""
    logger.info(f"\n--- A iniciar Coleção Híbrida de Nomes de Skills (Fonte: {SINGLE_SOURCE_URL}) ---")
    
    # 1. Buscar HTML
    html_content = fetch_wiki_html(SINGLE_SOURCE_URL)
    if not html_content:
        logger.error("❌ Não foi possível obter o HTML. A sair.")
        return

    # 2. Extração Bruta com BS4
    raw_names = extract_raw_names_with_bs4(html_content)
    
    if not raw_names:
        logger.warning("⚠️ Beautiful Soup falhou. O Ground Truth não foi atualizado.")
        return

    # 3. Limpeza e Validação com LLM
    final_names = clean_names_with_llm(raw_names)
    
    if not final_names:
        logger.warning("⚠️ O LLM falhou na limpeza. O Ground Truth não foi atualizado.")
        return

    # 4. Carregar dados existentes e fazer o merge simples
    ref_data = load_current_reference_data()
    
    skills_active_before = len(ref_data["SKILL_GEMS_ACTIVE"])
    total_added = 0
    
    # 5. Adicionar todos os nomes à lista de Skills Ativas com nível 1 (placeholder)
    for name in final_names:
        if name not in ref_data["SKILL_GEMS_ACTIVE"]:
            # Adiciona a skill se não existir, usa 1 como nível mínimo (placeholder)
            ref_data["SKILL_GEMS_ACTIVE"][name] = 1 
            total_added += 1
            
    # 6. Salvar o resultado
    save_reference_data(ref_data)
        
    final_skills_active = len(ref_data["SKILL_GEMS_ACTIVE"])

    logger.info(f"\n✅ COLEÇÃO DE NOMES CONCLUÍDA COM SUCESSO!")
    logger.info(f"  - Skills Ativas (SKILL_GEMS_ACTIVE): {skills_active_before} -> {final_skills_active} (+{total_added} novos nomes)")
    logger.info(f"  - {final_skills_active} Nomes de Skills Totais coletados da fonte.")


if __name__ == '__main__':
    update_reference_data()