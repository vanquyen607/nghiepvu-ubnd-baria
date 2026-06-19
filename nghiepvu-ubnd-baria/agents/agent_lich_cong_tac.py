"""
Agent 4: Lịch công tác tuần trên Google Sheets
"""
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import date, timedelta

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def run():
    os.chdir(os.path.join(os.path.dirname(__file__), "..", "scripts"))
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=".env", override=True)

    print("📊 Agent 4: Lịch công tác tuần")
    print("=" * 45)

    sheet_id = os.getenv("GOOGLE_SHEET_LICH_ID", "")
    if not sheet_id or len(sheet_id) < 10:
        print("❌ Chưa có GOOGLE_SHEET_LICH_ID")
        print("   Chạy: python scripts/create_sheets.py")
        return

    try:
        creds = Credentials.from_authorized_user_file(os.path.join(os.path.dirname(__file__), "..", "scripts", "token.json"), SCOPES)
        service = build('sheets', 'v4', credentials=creds)

        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id, range='A:I'
        ).execute()
        rows = result.get('values', [])

        if len(rows) <= 2:
            print("⚠️ Lịch công tác trống")

        print(f"\n📅 Tuần này ({date.today().strftime('%d/%m/%Y')}):")
        print(f"  {'Thứ/Ngày':<14} {'Giờ':<12} {'Nội dung':<40}")
        print(f"  {'-'*14} {'-'*12} {'-'*40}")
        for row in rows[2:]:
            thu = row[0][:12] if len(row) > 0 else "-"
            gio = row[1][:10] if len(row) > 1 else "-"
            nd = row[2][:38] if len(row) > 2 else "-"
            print(f"  {thu:<14} {gio:<12} {nd:<40}")

        print(f"\n✅ {max(0, len(rows)-2)} sự kiện trong lịch công tác tuần")

    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    run()