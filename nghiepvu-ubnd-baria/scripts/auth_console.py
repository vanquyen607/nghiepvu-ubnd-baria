import os, sys
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

flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
url, _ = flow.authorization_url(prompt='consent', access_type='offline')

print("=== MO URL NAY TRONG TRINH DUYET ===")
print(url)
print("======================================")
print()
print("Sau khi Allow, trinh duyet se chuyen huong den")
print("http://localhost:PORT/?code=...")
print()
print("Copy TOAN BO URL (bao gom ca code=...) roi paste ben duoi:")
code_url = input().strip()

# Extract code from URL
import urllib.parse
parsed = urllib.parse.urlparse(code_url)
params = urllib.parse.parse_qs(parsed.query)
code = params.get('code', [None])[0]

if not code:
    print("Khong tim thay code. Thu paste toan bo URL.")
    sys.exit(1)

flow.fetch_token(code=code)
with open(TOKEN_PATH, 'w') as f:
    f.write(flow.credentials.to_json())
print("Da luu token.json thanh cong!")
