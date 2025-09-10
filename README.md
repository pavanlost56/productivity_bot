# Productivity Bot – Step 1 (Google Calendar + Telegram)

This is the **Step 1 MVP** for your Python automation project. It sets up:
- A Telegram bot (`/start`, `/today`)
- Google Calendar integration (OAuth) to list today's events in your timezone

We’ll add Excel reports, charts, voice, and AI (Gemini + OpenAI) in the next steps.

---

## Prerequisites
- Python 3.10+
- A Telegram Bot token (from @BotFather)
- A Google Cloud project with **Calendar API** enabled and an **OAuth Client ID** (Desktop)
  - Download the OAuth client JSON as `client_secret.json` and place it in the project root.

## Setup
```bash
# 1) Create and activate a virtual env
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Configure environment variables
cp .env.sample .env
# Edit .env and set TELEGRAM_BOT_TOKEN, (optionally) paths/timezone

# 4) Put your Google OAuth credentials
# Place client_secret.json in this folder (same level as main.py)

# 5) Run the bot
python -m productivity_bot.main
```

On first run, a browser window will open to complete Google authentication. This creates `token.json` for future runs.

---

## Commands (current)
- `/start` – quick hello + help
- `/today` – lists today's Calendar events in your timezone (default Asia/Kolkata)

---

## Environment (.env)
```
TELEGRAM_BOT_TOKEN=123456:ABC-YourTokenHere
GOOGLE_CLIENT_SECRETS_FILE=client_secret.json
GOOGLE_TOKEN_FILE=token.json
DEFAULT_TIMEZONE=Asia/Kolkata
```

---

## Project Structure
```
productivity_bot/
├── __init__.py
├── main.py
├── config.py
├── google_calendar.py
├── telegram_bot.py
├── excel_report.py          # placeholder for Step 2
├── ai_assistant.py          # placeholder for Step 3
├── utils.py
├── data/                    # generated files (reports/logs)
└── __pycache__/             # ignored
```

---

## Next Steps
- Step 2: Excel export + daily/weekly charts
- Step 3: Progress updates, /addtask, /done
- Step 4: AI insights (Gemini + OpenAI)
- Step 5: Voice input (Telegram voice + Whisper)
