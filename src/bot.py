import os
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from handlers import (
    start,
    help_command,
    button_handler,
    start_live,
    stop_live,
    round_nav_handler
)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Main (Run Bot)
def main():
    logging.info("Seu Bot está Vivo!!")
    app = ApplicationBuilder().token(TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("live", start_live))
    app.add_handler(CommandHandler("stoplive", stop_live))

    # CallbackQueryHandlers
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(round_nav_handler, pattern="^(prev_round|next_round)$"))

    app.run_polling()

if __name__ == "__main__":
    main()
