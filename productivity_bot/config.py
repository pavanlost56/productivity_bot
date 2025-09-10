from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

# Core configuration
TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")

# Google OAuth client JSON (downloaded from Google Cloud Console)
GOOGLE_CLIENT_SECRETS_FILE: str = os.getenv(
    "GOOGLE_CLIENT_SECRETS_FILE", "client_secret.json"
)

# Where we store the OAuth token after the first login
GOOGLE_TOKEN_FILE: str = os.getenv("GOOGLE_TOKEN_FILE", "token.json")

# Your preferred timezone
DEFAULT_TIMEZONE: str = os.getenv("DEFAULT_TIMEZONE", "Asia/Kolkata")

# config.py
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
