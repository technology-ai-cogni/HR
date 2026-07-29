import sys
import os
from gdrive_integration import list_files_in_folder

def test_gdrive():
    if len(sys.argv) < 2:
        print("Usage: python test_gdrive.py <google-drive-folder-id>")
        sys.exit(1)
        
    folder_id = sys.argv[1]
    print(f"Testing Google Drive connection to folder ID: {folder_id}")
    
    # Check if credential files exist
    sa_exists = os.path.exists('service_account.json')
    oauth_exists = os.path.exists('credentials.json')
    token_exists = os.path.exists('token.json')
    
    print(f"Credentials status:")
    print(f" - service_account.json: {'FOUND' if sa_exists else 'NOT FOUND'}")
    print(f" - credentials.json:     {'FOUND' if oauth_exists else 'NOT FOUND'}")
    print(f" - token.json:           {'FOUND' if token_exists else 'NOT FOUND'}")
    
    if not sa_exists and not oauth_exists and not token_exists:
        print("\nERROR: No credentials found! Please add service_account.json or credentials.json to the project directory.")
        return
        
    try:
        files = list_files_in_folder(folder_id)
        print(f"\nSuccess! Found {len(files)} files in folder:")
        for idx, file in enumerate(files, 1):
            size_kb = int(file.get('size', 0)) // 1024 if file.get('size') else 0
            print(f"{idx}. {file['name']} (ID: {file['id']}, MimeType: {file['mimeType']}, Size: {size_kb} KB)")
    except Exception as e:
        print("\nError fetching folder details from Google Drive:")
        print(e)

if __name__ == "__main__":
    test_gdrive()
