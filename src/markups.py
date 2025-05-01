from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Main Menu
def main_menu_markup(female: bool) -> InlineKeyboardMarkup:
    toggle_label = (
        "🔄 Ir para Line Feminina ♀️🏳️‍🌈" if not female
        else "🔄 Ir para Line Masculina ♂️"
    )

    keyboard = [
        [InlineKeyboardButton("🗓 Próxima Partida", callback_data="next_match")],
        [InlineKeyboardButton("🎉 Enquete de Torcida", callback_data="cheer_poll")],
        [InlineKeyboardButton("🏆 Último Resultado", callback_data="last_result")],
        [InlineKeyboardButton("📊 Estatísticas", callback_data="menu_stats")],
        [InlineKeyboardButton(toggle_label, callback_data="toggle_line")],
        [InlineKeyboardButton("💬 Fale no WhatsApp (beta)", url="https://wa.me/5511993404466")],
        [InlineKeyboardButton("🌐 Redes Sociais", callback_data="menu_socials")]
    ]
    return InlineKeyboardMarkup(keyboard)


# Statistics Menu
def stats_menu_markup() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🥇 Top Fragger", callback_data="stats_top")],
        [InlineKeyboardButton("📈 Win Rate", callback_data="stats_wr")],
        [InlineKeyboardButton("🔙 Voltar", callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


# General Social Media Menu
def socials_menu_markup() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("📸 Instagram", url="https://www.instagram.com/furiagg"),
            InlineKeyboardButton("🐦 Twitter", url="https://twitter.com/FURIA"),
        ],
        [
            InlineKeyboardButton("🎵 TikTok", url="https://www.tiktok.com/@furiagg"),
            InlineKeyboardButton("▶️ YouTube", url="https://www.youtube.com/@FURIA"),
        ],
        [InlineKeyboardButton("🔙 Voltar", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


# Social Media Menu for Female Line
def socials_female_menu_markup() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("📸 Instagram (Feminina)", url="https://www.instagram.com/furiagg"),
            InlineKeyboardButton("🐦 Twitter (Feminina)", url="https://twitter.com/FURIA"),
        ],
        [
            InlineKeyboardButton("🎵 TikTok (Feminina)", url="https://www.tiktok.com/@furiagg"),
            InlineKeyboardButton("▶️ YouTube (Feminina)", url="https://www.youtube.com/@FURIA"),
        ],
        [InlineKeyboardButton("🔙 Voltar", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Social Media Menu for Male Line
def socials_male_menu_markup() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("📸 Instagram (Masculina)", url="https://www.instagram.com/furiagg"),
            InlineKeyboardButton("🐦 Twitter (Masculina)", url="https://twitter.com/FURIA"),
        ],
        [
            InlineKeyboardButton("🎵 TikTok (Masculina)", url="https://www.tiktok.com/@furiagg"),
            InlineKeyboardButton("▶️ YouTube (Masculina)", url="https://www.youtube.com/@FURIA"),
        ],
        [InlineKeyboardButton("🔙 Voltar", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)
