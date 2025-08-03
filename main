import logging
import os
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import firebase_admin
from firebase_admin import credentials, firestore

# --- CONFIGURATION ---
# IMPORTANT: Before running, you need to set up your credentials for this bot.
# 1. Create a file named 'config_leaderboard.py' in the same directory.
# 2. In config_leaderboard.py, add the following line with your bot's token:
#    TELEGRAM_BOT_TOKEN = "YOUR_NEW_LEADERBOARD_BOT_TOKEN"
# 3. Make sure the 'firebase_credentials.json' file from your Firebase project is in the same directory.

# The Firebase App ID for your game.
# This should match the ID used by your main game bot.
FIREBASE_APP_ID = "msgc-power-store" 

try:
    # We only try to import the token from the config file.
    from config_leaderboard import TELEGRAM_BOT_TOKEN
except ImportError:
    print("ERROR: 'config_leaderboard.py' not found or 'TELEGRAM_BOT_TOKEN' is missing.")
    print("Please create the file and add your bot token to it.")
    TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN" # Placeholder
    print("WARNING: Using a placeholder token. The bot will not run without a real token.")


# --- SETUP ---

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Firebase
try:
    if os.path.exists("firebase_credentials.json"):
        cred = credentials.Certificate("firebase_credentials.json")
        # Check if the app is already initialized to avoid errors
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        logger.info("Firebase initialized successfully.")
    else:
        logger.error("FATAL: firebase_credentials.json not found. Please download it from your Firebase project settings.")
        db = None
        exit()
except Exception as e:
    logger.error(f"FATAL: Failed to initialize Firebase: {e}")
    db = None
    exit()

# --- HELPER FUNCTIONS ---

def escape_markdown_v2(text: str) -> str:
    """Escapes characters for Telegram's MarkdownV2 parse mode."""
    if not text:
        return ""
    # A list of characters to escape
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
    # Check if the command is used in a private chat
    if update.message.chat.type == 'private':
        await update.message.reply_text("This command can only be used in a group chat.")
        return

    if not db:
        await update.message.reply_text("Database not available. Cannot fetch leaderboard.")
        return

    try:
        # Reference to the same user collection as the main bot
        collection_path = f'artifacts/{FIREBASE_APP_ID}/users'
        users_ref = db.collection(collection_path)
        # Corrected the attribute from .path to ._path
        logger.info(f"Attempting to query Firestore collection at path: {'/'.join(users_ref._path)}")

        all_user_docs = users_ref.stream()

        players = []
        docs_found = 0
        for doc in all_user_docs:
            docs_found += 1
            player_data = doc.to_dict()
            logger.info(f"Found player doc: {doc.id} with data: {player_data}")
            if player_data:
                players.append({
                    'name': player_data.get('first_name', 'Unknown Player'),
                    'coins': player_data.get('coins', 0)
                })
        
        logger.info(f"Finished streaming docs. Found {docs_found} documents in the collection.")
        logger.info(f"Populated {len(players)} players into the leaderboard list.")

        if not players:
            await update.message.reply_text("No players have registered in the tournament yet. The leaderboard is empty.")
            return

        # Sort players by coins in descending order
        sorted_players = sorted(players, key=lambda p: p['coins'], reverse=True)

        # Build the leaderboard message
        leaderboard_text = "🏆 *Mavericks Tournament 3\\.0 Leaderboard* 🏆\n\n"
        
        rank_emojis = {1: '🥇', 2: '🥈', 3: '🥉'}

        for i, player in enumerate(sorted_players):
            rank = i + 1
            # Use get() for emojis, providing a default format for ranks > 3
            rank_emoji = rank_emojis.get(rank, f" {rank}\\.")
            # Escape the player's name to prevent Markdown issues
            safe_name = escape_markdown_v2(player['name'])
            leaderboard_text += f"{rank_emoji} *{safe_name}*: {player['coins']} PC\n"
        
        await update.message.reply_text(leaderboard_text, parse_mode='MarkdownV2')
        logger.info(f"Leaderboard displayed successfully in chat: {update.message.chat.title}")

    except Exception as e:
        logger.error(f"Error in /leaderboard command: {e}", exc_info=True)
        await update.message.reply_text("An error occurred while fetching the leaderboard.")


def main() -> None:
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        logger.error("FATAL: TELEGRAM_BOT_TOKEN is not configured. Please set it in config_leaderboard.py.")
        return
        
    if not db:
        logger.error("FATAL: Firebase is not initialized. The bot cannot start.")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("leaderboard", leaderboard_command))

    # Run the bot until the user presses Ctrl-C
    logger.info("Leaderboard Bot is starting...")
    application.run_polling()
    logger.info("Leaderboard Bot has stopped.")

if __name__ == "__main__":
    main()