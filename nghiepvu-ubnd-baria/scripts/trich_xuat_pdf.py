"""
Trích xuất PDF: Đọc file PDF giấy mời/công văn → trích xuất thông tin cấu trúc
Yêu cầu: pip install pdfplumber
Chạy: python scripts/trich_xuat_pdf.py
"""
import pdfplumber
import json
import glob
import os
import sys
import re
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def extract_text(pdf_path):
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                pages.append(t)
    return "\n".join(pages)


def parse_van_ban(text, filename):
    info = {
        "file": filename,
        "loai": "",
        "co_quan": "",
        "so_hieu": "",
        "ngay_thang": "",
        "noi_dung": "",
        "thoi_gian_hop": "",
        "dia_diem": "",
        "chu_tri": "",
        "thanh_phan": [],
        "yeu_cau": [],
    }
    lines = text.split("\n")

    # Loại văn bản
    u = text.upper()
    if "GIẤY MỜI" in u:
        info["loai"] = "Giấy mời"
    elif "CÔNG VĂN" in u:
        info["loai"] = "Công văn"
    elif "THÔNG BÁO" in u:
        info["loai"] = "Thông báo"
    else:
        info["loai"] = "Khác"

    # Cơ quan
    for line in lines[:6]:
        line = line.strip()
        if any(kw in line for kw in ["ỦY BAN NHÂN DÂN", "SỞ ", "PHÒNG", "CỤC", "THÀNH PHỐ"]):
            info["co_quan"] = line
            break

    # Số hiệu
    for line in lines:
        if re.search(r"^số\s*:", line, re.IGNORECASE):
            info["so_hieu"] = line.strip()
            break

    # Ngày tháng
    for line in lines[:15]:
        m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", line)
        if m:
            info["ngay_thang"] = f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
            break
        m2 = re.search(r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})", line, re.IGNORECASE)
        if m2:
            info["ngay_thang"] = f"{m2.group(1)}/{m2.group(2)}/{m2.group(3)}"
            break

    # Thời gian họp
    for line in lines:
        if any(kw in line.lower() for kw in ["thời gian", "vào lúc", "lúc "]):
            info["thoi_gian_hop"] = line.strip()
            break

    # Địa điểm
    for line in lines:
        if "địa điểm" in line.lower() or line.strip().startswith("Địa"):
            info["dia_diem"] = line.strip()
            break

    # Chủ trì
    for line in lines:
        if "chủ trì" in line.lower() or any(kw in line for kw in ["Phó Giám đốc", "Giám đốc", "Phó Trưởng phòng", "Trưởng phòng"]):
            info["chu_tri"] = line.strip()
            break

    # Nội dung
    for line in lines:
        if "Về nội dung" in line or "Về việc" in line:
            info["noi_dung"] = line.strip()
            break

    # Thành phần
    in_tp = False
    for line in lines:
        ls = line.strip()
        if any(kw in ls.lower() for kw in ["kính mời", "tham dự", "thành phần"]):
            in_tp = True
            continue
        if in_tp:
            if ls.startswith("-") or ls.startswith("•"):
                info["thanh_phan"].append(ls.lstrip("-• "))
            elif any(kw in ls.lower() for kw in ["chủ trì", "địa điểm", "thời gian", "chuẩn bị", "trân trọng", "vì tính"]):
                break

    return info


def run():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    pdfs = glob.glob("*.pdf")

    print("=" * 55)
    print("  📄 UBND Bà Rịa — Trích xuất PDF")
    print("=" * 55)

    if not pdfs:
        print("⚠️ Không tìm thấy file PDF nào!")
        return

    results = []
    for pdf in pdfs:
        print(f"\n📄 {pdf}")
        try:
            text = extract_text(pdf)
            info = parse_van_ban(text, pdf)
            results.append(info)
            print(f"  ✅ Loại: {info['loai']}")
            print(f"  🏢 Cơ quan: {info['co_quan']}")
            print(f"  📅 Ngày: {info['ngay_thang']}")
            print(f"  🕐 Thời gian: {info['thoi_gian_hop']}")
            print(f"  📍 Địa điểm: {info['dia_diem']}")
        except Exception as e:
            print(f"  ❌ Lỗi: {e}")

    # Lưu JSON
    out = "ket_qua_trich_xuat.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Đã lưu: {out}")


if __name__ == "__main__":
    run()