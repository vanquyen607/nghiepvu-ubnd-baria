"""
Auth Init: Khởi tạo Google OAuth 2.0
Chạy script này lần đầu để tạo token.json
"""
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from google_auth_oauthlib.flow import InstalledAppFlow

CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "client_secret.json")
TOKEN_PATH = os.getenv("TOKEN_PATH", "token.json")
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/gmail.readonly'
]

print("=" * 50)
print("  Google OAuth 2.0 Authentication")
print("=" * 50)
print()
print("Cac buoc:")
print("  1. Mở trinh duyet dang nhap Google")
print("  2. Xac nhan quyen truy cap")
print("  3. Doi script tu dong luu token")
print()

try:
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    credentials = flow.run_local_server(port=3000, prompt='consent', access_type='offline')
    with open(TOKEN_PATH, 'w') as f:
        f.write(credentials.to_json())
    print(f"Da luu token vao: {TOKEN_PATH}")
    print("Xac thuc thanh cong!")
except Exception as e:
    print(f"Loi: {e}")