# 🛡️ Telegram SpamXshield Bot

**AI-powered auto-moderation bot for Telegram groups and channels.**  
Detects spam, prevents flooding, auto-bans offenders, manages welcomes, and gives admins full control, all deployed on Render

---

## Features

| Feature | Description |
|---------|-------------|
| **AI Spam Detection** | Detects spam based on patterns, keywords, URLs, caps, and repetition |
| **Flood Protection** | Limits messages per user (default: 5 messages in 5 seconds) |
| **Auto-Ban** | Auto-bans users after configurable warning threshold (default: 3 warnings) |
| **User Reputation** | Tracks user behavior with reputation scores |
| **Welcome Messages** | Customizable welcome messages for new members |
| **Admin Commands** | `/ban`, `/unban`, `/warn`, `/reports`, `/setwelcome`, `/resolve` |
| **Channel Management** | `/autodelete on/off`, `/floodlimit` |
| **Spam Reports** | Track and resolve spam reports |
| **Admin Alerts** | Real-time notifications for spam activity |
| **Health Check** | Flask endpoint for Render monitoring |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Telegram API credentials from [my.telegram.org](https://my.telegram.org)
- Telegram Bot Token from [@BotFather](https://t.me/botfather)

### Installation

```bash
# Clone the repository
git clone https://github.com/rehuux/spamXshield.git
cd spamXshield

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Run Locally

```bash
python bot.py
```

Deploy on Render

1. Push code to GitHub
2. Go to render.com
3. Create new Web Service
4. Connect your GitHub repo
5. Set environment variables
6. Click Deploy 🚀

---

📋 Commands

User Commands

Command Description
/start Show welcome message
/help Show help menu
/rules Show group rules
/status Show group statistics

Admin Commands

Command Description
/ban @username Ban a user
/unban @username Unban a user
/warn @username Warn a user
/reports View pending spam reports
/resolve <id> Resolve a spam report
/setwelcome <message> Set welcome message
/autodelete on/off Toggle auto-delete
/floodlimit <number> Set flood limit

---

⚙️ Configuration

Environment Variables

Variable Description Default
API_ID Telegram API ID Required
API_HASH Telegram API Hash Required
SESSION_STRING Telegram session string Required
OWNER_ID Your Telegram User ID Required
ADMIN_IDS Admin user IDs (comma separated) Required
SPAM_THRESHOLD Warnings before auto-ban 3
FLOOD_LIMIT Messages allowed in window 5
FLOOD_WINDOW Time window in seconds 5
BAN_DURATION Ban duration in hours 24
SPAM_CONFIDENCE_THRESHOLD Spam score threshold 0.7
PORT Render port 10000

Getting Your Telegram User ID

1. Open Telegram
2. Search for @userinfobot
3. Send /start
4. Copy your numeric User ID

---

🛠️ Technology Stack

Component Technology
Language Python 3.11+
Telegram API Telethon
Database SQLite
Web Server Flask (health check)
Hosting Render (free tier)

---

📁 Project Structure

```
telegram-spam-shield/
├── bot.py              # Main Telegram bot
├── database.py         # SQLite operations
├── spam_detector.py    # AI spam detection logic
├── config.py           # Configuration loader
├── main.py             # Flask health check
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container configuration
├── render.yaml         # Render auto-deploy config
├── .env.example        # Environment template
├── .gitignore          # Git ignore file
└── README.md           # This file
```

---

🔒 Security & Privacy

· All data is stored locally in SQLite
· No external API calls for spam detection
· User data is never shared or sold
· Session string is stored securely in environment variables

---

🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (git checkout -b feature/amazing-feature)
3. Commit your changes (git commit -m 'Add some amazing feature')
4. Push to the branch (git push origin feature/amazing-feature)
5. Open a Pull Request

---

⚠️ Disclaimer

This bot is for educational purposes only. Use responsibly and respect Telegram's Terms of Service. The developers are not responsible for any misuse or account bans resulting from improper use.

---

📄 License

This project is for educational purposes only. All rights reserved.

---

👨‍💻 Credits

· Developer: @rehuux
· Owner: Syed Rehan
· Built with Python + Telethon + SQLite

---

🌟 Support

If you find this project useful, please give it a ⭐ on GitHub!

---

⚡ Powered by @rehuux
