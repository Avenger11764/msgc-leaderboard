import logging
import os
import re
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import firebase_admin
from firebase_admin import credentials, firestore

# --- CONFIGURATION ---
# On Railway, these will be set as environment variables.
TELEGRAM_BOT_TOKEN = os.environ.get("8432697262:AAERRuVpN5l8jBCc38dq3H6nG6Z7tw_H4rc")
FIREBASE_APP_ID = "msgc-power-store" 
# Get Firebase credentials from environment variable
FIREBASE_CREDENTIALS_JSON = os.environ.get("FIREBASE_CREDENTIALS_JSON")


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Firebase
try:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("FATAL: TELEGRAM_BOT_TOKEN environment variable not set.")
        exit()
    if not FIREBASE_CREDENTIALS_JSON:
        logger.error("FATAL: FIREBASE_CREDENTIALS_JSON environment variable not set.")
        exit()

    # Load credentials from the JSON string in the environment variable
    cred_dict = json.loads(FIREBASE_CREDENTIALS_JSON)
    cred = credentials.Certificate(cred_dict)
    
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    logger.info("Firebase initialized successfully.")

except Exception as e:
    logger.error(f"FATAL: Failed to initialize: {e}")
    db = None
    exit()

# --- HELPER FUNCTIONS ---

def escape_markdown_v2(text: str) -> str:
    """Escapes characters for Telegram's MarkdownV2 parse mode."""
    if not text:
        return ""
    escape_chars = r'([_*\[\]()~`>#+\-=|{}.!])'
    return re.sub(escape_chars, r'\\\1', text)

# --- COMMAND HANDLERS ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command."""
    await update.message.reply_text(
        "🏆 Welcome to the Mavericks Tournament Leaderboard Bot! 🏆\n\n"
        "Use the /leaderboard command in your group chat to see the current standings."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the help message."""
    await update.message.reply_text(
        "This bot has only one command:\n\n"
        "/leaderboard - Shows the player rankings by coin balance. This command only works in a group chat."
    )

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the leaderboard of player coin balances."""
    logger.info("Leaderboard command triggered.")
    if update.message.chat.type == 'private':
        await update.message.reply_text("This command can only be used in a group chat.")
        return

    if not db:
        await update.message.reply_text("Database not available. Cannot fetch leaderboard.")
        return

    try:
        users_ref = db.collection(f'artifacts/{FIREBASE_APP_ID}/users')
        all_user_docs = users_ref.stream()

        players = []
        for doc in all_user_docs:
            player_data = doc.to_dict()
            if player_data:
                players.append({
                    'name': player_data.get('first_name', 'Unknown Player'),
                    'coins': player_data.get('coins', 0)
                })

        if not players:
            await update.message.reply_text("No players have registered in the tournament yet. The leaderboard is empty.")
            return

        sorted_players = sorted(players, key=lambda p: p['coins'], reverse=True)
        leaderboard_text = "🏆 *Mavericks Tournament 3\\.0 Leaderboard* 🏆\n\n"
        rank_emojis = {1: '🥇', 2: '🥈', 3: '🥉'}

        for i, player in enumerate(sorted_players):
            rank = i + 1
            rank_emoji = rank_emojis.get(rank, f" {rank}\\.")
            safe_name = escape_markdown_v2(player['name'])
            leaderboard_text += f"{rank_emoji} *{safe_name}*: {player['coins']} PC\n"
        
        await update.message.reply_text(leaderboard_text, parse_mode='MarkdownV2')
        logger.info(f"Leaderboard displayed successfully in chat: {update.message.chat.title}")

    except Exception as e:
        logger.error(f"Error in /leaderboard command: {e}", exc_info=True)
        await update.message.reply_text("An error occurred while fetching the leaderboard.")


def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("leaderboard", leaderboard_command))

    logger.info("Leaderboard Bot is starting...")
    application.run_polling()
    logger.info("Leaderboard Bot has stopped.")

if __name__ == "__main__":
    main()

