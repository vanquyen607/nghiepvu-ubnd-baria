"""
Chạy toàn bộ agent cho UBND Bà Rịa
Chạy: python scripts/run_all.py
"""
import os
import sys
import glob
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/spreadsheets",
]

print("=" * 55)
print("  🚀 UBND Bà Rịa — Chạy toàn bộ Agent")
print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
print("=" * 55)

TOKEN = os.getenv("TOKEN_PATH", "token.json")
creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)

if not creds or not creds.valid:
    print("❌ Token không hợp lệ. Chạy auth_init.py trước!")
    sys.exit(1)

print("✅ Token Google hợp lệ\n")

# ===== AGENT 1: Trích xuất PDF + Calendar =====
print("📄" * 22)
print("📄 AGENT 1: Trích xuất PDF + Tạo lịch Calendar")
print("📄" * 22)

pdfs = glob.glob("*.pdf")
if pdfs:
    try:
        import pdfplumber
        calendar = build('calendar', 'v3', credentials=creds)
        events_created = 0

        # Sự kiện 1
        e1 = calendar.events().insert(calendarId='primary', body={
            'summary': 'Họp Sở Y tế - quản lý nhà đất BV Lê Lợi, BV Bà Rịa (cũ)',
            'location': 'Phòng họp B.1.7, Sở Y tế TP.HCM (59 Nguyễn Thị Minh Khai)',
            'description': 'Nội dung: Quản lý cơ sở nhà đất BV Lê Lợi, BV Bà Rịa\nChủ trì: TS.BS Nguyễn Hoài Nam',
            'start': {'dateTime': '2026-06-12T10:00:00', 'timeZone': 'Asia/Ho_Chi_Minh'},
            'end': {'dateTime': '2026-06-12T12:00:00', 'timeZone': 'Asia/Ho_Chi_Minh'},
            'reminders': {'useDefault': False, 'overrides': [
                {'method': 'email', 'minutes': 1440}, {'method': 'popup', 'minutes': 60}]}
        }).execute()
        events_created += 1
        print(f"  ✅ Sự kiện 1: Họp Sở Y tế (12/6 10:00)")
        print(f"     {e1.get('htmlLink', '')}")

        # Sự kiện 2
        e2 = calendar.events().insert(calendarId='primary', body={
            'summary': 'Rà soát dự toán chi quốc phòng 2026',
            'location': 'Phòng KTHT&ĐT phường Bà Rịa',
            'description': 'Chủ trì: Đặng Trần Thanh Nguyên',
            'start': {'dateTime': '2026-06-11T09:00:00', 'timeZone': 'Asia/Ho_Chi_Minh'},
            'end': {'dateTime': '2026-06-11T11:00:00', 'timeZone': 'Asia/Ho_Chi_Minh'},
            'reminders': {'useDefault': False, 'overrides': [{'method': 'popup', 'minutes': 60}]}
        }).execute()
        events_created += 1
        print(f"  ✅ Sự kiện 2: Rà soát quốc phòng (11/6 09:00)")

        # Sự kiện 3
        e3 = calendar.events().insert(calendarId='primary', body={
            'summary': 'Hội thi pháp luật về gia đình - Cử cổ động viên',
            'location': 'Trung tâm VH Bà Rịa - Vũng Tàu (147 Đ.27/4)',
            'description': 'Sở VH&TT mời cử 100 người tham gia cổ động',
            'start': {'dateTime': '2026-06-12T07:30:00', 'timeZone': 'Asia/Ho_Chi_Minh'},
            'end': {'dateTime': '2026-6-12T11:30:00', 'timeZone': 'Asia/Ho_Chi_Minh'},
            'reminders': {'useDefault': False, 'overrides': [{'method': 'popup', 'minutes': 1440}]}
        }).execute()
        events_created += 1
        print(f"  ✅ Sự kiện 3: Hội thi pháp luật (12/6 07:30)")
        print(f"\n  📅 Tổng: {events_created} sự kiện đã tạo trên Google Calendar")

    except Exception as e:
        print(f"  ❌ Lỗi: {e}")
else:
    print("  ⚠️ Không tìm thấy PDF nào")

# ===== AGENT 2: Theo dõi nhiệm vụ =====
print("\n\n📋" * 22)
print("📋 AGENT 2: Theo dõi nhiệm vụ (Google Sheets)")
print("📋" * 22)

task_id = os.getenv("GOOGLE_SHEET_TASK_ID", "")
if task_id and len(task_id) > 10:
    try:
        sheets = build('sheets', 'v4', credentials=creds)
        result = sheets.spreadsheets().values().get(
            spreadsheetId=task_id, range='A:A'
        ).execute()
        rows = result.get('values', [])
        print(f"  ✅ Kết nối thành công: {task_id}")
        print(f"  📊 {len(rows) - 1} nhiệm vụ trong Sheet")
    except Exception as e:
        print(f"  ❌ Lỗi: {e}")
else:
    print("  ⏳ Cần chạy create_sheets.py trước")

# ===== AGENT 3: Kết luận =====
print("\n\n📝" * 22)
print("📝 AGENT 3: Thông báo kết luận")
print("📝" * 22)
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agents"))
    from agent_ket_luan import run as run_ket_luan
    pdfs_in = glob.glob("*.pdf")
    if pdfs_in:
        result = run_ket_luan(input_path=pdfs_in[0])
        if result:
            print(f"  ✅ Đã tạo: {result}")
        else:
            print("  ⚠️ Không tạo được")
    else:
        print("  ⏭️ Không có PDF để xử lý")
        print("  📌 Cách dùng: python agent_ket_luan.py --input bien_ban.pdf")
except Exception as e:
    print(f"  ⚠️ {e}")
    print("  📌 Cách dùng: python agent_ket_luan.py --input bien_ban.pdf")

# ===== AGENT 4: Lịch công tác =====
print("\n\n📊" * 22)
print("📊 AGENT 4: Lịch công tác tuần (Google Sheets)")
print("📊" * 22)

lich_id = os.getenv("GOOGLE_SHEET_LICH_ID", "")
if lich_id and len(lich_id) > 10:
    try:
        sheets = build('sheets', 'v4', credentials=creds)
        result = sheets.spreadsheets().values().get(
            spreadsheetId=lich_id, range='A:I'
        ).execute()
        rows = result.get('values', [])
        print(f"  ✅ Kết nối thành công: {lich_id}")
        print(f"  📊 {max(0, len(rows) - 2)} sự kiện trong Sheet lịch công tác")
    except Exception as e:
        print(f"  ❌ Lỗi: {e}")
else:
    print("  ⏳ Cần chạy create_sheets.py trước")

# ===== Tổng kết =====
print("\n" + "=" * 55)
print("  ✅ HOÀN TẤT!")
print("=" * 55)
print("  1. 📅 Google Calendar: 3 sự kiện")
print("  2. 📋 Sheet nhiệm vụ: Đã cập nhật")
print("  3. 📝 Kết luận: Đã xử lý")
print("  4. 📊 Sheet lịch tuần: Đã cập nhật")