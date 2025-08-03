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
TELEGRAM_BOT_TOKEN = "8432697262:AAERRuVpN5l8jBCc38dq3H6nG6Z7tw_H4rc"
FIREBASE_APP_ID = "msgc-power-store" 
# Get Firebase credentials from environment variable
FIREBASE_CREDENTIALS_JSON = {
  "type": "service_account",
  "project_id": "power-store-bot",
  "private_key_id": "751cd8ae666181e35b892de0df090ea7705a8936",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCMeBUBAnjv/GYR\nriKlWvZbaoSpJgb2/hl5PypwAdIfQ9t9IEc4+1erze/9+Zq5+G73EecwCMuLzjbP\njD84BM81Bq2FeV5R0+FY0PXR1fHFan+xsBKx2PpAcnkqbkYeroEPkXCk0ACfvoO2\n8IFLDq17kB2VzcNGWzRMTQne2Dn4VOgy+eD/vejUuiNQS5Rc32HxV9bo84PBHDo6\nH5uyGoDK3MwcVsFSlv2FTSR3WC/c2gwBA5X9HyQl/u/LW53sGrH4pD3T1bGVBP57\n8lsy66H1q5xDaeC5STQm6/rGtVRXjGxv3cN8v/DeMvB/zxBrPK7dywbw6q1C/pjO\nB2nUDbgVAgMBAAECggEABUj0U1omNjNLHNGuLIYAXF6k2J9dZjgXucPaYyXyY6pA\nLRREkbyFJynjpGzaeTJDbIjQJ7LBA8TRs5vdegxWRnK2nx26on4EDb0o7ojr5IdW\nABe1kFrvSXL1I5dMDJX4tZ79e7n2uAvpNT4Vwz7tYIeC0XLRLMm8LT29yBRfE/yB\njeNuSsTU2CzP9xDXCjcIneTSukCUmP40xfyBq28JZUF0EB8O/zUdaUPki5IuDOAN\n3x8iNNEuuFpD8qYe4Hmdd4IUflAptJ+NTbefy1cAIZKV9WqWw/6Ea/YIjtdDKhou\n7s5woVYV5elK28XkBb4xhHzD5JXu6UX3h6UReq4KuQKBgQC/HqJkCLiie0qigUlL\nUW/WS9Z+RkRYkGQ10kGOSPKyCuc3h7i/dxSE+hYvFAGfgr0N6l1OLKV761oAJh7j\nb/1Ebzqz6MlnSKpb5ZX0GEfxDfIS2LRNhArtjKrZATQF6mbD/g3nHFBOUi0mwx7Y\nVEZiKpBjog68Wo7GgP6c6ocpeQKBgQC8J6DYip4C/nHnCM5qQxpTJhHNbYVr98RE\nPIteHOcKSZ4TtAls2EDrsfyapqtmbZGwb+JitZ9rLYnIBSl3e8dC56bzE0n1che6\nrBE78ZKxcVGbe1Df2KFbZS4NdhmCZ0wERspxVUdafpwYRZqr1ndMPXcTMS8aY7Zq\nSQbrM9w4fQKBgAWsChO/8oLX9+IUxjEXDKOmgooi2bprJp42TD3FynYgPrZ2L7R2\n+0PrDCd/h4DNZ4D3OKeuSYcA+B3TA82qMDEMwAhA22FWVb/+c1HYOqJb0JhgmBFI\n3u4n45YnI/0c9MnSS2VVgMiiRbbFya+P6LrXGovqbleGtIANqgDMMRC5AoGAN5iq\nEXIcMJxIwdC7VXDQhYM5PW9APl/u0Y7mS3/U0RhhqkbHhi78N+jW0EexW8nCg9T7\nmtk56uyAyuajkxezEFTs4uRvNSRqWJFhYkoGY4Itb/jnM82KGDx0eCvOa9bkAlt8\nlDJzrAy/SPjANEhh5dg/qB8fYPfXvd4oOjWPu+0CgYB2pd2gynkEAdvB01/V4HQ0\ndK5+ss7w9A1vQP9GW7uccQah8gTGB36rT85KayklvJheZZFZmJcZkorvjArEmqJx\nAV6yXtK/orMeUpHDafh1QAYgADgmWTagErAKFCQLp5CFUYJdnXmPFrQr+Iv1aqVE\nLQaycLiFeyR7hQ5W8Z8Ryg==\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-fbsvc@power-store-bot.iam.gserviceaccount.com",
  "client_id": "103497132702889711956",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40power-store-bot.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}


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
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_JSON)
    
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

