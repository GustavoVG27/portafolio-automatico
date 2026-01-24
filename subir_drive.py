import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

creds_info = json.loads(os.environ["GOOGLE_DRIVE_KEY"])
creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)

service = build("drive", "v3", credentials=creds)

file_metadata = {
    "name": "historial_portafolio.csv"
}

media = MediaFileUpload(
    "historial_portafolio.csv",
    mimetype="text/csv",
    resumable=True
)

service.files().create(
    body=file_metadata,
    media_body=media,
    fields="id"
).execute()

print("☁️ CSV subido a Google Drive")
