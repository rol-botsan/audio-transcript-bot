import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = int(os.environ["TELEGRAM_CHAT_ID"])

DRIVE_FOLDER_ID = os.environ["DRIVE_FOLDER_ID"]
GOOGLE_CREDENTIALS_PATH = os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json")
GOOGLE_TOKEN_PATH = os.environ.get("GOOGLE_TOKEN_PATH", "token.json")
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.file"]

PLAYWRIGHT_USER_DATA_DIR = os.environ.get("PLAYWRIGHT_USER_DATA_DIR", "./chrome-profile")
PLAYWRIGHT_HEADLESS = os.environ.get("PLAYWRIGHT_HEADLESS", "true").lower() == "true"

WORK_DIR = os.environ.get("WORK_DIR", "./tmp")
BLACK_IMAGE_PATH = os.environ.get("BLACK_IMAGE_PATH", "./assets/black.png")

CAPTION_GENERATION_TIMEOUT_S = int(os.environ.get("CAPTION_GENERATION_TIMEOUT_S", "900"))
