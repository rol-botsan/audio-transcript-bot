# État du projet (pause en cours)

## Ce qui fonctionne déjà (déployé sur le VPS Hetzner)

- Bot Telegram indépendant (`audio-transcript-bot`), code dans son propre dossier/repo,
  séparé de `Gmail-Agent`.
- Cloné et installé sur le VPS (`~/audio-transcript-bot`), venv + dépendances + ffmpeg + Playwright.
- `.env` et `credentials.json` configurés et transférés sur le VPS (via `scp`, jamais via git).
- Autorisation Google Drive (OAuth `drive.file`) faite avec succès — `token.json` généré et
  fonctionnel sur le VPS (via `scripts/authorize_drive.py` + tunnel SSH).
- Upload de fichiers vers Drive : prêt à l'usage (`drive_client.py`).
- Bureau graphique XFCE + serveur VNC (TigerVNC) installés et fonctionnels sur le VPS,
  accessible depuis le PC via tunnel SSH (`ssh -L 5901:localhost:5901 ...`) + TigerVNC Viewer.

## Ce qui est bloqué

**Génération automatique des sous-titres via la fonction native de Google Drive
(`captions_playwright.py`) : bloquée définitivement.**

- Google refuse la connexion à tout navigateur piloté par Playwright avec le message
  *"Couldn't sign you in — This browser or app may not be secure"*.
- Testé sans succès :
  - Chromium embarqué par Playwright, headless et headed
  - Vrai Google Chrome (`channel="chrome"`) + `--no-sandbox`, sur un vrai bureau VNC
- Conclusion : Google détecte la session pilotée par CDP (Chrome DevTools Protocol)
  indépendamment du navigateur utilisé. Impossible à contourner sans techniques
  d'évasion de la détection anti-bot, qu'on a choisi de ne pas utiliser.

## Décision à prendre pour la suite (3 options, non tranchée)

1. **API Whisper (OpenAI)** — ~11 €/mois pour 1h d'audio/jour. Entièrement automatisé,
   fiable, pas de risque de blocage. Nécessite de réécrire l'étape de transcription
   dans `bot.py` (appel API au lieu de Playwright) et de supprimer `captions_playwright.py`.

2. **Continuer à chercher un contournement légitime** — poser la question à une
   communauté technique (message déjà rédigé) pour voir s'il existe une méthode
   supportée d'obtenir une session Google authentifiée sur un serveur pour ce cas d'usage.

3. **Semi-automatique avec Gemini (Google One)** — gratuit, inclus dans l'abonnement
   existant de l'utilisateur. Le bot ferait : réception Telegram → renommage → upload
   Drive (fichier audio brut, pas besoin de conversion MP4/image noire) → notification
   avec lien Drive. La transcription serait déclenchée manuellement par l'utilisateur
   via "Demander à Gemini" dans Drive (2-3 clics), pas d'automatisation de connexion Google.
   Impliquerait de simplifier le code : suppression de `convert.py`,
   `captions_playwright.py`, et de toute la partie VNC/Playwright du déploiement.

## Repo

Code source : https://github.com/rol-botsan/audio-transcript-bot (privé)

## Fichiers clés

- `bot.py` — handlers Telegram + orchestration
- `convert.py` — conversion audio → MP4 (utile seulement si option Drive-native reprise un jour)
- `drive_client.py` — upload Google Drive (fonctionnel)
- `captions_playwright.py` — génération sous-titres via Drive (bloqué, cf. ci-dessus)
- `config.py` — configuration via `.env`
- `scripts/authorize_drive.py` — script d'autorisation OAuth Drive (fonctionnel)
- `deploy/audio-transcript-bot.service` — unité systemd (pas encore installée/activée sur le VPS)

## Prochaine étape à la reprise

Choisir entre les options 1/2/3 ci-dessus, puis reprendre à partir de la tâche
"Deploy systemd service" (le service n'est pas encore configuré/démarré sur le VPS).
