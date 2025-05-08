import os
from typing import Optional, Dict, Any

import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from markups import (
    main_menu_markup,
    stats_menu_markup,
    socials_female_menu_markup,
    socials_menu_markup,
    socials_male_menu_markup
)
from services.last_scoreboard import build_bo3_url, get_furia_scoreboard
from services.next_match import fetch_upcoming_matches
from services.result_matcher import get_latest_match_info
from services.roster_service import get_current_roster


# --- Configuration & Constants ---
PANDASCORE_TOKEN: str = os.getenv("PANDASCORE_TOKEN", "")
HEADERS: Dict[str, str] = {
    'User-Agent': 'FuriaResultsBot/1.0',
    'Referer': 'https://liquipedia.net/counterstrike/FURIA'
}
TEAM_SLUG: str = 'FURIA'

# Stores live states per chat_id
live_states: Dict[int, Dict[str, Any]] = {}


async def fetch_live_match() -> Optional[Dict[str, Any]]:
    """
    Fetch current live CS:GO match from PandaScore API.
    Returns a dict with round, score, team1, team2 or None if no live match.
    """
    url = "https://api.pandascore.co/csgo/matches/live"
    params = {"token": PANDASCORE_TOKEN}

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    if not data:
        return None

    match = data[0]
    return {
        "round": match["live"]["round"],
        "score": f"{match['scores']['1']}x{match['scores']['2']}",
        "team1": match["opponents"][0]["opponent"]["name"],
        "team2": match["opponents"][1]["opponent"]["name"]
    }




# --- Live Status Handlers ---
async def start_live(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Begin periodic live match updates every 45 seconds."""
    chat_id = update.effective_chat.id
    state = live_states.setdefault(chat_id, {})

    if state.get("status") == "active":
        await update.message.reply_text("🔴 Live status já ativo.")
        return

    live_states[chat_id] = {"status": "active", "message_id": None, "round": None}
    context.job_queue.run_repeating(
        check_live, interval=45, first=0, chat_id=chat_id, name=str(chat_id)
    )
    await update.message.reply_text("✅ Live status iniciado! Atualizações a cada 45s.")


async def stop_live(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop the live match updates and clear state."""
    chat_id = update.effective_chat.id
    jobs = context.job_queue.get_jobs_by_name(str(chat_id))

    if not jobs:
        await update.message.reply_text("❌ Nenhum live ativo.")
        return

    for job in jobs:
        job.schedule_removal()
    live_states.pop(chat_id, None)
    await update.message.reply_text("🛑 Live status desativado.")


async def check_live(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Job callback to fetch live match and update or send message."""
    job = context.job
    chat_id = job.chat_id
    state = live_states.get(chat_id)

    # If deactivated
    if not state or state.get("status") != "active":
        job.schedule_removal()
        return

    info = await fetch_live_match()
    if not info:
        await context.bot.send_message(chat_id, "❌ Falha ao obter dados ao vivo.")
        return

    text = (
        f"🔴 Live Round {info['round']}\n"
        f"{info['team1']} vs {info['team2']}\n"
        f"Placar: {info['score']}"
    )
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("⬅️ Anterior", callback_data="prev_round"),
        InlineKeyboardButton("➡️ Próxima", callback_data="next_round"),
    ]])

    msg_id = state.get("message_id")
    if msg_id:
        try:
            current_msg = await context.bot.get_message(chat_id, msg_id)
        except Exception:
            current_msg = None

        if current_msg and current_msg.text == text and current_msg.reply_markup == keyboard:
            return

        await context.bot.edit_message_text(
            text=text,
            chat_id=chat_id,
            message_id=msg_id,
            reply_markup=keyboard
        )
    else:
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard
        )
        state["message_id"] = msg.message_id


async def round_nav_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle manual navigation between rounds in the live status message."""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id
    state = live_states.get(chat_id)

    if not state:
        return

    current = state.get("round", 1)
    state["round"] = current + 1 if query.data == "next_round" else max(1, current - 1)

    await query.edit_message_text(
        text=f"🔄 Rodada manual: {state['round']}",
        reply_markup=query.message.reply_markup
    )



# --- User Poll for Favorite Player ---
async def send_cheer_poll(
    chat_id: int,
    bot,
    team_slug: str = TEAM_SLUG
) -> None:
    """Send a non-anonymous poll asking which player will shine."""
    try:
        options = await get_current_roster(team_slug)
    except Exception as e:
        options = []
        await bot.send_message(chat_id, f"❌ Ocorreu um erro: {e}. Usando lista padrão de jogadores.")

    if not options:
        options = ["yuurih", "KSCERATO", "FalleN", "molodoy", "YEKINDAR"]

    await bot.send_poll(
        chat_id=chat_id,
        question="Quem vai brilhar hoje? 🌟",
        options=options,
        is_anonymous=False,
        allows_multiple_answers=False
    )




# --- Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message and show main menu."""
    context.user_data.setdefault("female", False)
    await update.message.reply_text(
        "🔥 Bem-vindo fã da FURIA! 💥 Escolha uma opção:",
        reply_markup=main_menu_markup(context.user_data["female"])
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display help information."""
    help_text = (
        "/start - Acessar menu principal\n"
        "/live(beta) - Status de partidas ao vivo via PandaScore\n"
    )
    await update.message.reply_text(help_text)

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle all inline button callbacks from the main menu."""
    query = update.callback_query
    await query.answer()
    await context.bot.send_chat_action(
        chat_id=query.message.chat_id,
        action=ChatAction.TYPING
    )

    data = query.data
    female = context.user_data.get("female", False)
    team_slug = "FURIA_Female" if female else TEAM_SLUG
    # Draft5 slug
    draft_slug = "1200-FURIA-fem" if female else "330-FURIA"

    # Social menus
    if data in ("menu_socials", "socials_female", "socials_male"):
        return await socials_button_handler(update, context, female)

    # Toggle lineup
    if data == "toggle_line":
        female = not female
        context.user_data["female"] = female
        label = "feminina" if female else "masculina"
        return await query.edit_message_text(
            text=f"✅ Agora usando a line {label}!",
            reply_markup=main_menu_markup(female),
            parse_mode="Markdown"
        )

    # Next match
    if data == "next_match":
        # retry twice on timeout
        upcoming = []
        for _ in range(2):
            try:
                upcoming = await fetch_upcoming_matches(draft_slug)
                break
            except PlaywrightTimeoutError:
                continue
            except Exception:
                try:
                    return await query.edit_message_text(
                        "❌ Erro ao buscar próximas partidas.",
                        reply_markup=main_menu_markup(female)
                    )
                except BadRequest:
                    return

        if not upcoming:
            try:
                return await query.edit_message_text(
                    "ℹ️ Ainda não há próximas partidas agendadas para essa line.",
                    reply_markup=main_menu_markup(female)
                )
            except BadRequest:
                return

        lines = [f"🔥 Próximas partidas - {'FEMININA' if female else 'MASCULINA'}"]
        for m in upcoming[:5]:
            opp = m['team2'] if m['team1'] == draft_slug else m['team1']
            lines.append(
            f"📅 {m['date']} às {m['time']} — {draft_slug} vs {opp} ({m['best_of']})\n"
            f"🏆 {m['tournament']}"
        )
        lines.append(f"🔗 Onde ver:\n https://draft5.gg/equipe/{draft_slug}/proximas-partidas")
    
        text = "\n\n".join(lines)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Atualizar", callback_data="next_match")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="menu_main")]
        ])
        try:
            return await query.edit_message_text(
                text=text,
                reply_markup=keyboard
            )
        except BadRequest:
            return

    # Last result
    if data == "last_result":
        latest = get_latest_match_info(team_slug, HEADERS)
        if latest:
            text = (
                f"🏆 Último Resultado 🏆\n"
                f"• Data: {latest['Date']}\n"
                f"• Evento: {latest['Event']}\n"
                f"• Adversário: {latest['Opponent']}\n"
                f"• Placar: {latest['Score']}\n"
                f"• Resultado: {latest['Result']}"
            )
        else:
            text = "❌ Nenhuma informação encontrada."

        return await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=main_menu_markup(female)
        )

    # Statistics menu
    if data == "menu_stats":
        return await query.edit_message_text(
            "📊 Estatísticas – escolha:",
            reply_markup=stats_menu_markup()
        )

    # Top fragger stats
    if data == "stats_top":
        dynamic_headers = {
            'User-Agent': 'FuriaResultsBot/1.0',
            'Referer': f'https://liquipedia.net/counterstrike/{team_slug}'
        }
        url = build_bo3_url(team_slug, dynamic_headers)

        if not url:
            return await query.edit_message_text(
                "❌ Não foi possível gerar a URL do jogo.",
                reply_markup=main_menu_markup(female)
            )

        board = get_furia_scoreboard(url)
        if not board:
            return await query.edit_message_text(
                "❌ Não encontrei o placar dos jogadores.",
                reply_markup=main_menu_markup(female)
            )

        lines = ["🥇 Estatísticas da última partida: 🥇\n"]

        # 1) MVP — name
        mvp_nick, mvp_stats = next(iter(board.items()))
        lines.append(f"🏆 MVP – {mvp_nick} 🏆")

        lines.append("")

        # 2) Scoreboard
        lines.append("📋 Scoreboard completo:")
        for nick, stats in board.items():
            lines.append(
                f"• {nick}: {stats['Kills']}/{stats['Deaths']}/{stats['Assists']} SCORE: {stats['Score']}"
            )

        return await query.edit_message_text(
            text="\n".join(lines),
            reply_markup=main_menu_markup(female)
        )

    # Cheer poll
    if data == "cheer_poll":
        await send_cheer_poll(
            chat_id=update.effective_chat.id,
            bot=context.bot,
            team_slug=team_slug
        )
        return await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🎮 Enquete enviada!",
            reply_markup=main_menu_markup(female)
        )

    # Return to main menu
    if data == "menu_main":
        return await query.edit_message_text(
            "🔥 Bem-vindo fã da FURIA! 💥 Escolha uma opção:",
            reply_markup=main_menu_markup(female)
        )
    
    # TODO: Insert URL https://bo3.gg
    
    # Unknown callback
    await query.edit_message_text(
        "❓ Opção inválida.",
        reply_markup=main_menu_markup(female)
    )

async def socials_button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    female: bool
) -> None:
    """Handle navigation in the social media submenu."""
    query = update.callback_query
    await query.answer()

    if query.data == "socials_female":
        text = "🌟 Redes Sociais da Line Feminina:"
        markup = socials_female_menu_markup()
    elif query.data == "socials_male":
        text = "🔥 Redes Sociais da Line Masculina:"
        markup = socials_male_menu_markup()
    else:
        text = "Escolha uma rede social:"
        markup = socials_menu_markup()

    await query.edit_message_text(text=text, reply_markup=markup)
