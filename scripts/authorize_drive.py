"""
Script à lancer une seule fois sur le VPS pour autoriser l'accès à Google Drive.

Le VPS n'a pas de navigateur, donc ce script démarre un petit serveur local sur
un port fixe (8080) et affiche l'URL d'autorisation à copier dans ton propre
navigateur (sur ton PC). Pour que la redirection Google fonctionne, connecte-toi
en SSH avec un tunnel sur ce port :

    ssh -L 8080:localhost:8080 root@<IP_VPS>

puis lance ce script dans cette session SSH :

    python scripts/authorize_drive.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google_auth_oauthlib.flow import InstalledAppFlow

import config

flow = InstalledAppFlow.from_client_secrets_file(
    config.GOOGLE_CREDENTIALS_PATH, config.DRIVE_SCOPES
)
creds = flow.run_local_server(port=8080, open_browser=False, timeout_seconds=600)

Path(config.GOOGLE_TOKEN_PATH).write_text(creds.to_json())
print(f"OK - token sauvegardé dans {config.GOOGLE_TOKEN_PATH}")
