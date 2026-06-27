import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token (from @BotFather)
BOT_TOKEN = os.getenv('BOT_TOKEN', '')

# Admin/Owner IDs (comma separated)
ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip()]

# Owner ID (for notifications)
OWNER_ID = int(os.getenv('OWNER_ID', 0))

# Settings
SPAM_THRESHOLD = int(os.getenv('SPAM_THRESHOLD', '3'))  # 3 reports = auto-ban
FLOOD_LIMIT = int(os.getenv('FLOOD_LIMIT', '5'))  # 5 messages in 5 seconds = flood
FLOOD_WINDOW = int(os.getenv('FLOOD_WINDOW', '5'))  # 5 seconds window
BAN_DURATION = int(os.getenv('BAN_DURATION', '24'))  # 24 hours auto-unban

# AI Detection
AI_CONFIDENCE_THRESHOLD = float(os.getenv('AI_CONFIDENCE_THRESHOLD', '0.7'))

# Spam keywords (for manual detection)
SPAM_KEYWORDS = [
    'https://', 'http://', 't.me/', 'telegram.me/',
    'buy', 'sell', 'free', 'offer', 'discount', 'giveaway',
    'click here', 'subscribe', 'follow', 'like', 'share'
]

# Credits
DEV_NAME = "@rehuux"
OWNER_NAME = "Syed Rehan"
BOT_NAME = "Spam Shield Bot"
