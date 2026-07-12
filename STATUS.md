# État du projet

## Architecture actuelle (implémentée, pas encore testée end-to-end)

1. Audio envoyé au bot Telegram avec le nom de la personne en légende.
2. Transcription locale et gratuite via `faster-whisper` (`transcribe.py`).
3. Résumé structuré (résumé / points clés / prochaines étapes) via l'API Claude,
   sortie forcée en JSON via tool use (`claude_agent.py`).
4. Recherche/création du contact dans le CRM Notion existant, puis création
   d'une sous-page d'appel avec le résumé structuré (`notion_helper.py`).
5. Notification Telegram avec le lien vers la page Notion créée.

Format de page d'appel validé avec l'utilisateur, exemples réels créés en
sous-pages du contact "Cristian Sandu" dans Notion (à garder ou supprimer,
marqués `[TEST]`).

## Historique (pivot)

L'approche initiale (Google Drive + sous-titres auto via Playwright) a été
abandonnée : Google bloque toute connexion pilotée par un navigateur automatisé
(CDP), quel que soit le navigateur (Chromium ou vrai Chrome, headless ou headed).
Voir l'historique de conversation pour le détail. Infrastructure VNC/Chrome/
Playwright volontairement conservée sur le VPS pour d'éventurs futurs projets,
mais plus utilisée par ce bot.

## Fichiers

- `bot.py` — handlers Telegram + orchestration du pipeline
- `transcribe.py` — transcription locale faster-whisper
- `claude_agent.py` — résumé structuré via Claude (tool use)
- `notion_helper.py` — recherche/création contact + création page d'appel
- `config.py` — configuration via `.env`
- `deploy/audio-transcript-bot.service` — unité systemd (pas encore installée sur le VPS)

## Repo

https://github.com/rol-botsan/audio-transcript-bot (privé)

## Prochaine étape

1. Configurer `.env` avec les nouvelles clés (`ANTHROPIC_API_KEY`, `NOTION_API_KEY`,
   `NOTION_CRM_DATABASE_ID`) sur le VPS.
2. `git pull` + `pip install -r requirements.txt` sur le VPS.
3. Nettoyer les fichiers Google Drive obsolètes sur le VPS (`credentials.json`,
   `token.json`, `chrome-profile/`) s'ils sont encore présents.
4. Tester en envoyant un audio réel au bot.
5. Déployer le service systemd une fois le test validé.
