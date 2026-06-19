"""
Tạo Google Sheets cho UBND Bà Rịa
Chạy: python scripts/create_sheets.py
Tự động tạo 2 sheet: Theo dõi nhiệm vụ + Lịch công tác tuần
"""
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = os.getenv("TOKEN_PATH", "token.json")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
sheets = build('sheets', 'v4', credentials=creds)


def make_sheet(title):
    body = {
        'properties': {'title': title},
        'sheets': [{'properties': {'title': 'Sheet1'}}]
    }
    return sheets.spreadsheets().create(body=body).execute()


print("=" * 55)
print("  📊 UBND Bà Rịa — Tạo Google Sheets")
print("=" * 55)

# ===== SHEET 1: Theo dõi nhiệm vụ =====
print("\n📋 Đang tạo Sheet: Theo dõi nhiệm vụ...")
task = make_sheet('Theo dõi nhiệm vụ UBND Bà Rịa')
task_id = task['spreadsheetId']
m = sheets.spreadsheets().get(spreadsheetId=task_id).execute()
sid = m['sheets'][0]['properties']['sheetId']

cols = ['STT', 'Nội dung nhiệm vụ', 'Số/ký hiệu văn bản',
        'Ngày ban hành', 'Thời hạn hoàn thành', 'Chủ trì thực hiện',
        'Đơn vị phối hợp', 'Lãnh đạo phụ trách', 'Tiến độ (%)',
        'Trạng thái', 'Kết quả xử lý', 'Ghi chú']

sheets.spreadsheets().values().update(
    spreadsheetId=task_id, range='A1:L1',
    valueInputOption='USER_ENTERED', body={'values': [cols]}
).execute()

sheets.spreadsheets().batchUpdate(spreadsheetId=task_id, body={
    'requests': [{'repeatCell': {
        'range': {'sheetId': sid, 'startRowIndex': 0, 'endRowIndex': 1,
                  'startColumnIndex': 0, 'endColumnIndex': 12},
        'cell': {'userEnteredFormat': {
            'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.7},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
            'horizontalAlignment': 'CENTER',
            'borders': {'top': {'style': 'SOLID'}, 'bottom': {'style': 'SOLID'},
                        'left': {'style': 'SOLID'}, 'right': {'style': 'SOLID'}}
        }},
        'fields': 'userEnteredFormat'
    }}]
}).execute()

print(f"  ✅ ID: {task_id}")
print(f"  🔗 https://docs.google.com/spreadsheets/d/{task_id}")

# ===== SHEET 2: Lịch công tác tuần =====
print("\n📊 Đang tạo Sheet: Lịch công tác tuần...")
lich = make_sheet('Lịch công tác tuần UBND Bà Rịa')
lich_id = lich['spreadsheetId']
lm = sheets.spreadsheets().get(spreadsheetId=lich_id).execute()
lsid = lm['sheets'][0]['properties']['sheetId']

# Tiêu đề merge
sheets.spreadsheets().batchUpdate(spreadsheetId=lich_id, body={
    'requests': [{'mergeCells': {
        'range': {'sheetId': lsid, 'startRowIndex': 0, 'endRowIndex': 1,
                  'startColumnIndex': 0, 'endColumnIndex': 9},
        'mergeType': 'MERGE_ALL'
    }}]
}).execute()

title_row = [['LỊCH CÔNG TÁC TUẦN UBND PHƯỜNG BÀ RỊA']]
sheets.spreadsheets().values().update(
    spreadsheetId=lich_id, range='A1:I1',
    valueInputOption='USER_ENTERED', body={'values': title_row}
).execute()

lich_cols = ['Thứ/Ngày', 'Thời gian', 'Nội dung công việc',
             'Lãnh đạo chủ trì', 'Cơ quan chuẩn bị', 'Thành phần tham dự',
             'CB VP phụ trách', 'Địa điểm', 'Ghi chú']

sheets.spreadsheets().values().update(
    spreadsheetId=lich_id, range='A2:I2',
    valueInputOption='USER_ENTERED', body={'values': [lich_cols]}
).execute()

sheets.spreadsheets().batchUpdate(spreadsheetId=lich_id, body={
    'requests': [{'repeatCell': {
        'range': {'sheetId': lsid, 'startRowIndex': 0, 'endRowIndex': 2,
                  'startColumnIndex': 0, 'endColumnIndex': 9},
        'cell': {'userEnteredFormat': {
            'backgroundColor': {'red': 0.15, 'green': 0.35, 'blue': 0.6},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
            'horizontalAlignment': 'CENTER'
        }},
        'fields': 'userEnteredFormat'
    }}]
}).execute()

print(f"  ✅ ID: {lich_id}")
print(f"  🔗 https://docs.google.com/spreadsheets/d/{lich_id}")

# ===== Cập nhật .env =====
env_path = os.path.join(os.path.dirname(__file__), '.env')
with open(env_path, 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    "GOOGLE_SHEET_TASK_ID=1ENM0U4saYti7X3oHqgEySsHevQR6qLfC2_s3XM7PU0w",
    f"GOOGLE_SHEET_TASK_ID={task_id}"
).replace(
    "GOOGLE_SHEET_LICH_ID=1XvPGA8zXsT2NWAkpYKa1eTiSd8YfRAW4bEJ4x8FeisQ",
    f"GOOGLE_SHEET_LICH_ID={lich_id}"
)
with open(env_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n✅ Đã cập nhật .env:")
print(f"   GOOGLE_SHEET_TASK_ID={task_id}")
print(f"   GOOGLE_SHEET_LICH_ID={lich_id}")
print("\n🎉 Hoàn tất!")