import asyncio
import logging
import re
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import config
from captions_playwright import generate_captions_and_get_link
from convert import audio_to_mp4
from drive_client import get_drive_service, upload_video

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

WORK_DIR = Path(config.WORK_DIR)
WORK_DIR.mkdir(parents=True, exist_ok=True)


def _is_authorized(update: Update) -> bool:
    return bool(update.effective_chat) and update.effective_chat.id == config.TELEGRAM_CHAT_ID


def _sanitize_filename(name: str) -> str:
    name = name.strip()
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    return name[:150] or "audio"


async def _send_with_retry(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, retries: int = 3) -> None:
    for attempt in range(retries):
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
            return
        except Exception:
            logger.exception("Échec d'envoi Telegram (tentative %s)", attempt + 1)
            await asyncio.sleep(2 * (attempt + 1))
    logger.error("Abandon de l'envoi Telegram après %s tentatives", retries)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    await update.message.reply_text(
        "Envoie-moi un fichier audio (.mp3/.m4a/.amr). "
        "Ajoute un texte au message pour renommer le fichier, sinon le nom original est conservé."
    )


async def handle_audio_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return

    message = update.message
    audio_obj = message.audio or message.document
    if audio_obj is None:
        return

    original_name = getattr(audio_obj, "file_name", None) or f"audio_{audio_obj.file_unique_id}"
    caption_text = (message.caption or "").strip()
    base_name = _sanitize_filename(caption_text) if caption_text else Path(original_name).stem
    ext = Path(original_name).suffix or ".mp3"

    await message.reply_text(f"Reçu : {original_name}. Traitement en cours...")

    tg_file = await audio_obj.get_file()
    audio_path = WORK_DIR / f"{base_name}{ext}"
    await tg_file.download_to_drive(custom_path=str(audio_path))

    asyncio.create_task(_process_audio(context, message.chat_id, audio_path, base_name))


async def _process_audio(context: ContextTypes.DEFAULT_TYPE, chat_id: int, audio_path: Path, base_name: str) -> None:
    mp4_path = WORK_DIR / f"{base_name}.mp4"
    try:
        await asyncio.to_thread(audio_to_mp4, audio_path, Path(config.BLACK_IMAGE_PATH), mp4_path)

        service = await asyncio.to_thread(get_drive_service)
        file_id, _ = await asyncio.to_thread(upload_video, service, mp4_path, f"{base_name}.mp4")

        transcript_link = await generate_captions_and_get_link(file_id, timeout_s=config.CAPTION_GENERATION_TIMEOUT_S)

        await _send_with_retry(
            context, chat_id, f"✅ Transcription prête pour \"{base_name}\" :\n{transcript_link}"
        )
    except Exception:
        logger.exception("Échec du traitement de %s", audio_path)
        await _send_with_retry(context, chat_id, f"❌ Échec du traitement de \"{base_name}\". Voir les logs.")
    finally:
        audio_path.unlink(missing_ok=True)
        mp4_path.unlink(missing_ok=True)


def main() -> None:
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.AUDIO | filters.Document.AUDIO, handle_audio_file))
    logger.info("Bot démarré (long polling)")
    app.run_polling()


if __name__ == "__main__":
    main()
