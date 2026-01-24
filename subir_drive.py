import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# =========================
# CONFIG
# =========================
ARCHIVO = "historial_portafolio.csv"
SHARED_DRIVE_ID = "1cje4dOVOZI9m1PWCbebjjbqyuI8CENIt"

# =========================
# CREDENCIALES
# =========================
creds_json = json.loads(os.environ["GOOGLE_DRIVE_KEY"])

credentials = service_account.Credentials.from_service_account_info(
    creds_json,
    scopes=["https://www.googleapis.com/auth/drive"]
)

service = build("drive", "v3", credentials=credentials)

# =========================
# SUBIR CSV
# =========================
file_metadata = {
    "name": ARCHIVO,
    "parents": [SHARED_DRIVE_ID]
}

media = MediaFileUpload(ARCHIVO, mimetype="text/csv", resumable=True)

service.files().create(
    body=file_metadata,
    media_body=media,
    supportsAllDrives=True
).execute()

print("☁️ CSV subido correctamente a Google Drive")
