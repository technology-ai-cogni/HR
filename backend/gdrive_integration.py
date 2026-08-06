import os
import io
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive'
]

def get_gdrive_service():
    """Authenticates using Service Account JSON key or OAuth2 credentials."""
    creds = None
    
    # 1. Search for Service Account JSON key file in backend/ directory or env
    json_env = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    backend_dir = os.path.dirname(__file__)

    if json_env:
        try:
            if os.path.exists(json_env):
                creds = service_account.Credentials.from_service_account_file(json_env, scopes=SCOPES)
            else:
                info = json.loads(json_env)
                creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
            print("[INFO] Authenticated using GOOGLE_SERVICE_ACCOUNT_JSON env variable")
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            print(f"[WARNING] Failed to load GOOGLE_SERVICE_ACCOUNT_JSON: {e}")

    # Search for any *.json file with type=service_account in backend/
    possible_files = ["service_account.json", "credentials.json"] + [f for f in os.listdir(backend_dir) if f.endswith(".json")]
    for p in possible_files:
        full_p = os.path.join(backend_dir, p)
        if os.path.exists(full_p):
            try:
                with open(full_p, 'r') as fp:
                    data = json.load(fp)
                    if isinstance(data, dict) and data.get("type") == "service_account":
                        creds = service_account.Credentials.from_service_account_file(full_p, scopes=SCOPES)
                        print(f"[INFO] Authenticated using Service Account file: {p}")
                        return build('drive', 'v3', credentials=creds)
            except Exception:
                pass

    # 2. Fall back to OAuth2 User Flow (credentials.json + token.json)
    token_path = os.path.join(backend_dir, 'token.json')
    creds_path = os.path.join(backend_dir, 'credentials.json')

    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            print(f"[WARNING] Failed to load token.json: {e}")
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"[WARNING] Failed to refresh token: {e}")
                creds = None
        
        if not creds:
            if not os.path.exists(creds_path):
                raise FileNotFoundError(
                    "Google Drive API Service Account JSON key not found in backend directory.\n"
                    "Please place your Service Account .json key file in the backend directory."
                )
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
            
    print("[INFO] Authenticated using OAuth2 user credentials (token.json)")
    return build('drive', 'v3', credentials=creds)


def list_files_in_folder(folder_id: str):
    """Lists subfolders, PDF, and DOCX files in a Google Drive folder using pagination (no 100 limit cap)."""
    try:
        service = get_gdrive_service()
        query = (
            f"'{folder_id}' in parents and trashed = false and ("
            "mimeType = 'application/vnd.google-apps.folder' or "
            "mimeType = 'application/pdf' or "
            "mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' or "
            "mimeType = 'application/msword'"
            ")"
        )

        all_files = []
        page_token = None

        while True:
            results = service.files().list(
                q=query,
                pageSize=1000,
                pageToken=page_token,
                fields="nextPageToken, files(id, name, mimeType, size, webViewLink)",
                orderBy="folder,name"
            ).execute()

            items = results.get('files', [])
            for f in items:
                is_folder = (f.get("mimeType") == "application/vnd.google-apps.folder")
                all_files.append({
                    "id": f.get("id"),
                    "name": f.get("name"),
                    "mimeType": f.get("mimeType"),
                    "size": f.get("size", "0"),
                    "web_view_link": f.get("webViewLink") or f"https://drive.google.com/file/d/{f.get('id')}/view",
                    "is_folder": is_folder
                })

            page_token = results.get('nextPageToken')
            if not page_token:
                break

        return all_files
    except Exception as e:
        raise Exception(f"Google Drive Error: {str(e)}")


def download_file_bytes(file_id: str, file_name: str):
    """Downloads a file's content from Google Drive and returns a file-like object with web_view_link."""
    try:
        service = get_gdrive_service()
        request = service.files().get_media(fileId=file_id)
        
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            
        file_buffer.seek(0)
        file_buffer.name = file_name
        file_buffer.web_view_link = f"https://drive.google.com/file/d/{file_id}/view"
        return file_buffer
    except Exception as e:
        raise Exception(f"Failed to download file {file_name} from Google Drive: {str(e)}")
