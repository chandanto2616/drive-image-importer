"""
 - Service account: Your app authenticates to Google Drive using the service account JSON file.

 - build('drive', 'v3', ...): Creates a Drive API client. This is your "remote control" to read files from Drive. """


# shared/utils.py

from google.oauth2 import service_account
from googleapiclient.discovery import build

def get_drive_service():
    credentials = service_account.Credentials.from_service_account_file("service_account.json")
    service = build('drive', 'v3', credentials=credentials)
    return service

