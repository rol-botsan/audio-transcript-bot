# État du projet

## Pivot de direction (2026-07-12)

L'approche initiale (upload Google Drive + génération automatique des sous-titres
via Playwright) est **abandonnée** : Google bloque systématiquement toute connexion
pilotée par un navigateur automatisé (CDP), quel que soit le navigateur utilisé
(Chromium embarqué ou vrai Chrome, headless ou headed). Voir l'historique de
conversation pour le détail des tentatives.

## Nouveau workflow (en cours de construction)

1. Envoi d'un audio au bot Telegram, avec le **nom de la personne** dans le message.
2. Transcription **locale et gratuite** via `faster-whisper` (même approche que
   `voice.py` dans Gmail-Agent — pas d'API payante).
3. Le texte transcrit + le nom sont envoyés à **Claude** (API Anthropic) qui :
   - cherche le contact correspondant dans la base CRM Notion existante
   - crée un nouveau contact si aucune correspondance
   - logue l'appel (transcription + date) associé à ce contact
4. Notification Telegram de confirmation.

Objectif à terme : pouvoir retracer tous les appels échangés avec une personne donnée.

## Nettoyage effectué

Supprimés (code mort de l'ancienne approche Drive/Playwright) :
- `captions_playwright.py`, `drive_client.py`, `convert.py`, `scripts/authorize_drive.py`
- `assets/black.png`, `assets/generate_black_image.sh`, `deploy/audio-transcript-bot.service`
- Variables `.env`/`config.py` liées à Drive/Playwright (`DRIVE_FOLDER_ID`,
  `GOOGLE_CREDENTIALS_PATH`, `GOOGLE_TOKEN_PATH`, `PLAYWRIGHT_*`, `BLACK_IMAGE_PATH`,
  `CAPTION_GENERATION_TIMEOUT_S`)
- `requirements.txt` nettoyé (retrait `google-api-python-client`, `google-auth-*`,
  `playwright` ; ajout `faster-whisper`, `anthropic`, `notion-client`)

**Reste à faire sur le VPS** (pas encore nettoyé côté serveur) :
- Supprimer `credentials.json`, `token.json`, `chrome-profile/` (secrets/session
  Google Drive obsolètes)

**Conservé volontairement sur le VPS** (infrastructure générique réutilisable pour
de futurs projets) : `xfce4`, `tigervnc-standalone-server`, `google-chrome-stable`,
Playwright (Chromium).

## Point d'architecture à trancher

Le bot tournera comme **script Python autonome** sur le VPS (pas dans une session
Claude Code) — il devra donc appeler l'API Notion directement (librairie
`notion-client`), pas via le protocole MCP (MCP est spécifique aux clients comme
Claude Code/Desktop, pas embarquable dans un script headless déployé).

## Repo

https://github.com/rol-botsan/audio-transcript-bot (privé)

## Prochaine étape

Écrire le nouveau pipeline dans `bot.py` : transcription faster-whisper → appel
Claude (function calling / tool use pour chercher-créer le contact Notion et logger
l'appel) → notification Telegram.
