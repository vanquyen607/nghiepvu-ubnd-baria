"""
Agent 1: Trích xuất PDF → Google Calendar + Google Sheets
"""
import os
import glob
import sys
import re
from datetime import datetime, date
sys.stdout.reconfigure(encoding='utf-8')

try:
    import pdfplumber
except ImportError:
    print("❌ Cài đặt: pip install pdfplumber")
    sys.exit(1)

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/spreadsheets",
]


def load_services():
    from dotenv import load_dotenv
    dotenv_path = os.path.join(os.path.dirname(__file__), "..", "scripts", ".env")
    load_dotenv(dotenv_path=dotenv_path, override=True)
    token_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "token.json")
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    calendar = build('calendar', 'v3', credentials=creds)
    sheets = build('sheets', 'v4', credentials=creds)
    return calendar, sheets


def parse_time(text):
    res = {"gio": "", "phut": "00", "ngay": "", "thang": "", "nam": str(date.today().year), "thu": ""}

    # Tìm dòng chứa thời gian họp (ưu tiên)
    time_line = ""
    for line in text.split("\n"):
        if any(kw in line.lower() for kw in ["thời gian", "vào lúc", "lúc "]):
            time_line = line
            break

    search_text = time_line or text

    # Giờ
    gio_m = re.search(r"(\d{1,2})\s*giờ\s*(\d{2})?\s*phút", search_text)
    if gio_m:
        res["gio"] = gio_m.group(1)
        res["phut"] = gio_m.group(2) or "00"

    # Ngày tháng - ưu tiên định dạng "ngày Z tháng W năm V"
    ngay_m = re.search(r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})(?:\s+năm\s+(\d{4}))?", search_text, re.I)
    if ngay_m:
        res["ngay"] = ngay_m.group(1)
        res["thang"] = ngay_m.group(2)
        if ngay_m.group(3):
            res["nam"] = ngay_m.group(3)
    else:
        # Định dạng "ngày Z/W/V" hoặc "Z/W/V"
        sl_m = re.search(r"(\d{1,2})/(\d{1,2})(?:/(\d{4}))?", search_text)
        if sl_m:
            res["ngay"] = sl_m.group(1)
            res["thang"] = sl_m.group(2)
            if sl_m.group(3):
                res["nam"] = sl_m.group(3)
        else:
            # Định dạng "ngày Z.W" (dấu chấm)
            dot_m = re.search(r"ngày\s+(\d{1,2})[./](\d{1,2})", search_text)
            if dot_m:
                res["ngay"] = dot_m.group(1)
                res["thang"] = dot_m.group(2)

    # Thứ
    thu_map = {"2": "Thứ Hai", "3": "Thứ Ba", "4": "Thứ Tư", "5": "Thứ Năm",
               "6": "Thứ Sáu", "7": "Thứ Bảy", "cn": "Chủ Nhật"}
    thu_m = re.search(r"thứ\s*(\d|cn)", time_line or text, re.I)
    if thu_m:
        res["thu"] = thu_map.get(thu_m.group(1).lower(), "")

    return res


def parse_location(text):
    loc = ""
    lines = text.split("\n")

    for i, line in enumerate(lines):
        ls = line.strip()

        # "1. Thời gian, địa điểm: ... tại ..." - có thể xuống dòng
        if re.match(r"^\d+\.?\s*Thời gian,\s*địa điểm", ls, re.I):
            combined = ls
            for j in range(i + 1, min(i + 4, len(lines))):
                nxt = lines[j].strip()
                if not nxt or re.match(r"^\d+\.", nxt) or any(kw in nxt.lower() for kw in ["số lượng", "kính gửi"]):
                    break
                combined += " " + nxt
            m = re.search(r"tại\s+(.+)", combined, re.I)
            if m:
                loc = m.group(1).rstrip(".,;")
            break

        if "địa điểm" in ls.lower() and not re.match(r"^\d+\.?\s*Thời gian", ls, re.I):
            loc = re.sub(r"^[-•\s]*(Địa điểm|địa điểm|Địa)\s*[:\-]?\s*", "", ls).strip().rstrip(".,;")
            break

    return loc


def parse_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as p:
        for page in p.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"

    lines = text.split("\n")
    info = {
        "file": os.path.basename(pdf_path),
        "text": text,
        "content": "",
        "location": "",
        "time_str": "",
        "chu_tri": "",
        "thanh_phan": [],
        "so_hieu": "",
        **parse_time(text),
    }

    # Số hiệu văn bản (từ nội dung PDF, kết hợp số từ tên file)
    fname_num = os.path.basename(pdf_path).split('.')[0]
    for line in lines:
        m = re.match(r'^\s*Số\s*:\s*(.*)$', line.strip(), re.I)
        if m:
            raw = m.group(1).strip()
            dept = re.match(r'^(\/[^\s]+)', raw)
            if dept:
                info["so_hieu"] = f"{fname_num}{dept.group(1)}"
            elif raw:
                info["so_hieu"] = raw
            break
    if not info["so_hieu"]:
        info["so_hieu"] = fname_num

    # Nội dung
    for i, line in enumerate(lines):
        ls = line.strip()

        if not ls:
            continue

        # "- Nội dung: ..."
        m = re.match(r"^[-•]?\s*Nội dung\s*:\s*(.+)", ls, re.I)
        if m:
            info["content"] = m.group(1).strip()
            break

        # "Về nội dung ..." hoặc "Về việc ..." - gom các dòng tiếp theo
        if ls.lower().startswith("về nội dung") or ls.lower().startswith("về việc"):
            parts = [ls]
            for j in range(i + 1, min(i + 5, len(lines))):
                nxt = lines[j].strip()
                if not nxt or any(kw in nxt.lower() for kw in ["kính gửi", "kính mời", "số:"]):
                    break
                parts.append(nxt)
            info["content"] = " ".join(parts)
            break

    if not info["content"]:
        for line in lines[:15]:
            ls = line.strip()
            if ls and len(ls) > 20 and not any(kw in ls.upper() for kw in
                ["ỦY BAN", "CỘNG HÒA", "ĐỘC LẬP", "SỐ:", "GIẤY MỜI", "KÍNH GỬI"]):
                info["content"] = ls
                break

    # Địa điểm
    info["location"] = parse_location(text)

    # Chủ trì (lấy từ người ký cuối văn bản)
    for i, line in enumerate(lines):
        ls = line.strip()
        if "chủ trì" in ls.lower():
            info["chu_tri"] = re.sub(r"^[-•\s]*(Chủ trì|chủ trì)\s*[:\-]?\s*", "", ls).strip().rstrip(".,;")
            break

    # Nếu không có "Chủ trì" rõ, lấy từ chức danh người ký cuối
    if not info["chu_tri"]:
        sign_lines = []
        for i, line in enumerate(lines):
            ls = line.strip()
            if re.match(r'KT\.', ls, re.I) or re.match(r'TM\.', ls, re.I):
                # Lấy dòng chức danh và dòng họ tên phía sau
                for j in range(i, min(i + 4, len(lines))):
                    nxt = lines[j].strip()
                    if nxt and not any(kw in nxt.lower() for kw in
                        ["nơi nhận", "lưu:", "vt."]):
                        sign_lines.append(nxt)
                break
        if len(sign_lines) >= 2:
            info["chu_tri"] = sign_lines[-1]  # Lấy tên người ký
        elif len(sign_lines) >= 1:
            info["chu_tri"] = sign_lines[0]

    # Đơn vị chuẩn bị
    info["don_vi_chuan_bi"] = ""
    for line in lines:
        ls = line.strip()
        m = re.search(r"Đơn\s+vị\s+chuẩn\s+bị\s*(tài\s+liệu)?\s*[:\-]?\s*(.+)", ls, re.I)
        if m:
            info["don_vi_chuan_bi"] = m.group(2).strip().rstrip(".,;")
            break

    # Thành phần (các bullet "-" ngay sau "Kính gửi")
    info["thanh_phan"] = []
    in_kg = False
    for line in lines:
        ls = line.strip()
        if "kính gửi" in ls.lower():
            in_kg = True
            continue
        if in_kg:
            if ls.startswith("-") or ls.startswith("•"):
                t = ls.lstrip("-• ").strip().rstrip(".,;")
                if t:
                    info["thanh_phan"].append(t)
            elif info["thanh_phan"]:
                # Dòng không phải bullet: nếu ngắn (<20 ký tự) thì là tiếp nối bullet cuối
                if len(ls) < 20 and ls and not any(kw in ls.lower() for kw in
                    ["kính mời", "nội dung", "thời gian"]):
                    info["thanh_phan"][-1] += " " + ls.rstrip(".,;")
                else:
                    break

    # Địa điểm
    info["location"] = parse_location(text)

    # Chủ trì
    for line in lines:
        ls = line.strip()
        if "chủ trì" in ls.lower():
            info["chu_tri"] = re.sub(r"^[-•\s]*(Chủ trì|chủ trì)\s*[:\-]?\s*", "", ls).strip().rstrip(".,;")
            break

    # Thời gian string
    for line in lines:
        ls = line.strip()
        if any(kw in ls.lower() for kw in ["thời gian", "vào lúc", "lúc "]):
            info["time_str"] = ls
            break

    return info


def to_sheets_row(info):
    gio = f"{info['gio']}:{info['phut'].zfill(2)}" if info['gio'] else ""
    thu_ngay = ""
    if info["thu"] and info["ngay"] and info["thang"]:
        thu_ngay = f"{info['thu']} {info['ngay']}/{info['thang']}"
    elif info["ngay"] and info["thang"]:
        thu_ngay = f"{info['ngay']}/{info['thang']}"
    elif info["ngay"]:
        thu_ngay = info["ngay"]

    tp = "; ".join(info["thanh_phan"][:3]) if info["thanh_phan"] else ""
    dvcb = info.get("don_vi_chuan_bi", "")
    return [thu_ngay, gio, info["content"], info["chu_tri"], dvcb, tp, "", info["location"], ""]


def to_calendar_event(info):
    if not all([info["ngay"], info["thang"], info["gio"]]):
        return None
    nam = info["nam"]
    start = f"{nam}-{info['thang'].zfill(2)}-{info['ngay'].zfill(2)}T{info['gio'].zfill(2)}:{info['phut'].zfill(2)}:00"
    gio_end = int(info["gio"]) + 2
    end = f"{nam}-{info['thang'].zfill(2)}-{info['ngay'].zfill(2)}T{gio_end:02d}:{info['phut'].zfill(2)}:00"
    tp_text = "\n".join(f"- {t}" for t in info["thanh_phan"]) if info["thanh_phan"] else ""
    desc = f"Nội dung: {info['content']}\nChủ trì: {info['chu_tri']}"
    if tp_text:
        desc += f"\nThành phần:\n{tp_text}"
    return {
        'summary': info["content"][:80] if info["content"] else f"Cuộc họp ({info['file']})",
        'location': info["location"],
        'description': desc,
        'start': {'dateTime': start, 'timeZone': 'Asia/Ho_Chi_Minh'},
        'end': {'dateTime': end, 'timeZone': 'Asia/Ho_Chi_Minh'},
        'reminders': {'useDefault': False, 'overrides': [
            {'method': 'email', 'minutes': 1440}, {'method': 'popup', 'minutes': 60}
        ]}
    }


def run():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scripts_dir = os.path.join(base, "scripts")
    os.chdir(scripts_dir)

    from dotenv import load_dotenv
    load_dotenv(dotenv_path=".env", override=True)

    lich_sheet_id = os.getenv("GOOGLE_SHEET_LICH_ID", "")
    task_sheet_id = os.getenv("GOOGLE_SHEET_TASK_ID", "")

    print("📅 Agent 1: PDF → Google Calendar + Sheets")
    print("=" * 50)

    try:
        calendar, sheets = load_services()
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")
        return

    pdfs = sorted(glob.glob("*.pdf"))
    if not pdfs:
        print("⚠️ Không có PDF nào trong thư mục scripts/")
        return

    calendar_ok = 0
    sheets_ok = 0

    for pdf in pdfs:
        print(f"\n📄 {pdf}")
        info = parse_pdf(pdf)
        print(f"   📝 {info['content'][:60]}")
        print(f"   📍 {info['location'][:50]}")
        print(f"   🕐 {info['gio']}h{info['phut']} ngày {info['ngay']}/{info['thang']}/{info['nam']}")
        print(f"   🏷 Số hiệu: {info['so_hieu']}")

        ev = to_calendar_event(info)
        if ev:
            try:
                created = calendar.events().insert(calendarId='primary', body=ev).execute()
                calendar_ok += 1
                print(f"   ✅ Calendar: {created.get('summary', '')[:40]}")
            except Exception as e:
                print(f"   ⚠️ Calendar lỗi: {e}")

        if lich_sheet_id and len(lich_sheet_id) > 10:
            try:
                row = to_sheets_row(info)
                sheets.spreadsheets().values().append(
                    spreadsheetId=lich_sheet_id, range='A:I',
                    valueInputOption='USER_ENTERED',
                    body={'values': [row]}
                ).execute()
                sheets_ok += 1
                print(f"   ✅ Sheets (lịch công tác): đã thêm dòng")
            except Exception as e:
                print(f"   ⚠️ Sheets lỗi: {e}")

        if task_sheet_id and len(task_sheet_id) > 10 and info["content"]:
            try:
                now = date.today()
                tp_str = "; ".join(info["thanh_phan"][:3]) if info["thanh_phan"] else ""
                dvcb = info.get("don_vi_chuan_bi", "")
                phoi_hop = "; ".join(filter(None, [tp_str, dvcb]))
                task_row = [
                    "", info["content"], info["so_hieu"] or os.path.splitext(info["file"])[0],
                    now.strftime("%d/%m/%Y"), "", info["chu_tri"],
                    phoi_hop,
                    "", "", "🟢 Đang thực hiện", "", ""
                ]
                sheets.spreadsheets().values().append(
                    spreadsheetId=task_sheet_id, range='A:L',
                    valueInputOption='USER_ENTERED',
                    body={'values': [task_row]}
                ).execute()
                print(f"   ✅ Sheets (theo dõi nhiệm vụ): đã thêm nhiệm vụ")
            except Exception as e:
                print(f"   ⚠️ Task sheet lỗi: {e}")

    print(f"\n✅ Hoàn tất: {calendar_ok} sự kiện Calendar, {sheets_ok} dòng Sheets")


if __name__ == "__main__":
    run()
