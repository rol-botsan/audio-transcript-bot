# audio-transcript-bot

Bot Telegram indépendant : reçoit un fichier audio (`.mp3`/`.m4a`/`.amr`), le convertit
en MP4 (image noire statique), l'upload sur Google Drive, déclenche la génération
automatique des sous-titres via Playwright (fonctionnalité UI-only de Drive), et
notifie sur Telegram avec le lien vers le fichier une fois les sous-titres prêts.

Projet séparé de `Gmail-Agent` — token Telegram, credentials Google et service
systemd propres, tout en tournant sur le même VPS.

## Mise en place

### 1. Bot Telegram
Créer un nouveau bot via [@BotFather](https://t.me/BotFather) → récupérer le token.
Récupérer ton `chat_id` (ex: en parlant à [@userinfobot](https://t.me/userinfobot)).

### 2. Google Cloud / Drive
1. Créer (ou réutiliser) un projet sur [Google Cloud Console](https://console.cloud.google.com/).
2. Activer l'API **Google Drive**.
3. Créer des identifiants OAuth "Application de bureau" → télécharger en `credentials.json`.
4. Créer le dossier Drive cible et récupérer son ID (dans l'URL).

### 3. Installation sur le VPS
```bash
sudo apt install ffmpeg
git clone <ce-repo> ~/audio-transcript-bot && cd ~/audio-transcript-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install --with-deps chromium
cp .env.example .env   # puis remplir les valeurs
bash assets/generate_black_image.sh
```

### 4. Autorisation Google Drive (upload)
`flow.run_local_server()` a besoin d'un navigateur : à lancer **une première fois
sur une machine avec écran** (pas directement sur le VPS), avec `credentials.json`
et les mêmes valeurs de `.env` :
```bash
python -c "from drive_client import get_drive_service; get_drive_service()"
```
Ça ouvre un navigateur, tu te connectes, ça génère `token.json`. Copier ensuite
`token.json` sur le VPS (`scp token.json vps:~/audio-transcript-bot/`).

### 5. Session Google pour Playwright (sous-titres)
À exécuter une fois, interactivement (pas en headless) :
```bash
PLAYWRIGHT_HEADLESS=false python captions_playwright.py
```
Une fenêtre Chromium s'ouvre : connecte-toi à ton compte Google, puis appuie sur
Entrée dans le terminal. La session est sauvegardée dans `chrome-profile/` et
réutilisée pour tous les runs suivants (pas de re-login).

> ⚠️ Les sélecteurs Playwright dans `captions_playwright.py` (menu "Plus
> d'options" → "Gérer les pistes de sous-titres" → "Générer automatiquement")
> sont une première approximation basée sur les libellés actuels de l'UI Drive.
> Google ne fournit aucune API stable pour cette fonctionnalité — à valider/
> ajuster en observant le déroulement avec `PLAYWRIGHT_HEADLESS=false` la
> première fois.

### 6. Déploiement en service systemd
```bash
sudo cp deploy/audio-transcript-bot.service /etc/systemd/system/
sudo sed -i "s#/home/USER#$HOME#g" /etc/systemd/system/audio-transcript-bot.service
sudo systemctl daemon-reload
sudo systemctl enable --now audio-transcript-bot
```

## Utilisation

Envoyer un fichier audio au bot :
- **Avec un texte accompagnant le fichier** → ce texte devient le nom du fichier sur Drive.
- **Sans texte** → le nom original du fichier est conservé.

Le bot répond immédiatement "Traitement en cours...", puis envoie un second
message avec le lien Drive une fois les sous-titres générés (peut prendre
plusieurs minutes selon la durée de l'audio).

## Debug

En cas d'échec de la génération des sous-titres, une capture d'écran est
sauvegardée dans `tmp/playwright_error_<file_id>.png` et l'erreur est loggée.
