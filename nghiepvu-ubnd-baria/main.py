#!/usr/bin/env python3
"""
UBND PHƯỜNG BÀ RỊA - HỆ THỐNG TỰ ĐỘNG HÓA NGHIỆP VỤ HÀNH CHÍNH
Menu tương tác: quản lý nhiệm vụ, lịch công tác, PDF, Calendar
"""
import os
import sys
import glob
import re
from datetime import datetime, date, timezone

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.join(BASE, "scripts"))

from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN = os.getenv("TOKEN_PATH", "token.json")
LICH_SHEET_ID = os.getenv("GOOGLE_SHEET_LICH_ID", "")
TASK_SHEET_ID = os.getenv("GOOGLE_SHEET_TASK_ID", "")
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
SHEET_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CAL_SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_creds(scopes):
    token_path = os.path.join(BASE, "scripts", TOKEN)
    return Credentials.from_authorized_user_file(token_path, scopes)


def sheets_service():
    return build('sheets', 'v4', credentials=get_creds(SHEET_SCOPES))


def calendar_service():
    return build('calendar', 'v3', credentials=get_creds(CAL_SCOPES))


# ============================================================
#  HÀM TIỆN ÍCH
# ============================================================

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title):
    clear_screen()
    w = 60
    print("=" * w)
    print(f"  {title}")
    print("=" * w)


def pause():
    input("\nNhấn Enter để tiếp tục...")


def read_sheet(sheet_id, range_):
    s = sheets_service()
    r = s.spreadsheets().values().get(spreadsheetId=sheet_id, range=range_).execute()
    return r.get('values', [])


def write_sheet(sheet_id, range_, values):
    s = sheets_service()
    s.spreadsheets().values().append(
        spreadsheetId=sheet_id, range=range_,
        valueInputOption='USER_ENTERED',
        body={'values': [values]}
    ).execute()


def update_sheet(sheet_id, range_, values):
    s = sheets_service()
    s.spreadsheets().values().update(
        spreadsheetId=sheet_id, range=range_,
        valueInputOption='USER_ENTERED',
        body={'values': [values]}
    ).execute()


def delete_row_sheet(sheet_id, row_index):
    """Xoá dòng theo index (1-based)"""
    s = sheets_service()
    m = s.spreadsheets().get(spreadsheetId=sheet_id).execute()
    sid = m['sheets'][0]['properties']['sheetId']
    s.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={
        'requests': [{
            'deleteDimension': {
                'range': {
                    'sheetId': sid,
                    'dimension': 'ROWS',
                    'startIndex': row_index - 1,
                    'endIndex': row_index
                }
            }
        }]
    }).execute()


# ============================================================
#  MENU: XỬ LÝ PDF
# ============================================================

def menu_pdf():
    print_header("📄 XỬ LÝ PDF")
    pdfs = sorted(glob.glob("*.pdf"))
    if pdfs:
        print(f"\n📁 PDF trong thư mục scripts/ ({len(pdfs)} file):")
        for i, p in enumerate(pdfs, 1):
            size = os.path.getsize(p)
            print(f"   {i}. {p} ({size//1024}KB)")
    else:
        print("\n⚠️ Không có file PDF nào trong thư mục scripts/")
        print(f"   Hãy copy PDF vào: {os.path.join(BASE, 'scripts')}\\")

    print("\nChọn thao tác:")
    print("   1. Xử lý PDF → Calendar + Sheets")
    print("   2. Xem kết quả trích xuất gần nhất")
    print("   3. Quay lại")
    choice = input(">> ").strip()

    if choice == "1":
        from agents.agent_calendar import run as run_agent1
        run_agent1()
    elif choice == "2":
        try:
            import json
            with open("ket_qua_trich_xuat.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                print(f"\n📄 {item['file']}")
                print(f"   Loại: {item.get('loai', '')}")
                print(f"   Nội dung: {item.get('noi_dung', '')[:60]}")
                print(f"   Thời gian: {item.get('thoi_gian_hop', '')[:50]}")
                print(f"   Địa điểm: {item.get('dia_diem', '')[:50]}")
        except:
            print("⚠️ Chưa có dữ liệu trích xuất nào")

    pause()


# ============================================================
#  MENU: QUẢN LÝ NHIỆM VỤ (CRUD)
# ============================================================

def view_tasks():
    rows = read_sheet(TASK_SHEET_ID, 'A:L')
    if len(rows) <= 1:
        print("⚠️ Chưa có nhiệm vụ nào")
        return rows

    print(f"\n📋 {len(rows) - 1} nhiệm vụ:")
    print(f"  {'#':<3} {'Nội dung':<40} {'Hạn':<12} {'Trạng thái'}")
    print(f"  {'-'*3} {'-'*40} {'-'*12} {'-'*15}")
    for i, row in enumerate(rows[1:], 1):
        nd = row[1][:38] if len(row) > 1 else "-"
        han = row[4][:10] if len(row) > 4 else "-"
        tt = row[9] if len(row) > 9 else "🟢 Đang thực hiện"
        print(f"  {i:<3} {nd:<40} {han:<12} {tt}")
    return rows


def add_task():
    print_header("➕ THÊM NHIỆM VỤ MỚI")
    nd = input("Nội dung nhiệm vụ: ").strip()
    if not nd:
        print("⚠️ Không được để trống")
        return
    so_vb = input("Số/ký hiệu văn bản: ").strip()
    ngay_bh = input("Ngày ban hành (dd/mm/yyyy): ").strip()
    han = input("Thời hạn hoàn thành (dd/mm/yyyy): ").strip()
    chu_tri = input("Chủ trì thực hiện: ").strip()
    phoi_hop = input("Đơn vị phối hợp: ").strip()
    lanh_dao = input("Lãnh đạo phụ trách: ").strip()

    row = ["", nd, so_vb, ngay_bh, han, chu_tri, phoi_hop, lanh_dao, "", "🟢 Đang thực hiện", "", ""]
    write_sheet(TASK_SHEET_ID, 'A:L', row)
    print("✅ Đã thêm nhiệm vụ!")


def edit_task():
    rows = view_tasks()
    if len(rows) <= 1:
        pause()
        return

    try:
        idx = int(input(f"\nSố thứ tự nhiệm vụ cần sửa (1-{len(rows)-1}): "))
        if idx < 1 or idx > len(rows) - 1:
            raise ValueError
    except:
        print("⚠️ Số không hợp lệ")
        return

    old = rows[idx]
    print(f"\nĐang sửa: {old[1][:40] if len(old) > 1 else ''}")
    fields = [
        ("Nội dung", 1), ("Số VB", 2), ("Ngày ban hành", 3),
        ("Hạn hoàn thành", 4), ("Chủ trì", 5), ("Phối hợp", 6),
        ("Lãnh đạo", 7), ("Tiến độ %", 8), ("Trạng thái", 9)
    ]
    new_vals = ["" for _ in range(12)]
    for name, col in fields:
        cur = old[col] if len(old) > col else ""
        val = input(f"  {name} ({cur}): ").strip()
        new_vals[col] = val if val else cur

    range_ = f"A{idx+1}:L{idx+1}"
    final = [new_vals[c] if new_vals[c] else (old[c] if len(old) > c else "") for c in range(12)]
    update_sheet(TASK_SHEET_ID, range_, final)
    print("✅ Đã cập nhật!")


def delete_task():
    rows = view_tasks()
    if len(rows) <= 1:
        pause()
        return

    try:
        idx = int(input(f"\nSố thứ tự nhiệm vụ cần xoá (1-{len(rows)-1}): "))
        if idx < 1 or idx > len(rows) - 1:
            raise ValueError
    except:
        print("⚠️ Số không hợp lệ")
        return

    nd = rows[idx][1][:30] if len(rows[idx]) > 1 else ""
    confirm = input(f"Xoá '{nd}...'? (y/n): ").strip().lower()
    if confirm == 'y':
        delete_row_sheet(TASK_SHEET_ID, idx + 1)
        print("✅ Đã xoá!")


def update_task_status():
    rows = view_tasks()
    if len(rows) <= 1:
        pause()
        return

    try:
        idx = int(input(f"\nSố thứ tự (1-{len(rows)-1}): "))
        if idx < 1 or idx > len(rows) - 1:
            raise ValueError
    except:
        print("⚠️ Số không hợp lệ")
        return

    print("\nChọn trạng thái:")
    print("   1. 🔴 Quá hạn")
    print("   2. 🟡 Sắp đến hạn")
    print("   3. 🟢 Đang thực hiện")
    print("   4. ✅ Hoàn thành")
    c = input(">> ").strip()
    status_map = {"1": "🔴 Quá hạn", "2": "🟡 Sắp đến hạn", "3": "🟢 Đang thực hiện", "4": "✅ Hoàn thành"}
    status = status_map.get(c, "")
    if not status:
        print("⚠️ Sai lựa chọn")
        return

    row_idx = idx + 1
    update_sheet(TASK_SHEET_ID, f"J{row_idx}", [[status]])
    print(f"✅ Đã cập nhật trạng thái: {status}")


def menu_task():
    while True:
        print_header("📋 QUẢN LÝ NHIỆM VỤ (THEO DÕI NHIỆM VỤ)")
        view_tasks()
        print("\nChọn thao tác:")
        print("   1. ➕ Thêm nhiệm vụ")
        print("   2. ✏️ Sửa nhiệm vụ")
        print("   3. 🗑️ Xoá nhiệm vụ")
        print("   4. 🔄 Cập nhật trạng thái")
        print("   5. 🔙 Quay lại")
        choice = input(">> ").strip()

        if choice == "1":
            add_task()
        elif choice == "2":
            edit_task()
        elif choice == "3":
            delete_task()
        elif choice == "4":
            update_task_status()
        elif choice == "5":
            break
        pause()


# ============================================================
#  MENU: THÔNG BÁO KẾT LUẬN
# ============================================================

def menu_ket_luan():
    print_header("📝 THÔNG BÁO KẾT LUẬN")

    pdfs = sorted(glob.glob("*.pdf"))
    if pdfs:
        print("📁 Chọn file PDF để xử lý:")
        for i, p in enumerate(pdfs, 1):
            print(f"   {i}. {p}")
        print(f"   {len(pdfs)+1}. Nhập đường dẫn khác")
        print(f"   {len(pdfs)+2}. Quay lại")
        c = input(">> ").strip()

        if c.isdigit() and 1 <= int(c) <= len(pdfs):
            from agents.agent_ket_luan import run as run_agent3
            run_agent3(input_path=pdfs[int(c) - 1])
        elif c == str(len(pdfs) + 1):
            path = input("Đường dẫn file: ").strip()
            if path:
                from agents.agent_ket_luan import run as run_agent3
                run_agent3(input_path=path)
    else:
        print("\n⚠️ Không có PDF trong thư mục scripts/")
        path = input("Nhập đường dẫn file (PDF/DOCX/TXT): ").strip()
        if path:
            from agents.agent_ket_luan import run as run_agent3
            run_agent3(input_path=path)

    pause()


# ============================================================
#  MENU: QUẢN LÝ LỊCH CÔNG TÁC (CRUD)
# ============================================================

def view_schedule():
    rows = read_sheet(LICH_SHEET_ID, 'A:I')
    if len(rows) <= 2:
        print("⚠️ Lịch công tác trống")
        return rows

    print(f"\n📅 {len(rows) - 2} sự kiện:")
    print(f"  {'#':<3} {'Thứ/Ngày':<14} {'Giờ':<8} {'Nội dung':<40} {'Địa điểm':<25}")
    print(f"  {'-'*3} {'-'*14} {'-'*8} {'-'*40} {'-'*25}")
    for i, row in enumerate(rows[2:], 1):
        thu = row[0][:12] if len(row) > 0 else "-"
        gio = row[1][:6] if len(row) > 1 else "-"
        nd = row[2][:38] if len(row) > 2 else "-"
        dc = row[7][:23] if len(row) > 7 else "-"
        print(f"  {i:<3} {thu:<14} {gio:<8} {nd:<40} {dc:<25}")
    return rows


def add_event():
    print_header("➕ THÊM SỰ KIỆN")
    thu = input("Thứ / Ngày: ").strip()
    gio = input("Thời gian: ").strip()
    nd = input("Nội dung công việc: ").strip()
    if not nd:
        print("⚠️ Không được để trống")
        return
    lanh_dao = input("Lãnh đạo chủ trì: ").strip()
    co_quan = input("Cơ quan chuẩn bị: ").strip()
    tp = input("Thành phần tham dự: ").strip()
    cb = input("CB VP phụ trách: ").strip()
    dc = input("Địa điểm: ").strip()
    ghichu = input("Ghi chú: ").strip()

    row = [thu, gio, nd, lanh_dao, co_quan, tp, cb, dc, ghichu]
    write_sheet(LICH_SHEET_ID, 'A:I', row)
    print("✅ Đã thêm sự kiện!")


def edit_event():
    rows = view_schedule()
    if len(rows) <= 2:
        pause()
        return

    try:
        idx = int(input(f"\nSố thứ tự sự kiện cần sửa (1-{len(rows)-2}): "))
        if idx < 1 or idx > len(rows) - 2:
            raise ValueError
    except:
        print("⚠️ Số không hợp lệ")
        return

    old = rows[idx + 1]
    print(f"\nĐang sửa: {old[2][:40] if len(old) > 2 else ''}")
    fields = [
        ("Thứ/Ngày", 0), ("Thời gian", 1), ("Nội dung", 2),
        ("Lãnh đạo chủ trì", 3), ("Cơ quan chuẩn bị", 4),
        ("Thành phần", 5), ("CB VP phụ trách", 6),
        ("Địa điểm", 7), ("Ghi chú", 8)
    ]
    new_vals = []
    for name, col in fields:
        cur = old[col] if len(old) > col else ""
        val = input(f"  {name} ({cur}): ").strip()
        new_vals.append(val if val else cur)

    update_sheet(LICH_SHEET_ID, f"A{idx+2}:I{idx+2}", new_vals)
    print("✅ Đã cập nhật!")


def delete_event():
    rows = view_schedule()
    if len(rows) <= 2:
        pause()
        return

    try:
        idx = int(input(f"\nSố thứ tự cần xoá (1-{len(rows)-2}): "))
        if idx < 1 or idx > len(rows) - 2:
            raise ValueError
    except:
        print("⚠️ Số không hợp lệ")
        return

    nd = rows[idx + 1][2][:30] if len(rows[idx + 1]) > 2 else ""
    confirm = input(f"Xoá '{nd}...'? (y/n): ").strip().lower()
    if confirm == 'y':
        delete_row_sheet(LICH_SHEET_ID, idx + 2)
        print("✅ Đã xoá!")


def menu_schedule():
    while True:
        print_header("📊 QUẢN LÝ LỊCH CÔNG TÁC TUẦN")
        view_schedule()
        print("\nChọn thao tác:")
        print("   1. ➕ Thêm sự kiện")
        print("   2. ✏️ Sửa sự kiện")
        print("   3. 🗑️ Xoá sự kiện")
        print("   4. 🔙 Quay lại")
        choice = input(">> ").strip()

        if choice == "1":
            add_event()
        elif choice == "2":
            edit_event()
        elif choice == "3":
            delete_event()
        elif choice == "4":
            break
        pause()


# ============================================================
#  MENU: CALENDAR
# ============================================================

def view_calendar():
    print_header("📅 GOOGLE CALENDAR - SỰ KIỆN SẮP TỚI")
    try:
        cal = calendar_service()
        now = datetime.now(datetime.timezone.utc).isoformat()
        events = cal.events().list(
            calendarId=CALENDAR_ID, timeMin=now,
            maxResults=10, singleEvents=True,
            orderBy='startTime'
        ).execute()

        items = events.get('items', [])
        if not items:
            print("⚠️ Không có sự kiện nào sắp tới")
        else:
            for i, ev in enumerate(items, 1):
                start = ev['start'].get('dateTime', ev['start'].get('date', ''))[:16]
                summary = ev.get('summary', '(không tiêu đề)')[:50]
                loc = ev.get('location', '')[:25]
                print(f"  {i}. {start} - {summary}")
                if loc:
                    print(f"     📍 {loc}")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
    pause()


# ============================================================
#  MENU: CHẠY TẤT CẢ
# ============================================================

def menu_run_all():
    print_header("🚀 CHẠY TẤT CẢ AGENT")
    print("\nQuy trình xử lý:")
    print("  1. 📄 Agent 1: PDF → Calendar + Sheets")
    print("  2. 📋 Agent 2: Theo dõi nhiệm vụ")
    print("  3. 📝 Agent 3: Thông báo kết luận")
    print("  4. 📊 Agent 4: Lịch công tác tuần")
    print()
    c = input("Xác nhận chạy toàn bộ? (y/n): ").strip().lower()
    if c != 'y':
        return

    import subprocess
    result = subprocess.run(
        [sys.executable, os.path.join(BASE, "scripts", "run_all.py")],
        capture_output=False
    )


# ============================================================
#  MENU: ĐỒNG BỘ DỮ LIỆU
# ============================================================

def menu_sync():
    print_header("🔄 ĐỒNG BỘ DỮ LIỆU")
    print("\nĐồng bộ dữ liệu từ các nguồn:")
    print("   1. Đọc PDF mới → Cập nhật Calendar + Sheets")
    print("   2. Đồng bộ trạng thái nhiệm vụ (tính toán quá hạn)")
    print("   3. Xử lý tất cả PDF thành Thông báo kết luận")

    choice = input("\n>> ").strip()

    if choice == "1":
        from agents.agent_calendar import run as run_agent1
        run_agent1()
    elif choice == "2":
        rows = read_sheet(TASK_SHEET_ID, 'A:L')
        updated = 0
        for i, row in enumerate(rows[1:], 2):
            if len(row) > 9 and row[9] == "✅ Hoàn thành":
                continue
            deadline = row[4] if len(row) > 4 else ""
            if deadline:
                try:
                    parts = deadline.strip().split('/')
                    d = date(int(parts[2]), int(parts[1]), int(parts[0]))
                    diff = (d - date.today()).days
                    if diff < 0:
                        new_status = "🔴 Quá hạn"
                    elif diff <= 3:
                        new_status = "🟡 Sắp đến hạn"
                    else:
                        new_status = "🟢 Đang thực hiện"
                    update_sheet(TASK_SHEET_ID, f"J{i}", [[new_status]])
                    updated += 1
                except:
                    pass
        print(f"✅ Đã đồng bộ {updated} nhiệm vụ")
    elif choice == "3":
        from agents.agent_ket_luan import run as run_agent3
        for pdf in sorted(glob.glob("*.pdf")):
            print(f"\n📄 {pdf}")
            run_agent3(input_path=pdf)

    pause()


# ============================================================
#  MAIN MENU
# ============================================================

def main():
    while True:
        clear_screen()
        w = 60
        print("=" * w)
        print("  🏛️  UBND PHƯỜNG BÀ RỊA")
        print("  HỆ THỐNG TỰ ĐỘNG HÓA NGHIỆP VỤ HÀNH CHÍNH")
        print("=" * w)
        print(f"  📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print("-" * w)
        print("   1. 📄 Xử lý PDF → Calendar + Sheets")
        print("   2. 📋 Quản lý nhiệm vụ (Thêm/Sửa/Xoá/Trạng thái)")
        print("   3. 📝 Thông báo kết luận cuộc họp")
        print("   4. 📊 Quản lý lịch công tác tuần (Thêm/Sửa/Xoá)")
        print("   5. 📅 Xem sự kiện Google Calendar")
        print("   6. 🚀 Chạy tất cả Agent")
        print("   7. 🔄 Đồng bộ dữ liệu")
        print("-" * w)
        print("   0. Thoát")
        print("=" * w)

        choice = input(">> ").strip()

        if choice == "1":
            menu_pdf()
        elif choice == "2":
            menu_task()
        elif choice == "3":
            menu_ket_luan()
        elif choice == "4":
            menu_schedule()
        elif choice == "5":
            view_calendar()
        elif choice == "6":
            menu_run_all()
        elif choice == "7":
            menu_sync()
        elif choice == "0":
            print("\n👋 Tạm biệt!")
            break
        else:
            print("⚠️ Lựa chọn không hợp lệ")
            pause()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Tạm biệt!")
