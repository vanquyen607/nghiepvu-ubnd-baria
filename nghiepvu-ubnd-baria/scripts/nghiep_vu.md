# Chi tiết Nghiệp vụ — UBND Phường Bà Rịa

## Nghiệp vụ 1: Trích xuất PDF + Tạo lịch Google Calendar

### Mô tả
Tự động đọc PDF giấy mời/công văn, trích xuất thông tin (thời gian, địa điểm, nội dung) và tạo sự kiện trên Google Calendar.

### Dữ liệu đầu vào
- File PDF (giấy mời, công văn, thông báo)
- Hỗ trợ: .pdf, .docx, .jpg, .png (OCR)

### Thông tin trích xuất
- Tên cuộc họp / nội dung
- Thời gian bắt đầu – kết thúc
- Địa điểm tổ chức
- Đơn vị tổ chức / mời
- Thành phần tham dự
- Người chủ trì

### Flow
```
PDF → pdfplumber → AI phân tích → Tạo Google Calendar event
```

### Cách chạy
```bash
# Trích xuất PDF (standalone)
python scripts/trich_xuat_pdf.py

# Chạy agent calendar
python scripts/run_all.py
```

---

## Nghiệp vụ 2: Theo dõi nhiệm vụ

### Mô tả
Tự động tổng hợp, theo dõi và quản lý nhiệm vụ được giao trên Google Sheets.

### Cấu trúc Google Sheet (12 cột)
| A | B | C | D | E | F | G | H | I | J | K | L |
|---|---|---|---|---|---|---|---|---|---|---|---|
| STT | Nội dung | Số VB | Ngày BH | Hạn | Chủ trì | Phối hợp | Lãnh đạo | Tiến độ | Trạng thái | Kết quả | Ghi chú |

### Logic trạng thái tự động
- `✅ Hoàn thành` — đã xong
- `🟢 Đang thực hiện` — còn hạn
- `🟡 Sắp đến hạn` — ≤ 3 ngày
- `🔴 Quá hạn` — hết hạn

---

## Nghiệp vụ 3: Thông báo kết luận

### Mô tả
Soạn thảo Thông báo kết luận cuộc họp theo thể thức hành chính UBND.

### Cách chạy
```bash
python scripts/agent_ket_luan.py --input bien_ban.pdf --audio ghi_am.mp3
```

### Cấu trúc văn bản
```
UBND PHƯỜNG BÀ RỊA
THÔNG BÁO KẾT LUẬN

I. Thông tin cuộc họp
II. Nội dung báo cáo
III. Ý kiến chỉ đạo và kết luận
IV. Nhiệm vụ được giao (stt, nội dung, chủ trì, hạn)
```

---

## Nghiệp vụ 4: Lịch công tác tuần

### Mô tả
Tổng hợp lịch họp từ nhiều nguồn → tạo lịch công tác tuần trên Google Sheet.

### Cấu trúc (9 cột)
Thứ/Ngày | Thời gian | Nội dung | Lãnh đạo | Cơ quan | Thành phần | CB VP | Địa điểm | Ghi chú

### Quy tắc sắp xếp
- Thứ 2 → Thứ 6 (hoặc Thứ 7)
- Sáng (07:00–11:30) → Chiều (13:30–17:00)
- Giờ bắt đầu tăng dần

---

## Cài đặt nhanh

```bash
# 1. Cài dependencies
pip install pdfplumber google-auth google-auth-oauthlib google-api-python-client python-dotenv

# 2. Cấu hình .env (xem .env.example)

# 3. Xác thực Google
python scripts/auth_init.py

# 4. Tạo Google Sheets
python scripts/create_sheets.py

# 5. Chạy toàn bộ
python scripts/run_all.py
```

## Khắc phục lỗi

| Lỗi | Giải pháp |
|-----|-----------|
| `Error 400: redirect_uri_mismatch` | Thêm `http://localhost:3000/` vào Google Cloud Console → Credentials → Redirect URIs |
| `Error 403: access_denied` | Thêm email vào Test users trong OAuth consent screen |
| `Error 10048: port` | Đổi cổng trong `auth_init.py` (VD: 3000 → 5000) |
| Token hết hạn | Xóa `token.json`, chạy lại `auth_init.py` |