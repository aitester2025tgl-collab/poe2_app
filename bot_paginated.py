# bot_paginated.py - VERSÃO FINAL (SEGURA COM .ENV E LÓGICA DE CLASSE ROBUSTA)

import json
import logging
import re 
import os # <--- CORREÇÃO CRÍTICA AQUI!
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from typing import Dict, Any, List, Set, Tuple
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== CONFIGURAÇÕES GERAIS =====
JSON_FILE = "poe2_builds.json"
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') # Lendo a partir da variável de ambiente

# -----------------------------------------------------
# Verificação Crítica do Token: O bot não deve arrancar sem o token
if not TELEGRAM_BOT_TOKEN:
    logger.error("❌ ERRO: TELEGRAM_BOT_TOKEN não encontrado no ficheiro .env. Parando a execução.")
    exit(1)
# -----------------------------------------------------

POE2_CLASSES = [
    "Warrior", "Monk", "Mercenary", "Sorceress", "Witch", 
    "Ranger", "Huntress", "Druid", "Duelist", "Marauder", 
    "Shadow", "Templar"
]

# ===== UTILITIES =====

def load_builds() -> Dict[str, Any]:
    """Carrega as builds do ficheiro JSON, com gestão de erros."""
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"❌ FICHEIRO NÃO ENCONTRADO: {JSON_FILE}. Execute o pipeline de dados!")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"❌ ERRO JSON: O ficheiro {JSON_FILE} está mal formatado. {e}")
        return {}
    except Exception as e:
        logger.error(f"❌ ERRO GERAL ao carregar {JSON_FILE}: {e}")
        return {}

def format_build(build: Dict[str, Any]) -> str:
    """Formata os dados de uma build para serem exibidos no Telegram (Markdown)."""
    
    # Ordenar as skills para garantir a ordem de exibição
    build_skills = []
    if 'skill_tree_leveling' in build and build['skill_tree_leveling']:
        for step in build['skill_tree_leveling']:
            level_range = step.get('level_range', 'N/A')
            step_skills = []
            
            for action in step.get('actions', []):
                if action.get('type') == 'Skill':
                    name = action.get('name', 'N/A')
                    # passives = ", ".join(action.get('passives', []))
                    step_skills.append(f"• `{name}`")
            
            if step_skills:
                build_skills.append(f"\n*{level_range}*\n" + "\n".join(step_skills))

    skills_text = "\\n".join(build_skills) if build_skills else "\\n_Nenhuma skill encontrada._"
    
    # Metadados de validação
    details = build.get('validation_details', {})
    confidence = details.get('confidence', 0.0)
    
    # Estrutura do texto final
    text = (
        f"**{build.get('build_name', 'Build Sem Nome')}**\n"
        f"*{build.get('class', 'N/A Class')} | {build.get('version', 'N/A Version')}*\n"
        f"---"
        f"\\n🔗 [Link Original]({build.get('url', 'N/A')})"
        f"\\n⭐ Recomendação: **{build.get('reputation', 0):,}** (Score Dinâmico)"
        f"\\n🔬 Confiança GT: `{confidence:.1%}`"
        f"\\n---"
        f"\\n**Skills de Leveling:**{skills_text}"
    )
    
    return text

def build_class_keyboard(class_name: str, current_index: int, total_builds: int) -> InlineKeyboardMarkup:
    """Cria o teclado de paginação para uma classe específica."""
    
    buttons = []
    # Primeira linha: Navegação (<< Anterior Próxima >>)
    nav_row = []
    
    # Botão Anterior
    if current_index > 0:
        nav_row.append(InlineKeyboardButton("◀️ Anterior", callback_data=f"class_{class_name}_{current_index - 1}"))
    
    # Contador
    nav_row.append(InlineKeyboardButton(f"[{current_index + 1}/{total_builds}]", callback_data="ignore"))
    
    # Botão Próxima
    if current_index < total_builds - 1:
        nav_row.append(InlineKeyboardButton("Próxima ▶️", callback_data=f"class_{class_name}_{current_index + 1}"))
    
    buttons.append(nav_row)
    
    # Segunda linha: Voltar ao Menu Principal
    buttons.append([InlineKeyboardButton("🏠 Menu Principal", callback_data="start_menu")])
    
    return InlineKeyboardMarkup(buttons)

# ===== COMANDOS =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia a mensagem de boas-vindas e o teclado com as classes."""
    logger.info("-> Comando /start recebido.")
    
    builds = load_builds()
    
    if not builds:
        logger.warning("Nenhuma build carregada. Enviando mensagem de erro.")
        await update.message.reply_text(
            "❌ *Erro de Dados:* O ficheiro 'poe2_builds.json' está vazio ou falhou ao carregar. Por favor, execute o 'update_builds_online.py --force' para carregar as builds.",
            parse_mode='Markdown'
        )
        return

    # Filtra apenas as classes que têm builds carregadas.
    # Esta é a lógica CRÍTICA para criar os botões.
    available_classes = [cls for cls, cls_builds in builds.items() if cls_builds]

    if not available_classes:
         logger.warning("Ficheiro carregado, mas nenhuma classe tem builds válidas.")
         await update.message.reply_text(
            "❌ *Erro de Conteúdo:* O ficheiro JSON não contém builds válidas. Execute 'update_builds_online.py --force' novamente.",
            parse_mode='Markdown'
        )
         return
    
    logger.info(f"Classes disponíveis: {', '.join(available_classes)}")
    
    # Cria os botões de classe (2 por linha para ser mais compacto)
    keyboard = []
    # Cria uma lista de botões com 2 por linha
    for i in range(0, len(available_classes), 2):
        row = []
        # Primeiro botão
        cls1 = available_classes[i]
        # O callback_data sempre começa em '0' (a primeira build)
        row.append(InlineKeyboardButton(cls1, callback_data=f"class_{cls1}_0"))
        
        # Segundo botão (se existir)
        if i + 1 < len(available_classes):
            cls2 = available_classes[i + 1]
            row.append(InlineKeyboardButton(cls2, callback_data=f"class_{cls2}_0"))
            
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "*Bem-vindo ao PoE 2 Build Finder!*\\n\\nEscolha uma classe para ver as builds mais recomendadas (baseadas no nosso Score Dinâmico):", 
        reply_markup=reply_markup,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processa cliques nos botões de paginação e seleção de classe."""
    query = update.callback_query
    await query.answer() # Fecha o pop-up de 'loading' no Telegram
    
    data = query.data
    
    # Lógica de retorno ao menu principal
    if data == "start_menu":
        await start(update, context)
        return
    
    # Ignorar o botão de contador
    if data == "ignore":
        return

    # Extrai o nome da classe e o índice/ação da paginação
    match = re.match(r"class_(\w+)_(\d+)$", data)
    if not match:
        logger.error(f"Padrão de callback_data desconhecido: {data}")
        await query.edit_message_text("❌ Erro de processamento. Tente novamente.")
        return

    cls, index_str = match.groups()
    index = int(index_str)
    
    builds = load_builds()
    class_builds = builds.get(cls, [])
    
    if not class_builds:
        await query.edit_message_text(f"❌ Nenhuma build encontrada para a classe **{cls}**.")
        return

    # 1. Ordenar as Builds pela Reputação (Score Dinâmico)
    try:
        class_builds.sort(key=lambda b: b.get('reputation', 0), reverse=True)
    except Exception as e:
        logger.error(f"Erro ao ordenar builds para {cls}: {e}")

    total_builds = len(class_builds)
    
    # Garantir que o índice está dentro dos limites
    index = max(0, min(index, total_builds - 1))
        
    # 2. Mostrar a Build
    build_to_display = class_builds[index]
    build_text = format_build(build_to_display)
    reply_markup = build_class_keyboard(cls, index, total_builds)
    
    try:
        await query.edit_message_text(
            text=build_text,
            reply_markup=reply_markup,
            parse_mode='Markdown', 
            disable_web_page_preview=True 
        )
    except Exception as e:
        logger.error(f"Erro ao editar mensagem: {e}")
        try:
            # Tentar enviar como uma nova mensagem se a edição falhar (pode ser problema de tamanho)
            await query.message.reply_text(
                "❌ Erro ao editar a build. Pode ser um problema de formato ou tamanho. Por favor, tente novamente no menu principal.",
                parse_mode='Markdown'
            )
        except:
            pass


# ===== INICIALIZAÇÃO =====
def main():
    """Roda o bot."""
    logger.info("--- INICIALIZAÇÃO DO BOT ---")
    
    # O exit(1) já foi feito acima, garantindo que o token existe.
    
    try:
        # Usa ApplicationBuilder
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        logger.info("✅ Telegram Application Builder inicializado.")
        
        # Handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_handler))
        logger.info("✅ Handlers registados: /start e botões.")

        logger.info("🚀 Bot a escutar. Envie /start no Telegram.")
        application.run_polling(poll_interval=1.0) # Uso de polling

    except Exception as e:
        logger.error(f"❌ ERRO FATAL AO INICIAR O BOT: {e}")
        
if __name__ == '__main__':
    main()