# audio-transcript-bot

Bot Telegram indépendant : reçoit un fichier audio (`.mp3`/`.m4a`/`.amr`) accompagné
du nom d'une personne, le transcrit localement et gratuitement (`faster-whisper`),
génère un résumé structuré via Claude (résumé / points clés / prochaines étapes),
puis le logue comme sous-page du contact correspondant dans le CRM Notion existant
(création du contact si aucune correspondance trouvée). Notifie sur Telegram avec
le lien vers la page Notion créée.

Projet séparé de `Gmail-Agent` — token Telegram et service systemd propres, tout
en tournant sur le même VPS.

## Mise en place

### 1. Bot Telegram
Créer un nouveau bot via [@BotFather](https://t.me/BotFather) → récupérer le token.
Récupérer ton `chat_id` (ex: en parlant à [@userinfobot](https://t.me/userinfobot)).

### 2. Clé API Anthropic (Claude)
Récupérer une clé sur [console.anthropic.com](https://console.anthropic.com/settings/keys).

### 3. Intégration Notion
1. Créer une intégration interne sur [notion.so/my-integrations](https://www.notion.so/my-integrations) → récupérer la clé API.
2. Ouvrir la database CRM contacts dans Notion → menu "..." → "Connexions" → ajouter cette intégration (sinon l'API n'y a pas accès).
3. Récupérer l'ID de la database (dans son URL, la partie avant `?v=`).

### 4. Installation sur le VPS
```bash
sudo apt install ffmpeg python3-venv
git clone https://github.com/rol-botsan/audio-transcript-bot.git ~/audio-transcript-bot
cd ~/audio-transcript-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # puis remplir toutes les valeurs
```

`ffmpeg` reste utile ici : `faster-whisper` s'en sert pour décoder les formats
audio (`.amr`, `.m4a`, etc.) avant transcription.

### 5. Déploiement en service systemd
```bash
sudo cp deploy/audio-transcript-bot.service /etc/systemd/system/
sudo sed -i "s#/home/USER#$HOME#g" /etc/systemd/system/audio-transcript-bot.service
sudo systemctl daemon-reload
sudo systemctl enable --now audio-transcript-bot
```

## Utilisation

Envoyer un fichier audio au bot **avec le nom de la personne** dans le message
(texte accompagnant le fichier — obligatoire, sert à retrouver/créer le contact).

Le bot répond "Transcription en cours...", puis un second message avec le lien
Notion une fois l'appel logué (transcription locale + résumé Claude + écriture
Notion, généralement quelques secondes à ~1 minute selon la durée de l'audio).

## Debug

Les logs du service : `journalctl -u audio-transcript-bot -f`
