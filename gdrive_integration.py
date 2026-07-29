import os
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_gdrive_service():
    """Authenticates using service_account.json or credentials.json, and returns the Drive service."""
    creds = None
    
    # 1. Check Service Account credentials first (often easiest for background/server tasks)
    if os.path.exists('service_account.json'):
        try:
            creds = service_account.Credentials.from_service_account_file(
                'service_account.json', scopes=SCOPES)
            print("[INFO] Authenticated using service_account.json")
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            print(f"[WARNING] Failed to authenticate with service_account.json: {e}")

    # 2. Fall back to OAuth2 User Flow (credentials.json + token.json)
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        except Exception as e:
            print(f"[WARNING] Failed to load token.json: {e}")
            
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"[WARNING] Failed to refresh token: {e}")
                creds = None
        
        if not creds:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError(
                    "Google Drive API credentials not found.\n"
                    "Please place either 'service_account.json' (Service Account key) or "
                    "'credentials.json' (OAuth 2.0 Desktop Client secret) in the project root directory.\n"
                    "Refer to the implementation plan for instructions."
                )
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            # This opens a local web server for authentication flow
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    print("[INFO] Authenticated using OAuth2 user credentials (token.json)")
    return build('drive', 'v3', credentials=creds)

def list_files_in_folder(folder_id: str):
    """Lists PDF and DOCX files in a Google Drive folder."""
    try:
        service = get_gdrive_service()
        # Query for files in the parent folder, not trashed, and matching PDF/DOCX mime-types
        query = (
            f"'{folder_id}' in parents and trashed = false and ("
            "mimeType = 'application/pdf' or "
            "mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'"
            ")"
        )
        
        results = service.files().list(
            q=query,
            pageSize=100,
            fields="nextPageToken, files(id, name, mimeType, size)"
        ).execute()
        
        return results.get('files', [])
    except Exception as e:
        raise Exception(f"Google Drive Error: {str(e)}")

def download_file_bytes(file_id: str, file_name: str):
    """Downloads a file's content from Google Drive and returns a file-like object."""
    try:
        service = get_gdrive_service()
        request = service.files().get_media(fileId=file_id)
        
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            
        # Reset the buffer pointer to the beginning
        file_buffer.seek(0)
        
        # Add name attribute so extract_text_from_file can detect extension
        file_buffer.name = file_name
        return file_buffer
    except Exception as e:
        raise Exception(f"Failed to download file {file_name} from Google Drive: {str(e)}")
