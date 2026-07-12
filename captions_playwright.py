import asyncio
import logging
from pathlib import Path

from playwright.async_api import async_playwright

import config

logger = logging.getLogger(__name__)

DRIVE_VIDEO_URL = "https://drive.google.com/file/d/{file_id}/view"


async def _get_context(playwright, headless: bool):
    user_data_dir = Path(config.PLAYWRIGHT_USER_DATA_DIR)
    user_data_dir.mkdir(parents=True, exist_ok=True)
    return await playwright.chromium.launch_persistent_context(
        str(user_data_dir),
        headless=headless,
        channel="chrome",
    )


async def login_once() -> None:
    """Exécuter une seule fois, interactivement (pas sur le VPS en headless),
    pour se connecter au compte Google utilisé pour la génération des
    sous-titres. La session est sauvegardée dans PLAYWRIGHT_USER_DATA_DIR et
    réutilisée ensuite par generate_captions_and_get_link()."""
    async with async_playwright() as p:
        context = await _get_context(p, headless=False)
        page = await context.new_page()
        await page.goto("https://accounts.google.com/")
        print("Connecte-toi à ton compte Google dans la fenêtre ouverte, puis appuie sur Entrée ici.")
        input()
        await context.close()


async def generate_captions_and_get_link(file_id: str, timeout_s: int = 900) -> str:
    """Pilote l'UI Drive pour générer automatiquement les sous-titres d'une
    vidéo, puis retourne le lien vers le fichier.

    ATTENTION : "Générer automatiquement" est une fonctionnalité de l'UI web
    Drive, absente de l'API Drive officielle. Les sélecteurs ci-dessous sont
    une première approximation basée sur les libellés actuels du menu et
    devront très probablement être ajustés en conditions réelles (lancer une
    fois avec PLAYWRIGHT_HEADLESS=false pour observer et corriger).
    """
    async with async_playwright() as p:
        context = await _get_context(p, headless=config.PLAYWRIGHT_HEADLESS)
        page = await context.new_page()
        try:
            await page.goto(DRIVE_VIDEO_URL.format(file_id=file_id), wait_until="networkidle")

            await page.get_by_role("button", name="Plus d'options").click()
            await page.get_by_text("Gérer les pistes de sous-titres").click()
            await page.get_by_text("Générer automatiquement").click()

            await page.wait_for_selector("text=Sous-titres générés", timeout=timeout_s * 1000)

            return DRIVE_VIDEO_URL.format(file_id=file_id)
        except Exception:
            work_dir = Path(config.WORK_DIR)
            work_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = work_dir / f"playwright_error_{file_id}.png"
            await page.screenshot(path=str(screenshot_path))
            logger.error("Échec génération sous-titres, capture d'écran: %s", screenshot_path)
            raise
        finally:
            await context.close()


if __name__ == "__main__":
    asyncio.run(login_once())
