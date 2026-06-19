"""
Agent 2: Theo dõi nhiệm vụ chưa hoàn thành trên Google Sheets
"""
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import date

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def load_sheets():
    from dotenv import load_dotenv
    load_dotenv()
    creds = Credentials.from_authorized_user_file(os.path.join(os.path.dirname(__file__), "..", "scripts", "token.json"), SCOPES)
    return build('sheets', 'v4', credentials=creds)

def calc_status(deadline_str, done=False):
    if done:
        return "✅ Hoàn thành"
    if not deadline_str:
        return "🟢 Đang thực hiện"
    try:
        parts = deadline_str.strip().split('/')
        d = date(int(parts[2]), int(parts[1]), int(parts[0]))
        today = date.today()
        diff = (d - today).days
        if diff < 0:
            return "🔴 Quá hạn"
        elif diff <= 3:
            return "🟡 Sắp đến hạn"
        else:
            return "🟢 Đang thực hiện"
    except:
        return "🟢 Đang thực hiện"

def get_tasks(service, spreadsheet_id):
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range='A:L'
    ).execute()
    return result.get('values', [])

def run():
    newdir = os.path.join(os.path.dirname(__file__), "..", "scripts")
    os.chdir(newdir)
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=".env", override=True)

    print("📋 Agent 2: Theo dõi nhiệm vụ")
    print("=" * 45)

    sheet_id = os.getenv("GOOGLE_SHEET_TASK_ID", "")
    if not sheet_id or len(sheet_id) < 10:
        print("❌ Chưa có GOOGLE_SHEET_TASK_ID")
        print("   Chạy: python scripts/create_sheets.py")
        return

    try:
        service = load_sheets()
        rows = get_tasks(service, sheet_id)
        if len(rows) <= 1:
            print("⚠️ Sheet trống (chỉ có header)")
            return

        print(f"\n📊 {len(rows) - 1} nhiệm vụ:\n")
        print(f"  {'STT':<4} {'Nội dung':<35} {'Hạn':<12} {'Trạng thái'}")
        print(f"  {'-'*4} {'-'*35} {'-'*12} {'-'*12}")
        for i, row in enumerate(rows[1:], 1):
            content = row[1][:33] + ".." if len(row) > 1 and len(row[1]) > 33 else (row[1] if len(row) > 1 else "-")
            deadline = row[4] if len(row) > 4 else "-"
            status = row[9] if len(row) > 9 else calc_status(deadline)
            print(f"  {i:<4} {content:<35} {deadline:<12} {status}")

        print(f"\n✅ {len(rows) - 1} nhiệm vụ trong Google Sheets")

    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    run()