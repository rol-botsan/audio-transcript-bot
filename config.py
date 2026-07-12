import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = int(os.environ["TELEGRAM_CHAT_ID"])

WORK_DIR = os.environ.get("WORK_DIR", "./tmp")

WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "small")

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")

NOTION_API_KEY = os.environ["NOTION_API_KEY"]
NOTION_CRM_DATABASE_ID = os.environ["NOTION_CRM_DATABASE_ID"]
