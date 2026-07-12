import asyncio
import logging
from datetime import datetime
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import config
from claude_agent import summarize_call
from notion_helper import create_call_page, get_or_create_contact_page_id
from transcribe import transcribe_audio

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

WORK_DIR = Path(config.WORK_DIR)
WORK_DIR.mkdir(parents=True, exist_ok=True)


def _is_authorized(update: Update) -> bool:
    return bool(update.effective_chat) and update.effective_chat.id == config.TELEGRAM_CHAT_ID


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
        "Envoie-moi un fichier audio (.mp3/.m4a/.amr) en ajoutant le nom de la "
        "personne dans le message (texte accompagnant le fichier). "
        "Je transcris l'appel et je le logue dans son dossier Notion."
    )


async def handle_audio_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return

    message = update.message
    audio_obj = message.audio or message.document
    if audio_obj is None:
        return

    contact_name = (message.caption or "").strip()
    if not contact_name:
        await message.reply_text(
            "Merci d'ajouter le nom de la personne dans le message accompagnant l'audio."
        )
        return

    original_name = getattr(audio_obj, "file_name", None) or f"audio_{audio_obj.file_unique_id}"
    ext = Path(original_name).suffix or ".mp3"
    call_time = datetime.now()

    await message.reply_text(f"Reçu, appel avec {contact_name}. Transcription en cours...")

    tg_file = await audio_obj.get_file()
    audio_path = WORK_DIR / f"{audio_obj.file_unique_id}{ext}"
    await tg_file.download_to_drive(custom_path=str(audio_path))

    asyncio.create_task(_process_audio(context, message.chat_id, audio_path, contact_name, call_time))


async def _process_audio(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    audio_path: Path,
    contact_name: str,
    call_time: datetime,
) -> None:
    try:
        transcript = await asyncio.to_thread(transcribe_audio, audio_path)
        summary = await asyncio.to_thread(summarize_call, transcript, contact_name)

        contact_page_id = await asyncio.to_thread(get_or_create_contact_page_id, contact_name)

        title = f"Appel — {call_time.strftime('%d/%m/%Y %H:%M')}"
        call_page_id = await asyncio.to_thread(
            create_call_page,
            contact_page_id,
            title,
            summary.summary,
            summary.key_points,
            summary.next_steps,
        )

        notion_url = f"https://notion.so/{call_page_id.replace('-', '')}"
        await _send_with_retry(
            context, chat_id, f"✅ Appel avec {contact_name} logué dans Notion :\n{notion_url}"
        )
    except Exception:
        logger.exception("Échec du traitement de %s", audio_path)
        await _send_with_retry(
            context, chat_id, f"❌ Échec du traitement de l'appel avec {contact_name}. Voir les logs."
        )
    finally:
        audio_path.unlink(missing_ok=True)


def main() -> None:
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.AUDIO | filters.Document.AUDIO, handle_audio_file))
    logger.info("Bot démarré (long polling)")
    app.run_polling()


if __name__ == "__main__":
    main()
