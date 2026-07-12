from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import config


def get_drive_service():
    creds = None
    token_path = Path(config.GOOGLE_TOKEN_PATH)
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), config.DRIVE_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Nécessite un navigateur : à exécuter une première fois sur une
            # machine avec écran (pas directement sur le VPS), puis copier le
            # token.json généré vers le VPS. Voir README.md.
            flow = InstalledAppFlow.from_client_secrets_file(
                config.GOOGLE_CREDENTIALS_PATH, config.DRIVE_SCOPES
            )
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())
    return build("drive", "v3", credentials=creds)


def upload_video(service, file_path: Path, filename: str) -> tuple[str, str]:
    metadata = {"name": filename, "parents": [config.DRIVE_FOLDER_ID]}
    media = MediaFileUpload(str(file_path), mimetype="video/mp4", resumable=True)
    file = service.files().create(body=metadata, media_body=media, fields="id, webViewLink").execute()
    return file["id"], file.get("webViewLink")
