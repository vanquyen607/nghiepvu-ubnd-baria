---
name: openclaw-ubnd-baria
description: |
  Skill tự động hóa nghiệp vụ hành chính UBND phường Bà Rịa:
  - Đọc PDF giấy mời/công văn → trích xuất thời gian, địa điểm, nội dung
  - Tạo lịch Google Calendar từ giấy mời
  - Theo dõi nhiệm vụ trên Google Sheets
  - Tạo lịch công tác tuần trên Google Sheets
  - Soạn thảo Thông báo kết luận cuộc họp
compatibility: OpenClaw >=0.4, Python >=3.10, Google Workspace APIs
---

# Skill — UBND Phường Bà Rịa

## Tổng quan

Skill triển khai **4 agent AI** tự động hóa nghiệp vụ hành chính của UBND phường Bà Rịa.

### Cấu trúc thư mục

```
nghiepvu-ubnd-baria/
├── SKILL.md                    ← File này
├── .env                        ← Cấu hình API (Google Calendar, Sheets)
├── .env.example                ← Mẫu cấu hình
├── client_secret.json          ← Google OAuth Client
├── token.json                  ← Token xác thực Google
├── nghiep_vu.md                ← Chi tiết nghiệp vụ & flow từng agent
├── scripts/
│   ├── auth_init.py            ← Khởi tạo Google OAuth
│   ├── trich_xuat_pdf.py       ← Script trích xuất PDF (hoạt động standalone)
│   ├── create_sheets.py        ← Tạo Google Sheets mẫu
│   ├── run_all.py              ← Chạy tất cả agents
│   └── setup.py                ← Cài đặt dependencies
├── agents/
│   ├── agent_calendar.py       ← Agent 1: PDF → Google Calendar
│   ├── agent_task_tracker.py   ← Agent 2: Theo dõi nhiệm vụ
│   ├── agent_ket_luan.py       ← Agent 3: Thông báo kết luận
│   └── agent_lich_cong_tac.py  ← Agent 4: Lịch công tác tuần
├── templates/                  ← Mẫu văn bản hành chính
├── output/                     ← Kết quả đầu ra
│   ├── ket_luan/               ← Thông báo kết luận
│   └── lich_cong_tac/          ← Lịch công tác tuần
└── logs/                       ← Nhật ký vận hành
```

### 4 Nghiệp vụ chính

| # | Agent | Input | Output |
|---|-------|-------|--------|
| 1 | **Trích xuất PDF + Calendar** | PDF giấy mời, công văn | Sự kiện Google Calendar |
| 2 | **Theo dõi nhiệm vụ** | Văn bản chỉ đạo, kết luận họp | Google Sheets + cảnh báo |
| 3 | **Thông báo kết luận** | Biên bản, ghi chép | File Word/PDF thông báo |
| 4 | **Lịch công tác tuần** | Giấy mời, lịch họp đa nguồn | Google Sheets lịch tuần |

---

## Bước cài đặt

### 1. Cài dependencies

```bash
pip install pdfplumber google-auth google-auth-oauthlib google-api-python-client python-dotenv python-docx
```

Hoặc chạy script setup:

```bash
python scripts/setup.py
```

### 2. Cấu hình Google API

#### a. Tạo Google Cloud Project
1. Vào [Google Cloud Console](https://console.cloud.google.com/)
2. Tạo project mới (VD: "UBND Automation")
3. Bật APIs: Calendar API, Sheets API, Drive API

#### b. Tạo OAuth Client ID
1. **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth client ID**
2. Application type: **Web application**
3. Authorized redirect URIs: thêm `http://localhost:3000/`
4. Tải file JSON về → đặt tên `client_secret.json` trong thư mục scripts/

#### c. Thêm người dùng thử nghiệm
1. **APIs & Services** → **OAuth consent screen**
2. Thêm email `vanquyen607@gmail.com` vào **Test users**

#### d. Cấu hình `.env`
Copy `.env.example` → `.env` và điền:

```
GOOGLE_CREDENTIALS_PATH=scripts/client_secret.json
GOOGLE_CALENDAR_ID=primary
GOOGLE_SHEET_TASK_ID=<sau khi chạy create_sheets.py>
GOOGLE_SHEET_LICH_ID=<sau khi chạy create_sheets.py>
NOTIFICATION_EMAIL=vanphongbaria@gmail.com
```

### 3. Khởi tạo xác thực Google

```bash
python scripts/auth_init.py
```

- Trình duyệt sẽ mở → đăng nhập Google → Allow
- File `token.json` sẽ được tạo

### 4. Tạo Google Sheets

```bash
python scripts/create_sheets.py
```

Tự động tạo 2 sheets:
- **Theo dõi nhiệm vụ UBND Bà Rịa** (12 cột: STT, nội dung, số VB, hạn, chủ trì, trạng thái...)
- **Lịch công tác tuần UBND Bà Rịa** (9 cột: Thứ/ngày, giờ, nội dung, lãnh đạo, địa điểm...)

### 5. Chạy toàn bộ

```bash
python scripts/run_all.py
```

---

## Nghiệp vụ 1: Đọc PDF + Tạo lịch Calendar

### Mô tả
Tự động đọc PDF giấy mời/công văn, trích xuất thông tin và tạo sự kiện Google Calendar.

### Dữ liệu đầu vào
- File PDF (giấy mời, công văn)
- Định dạng hỗ trợ: .pdf, .docx, .jpg, .png

### Thông tin trích xuất
- Tên cuộc họp / nội dung
- Thời gian bắt đầu – kết thúc
- Địa điểm
- Đơn vị tổ chức / mời
- Thành phần tham dự
- Người chủ trì

### Cách chạy

```bash
# Đọc tất cả PDF trong thư mục
python scripts/trich_xuat_pdf.py

# Tạo lịch Calendar từ PDF
python scripts/run_all.py
```

### Flow xử lý
```
PDF → pdfplumber.extract_text() → AI phân tích → Tạo Google Calendar event
```

---

## Nghiệp vụ 2: Theo dõi nhiệm vụ

### Mô tả
Tự động tổng hợp nhiệm vụ từ văn bản chỉ đạo, cập nhật Google Sheets, cảnh báo sắp/quá hạn.

### Cấu trúc Google Sheet "Theo dõi nhiệm vụ"

| Cột | Nội dung |
|-----|----------|
| A | STT |
| B | Nội dung nhiệm vụ |
| C | Số/ký hiệu văn bản |
| D | Ngày ban hành |
| E | Thời hạn hoàn thành |
| F | Chủ trì thực hiện |
| G | Đơn vị phối hợp |
| H | Lãnh đạo phụ trách |
| I | Tiến độ (%) |
| J | Trạng thái |
| K | Kết quả xử lý |
| L | Ghi chú |

### Logic trạng thái
- ✅ Hoàn thành
- 🟢 Đang thực hiện (còn hạn)
- 🟡 Sắp đến hạn (≤ 3 ngày)
- 🔴 Quá hạn

---

## Nghiệp vụ 3: Thông báo kết luận

### Mô tả
Tự động soạn thảo Thông báo kết luận cuộc họp theo thể thức văn bản hành chính UBND.

### Cách chạy

```bash
python scripts/agent_ket_luan.py --input bien_ban.pdf --audio ghi_am.mp3
```

### Cấu trúc Thông báo kết luận
```
UBND PHƯỜNG BÀ RỊA
THÔNG BÁO KẾT LUẬN

I. THÔNG TIN CUỘC HỌP
II. NỘI DUNG BÁO CÁO
III. Ý KIẾN CHỈ ĐẠO VÀ KẾT LUẬN
IV. NHIỆM VỤ ĐƯỢC GIAO
```

---

## Nghiệp vụ 4: Lịch công tác tuần

### Mô tả
Tổng hợp giấy mời, lịch họp từ nhiều nguồn → tạo bảng lịch công tác tuần trên Google Sheet.

### Cấu trúc Google Sheet

| Cột | Nội dung |
|-----|----------|
| A | Thứ / Ngày |
| B | Thời gian |
| C | Nội dung công việc |
| D | Lãnh đạo chủ trì |
| E | Cơ quan chuẩn bị |
| F | Thành phần tham dự |
| G | CB VP phụ trách |
| H | Địa điểm |
| I | Ghi chú |

### Quy tắc sắp xếp
- Thứ 2 → Thứ 6
- Sáng (07:00–11:30) → Chiều (13:30–17:00)
- Cùng buổi: giờ bắt đầu tăng dần

---

## Trích xuất PDF standalone

Script `scripts/trich_xuat_pdf.py` có thể chạy độc lập:

```bash
python scripts/trich_xuat_pdf.py
```

- Đọc tất cả file `.pdf` trong thư mục scripts/
- Trích xuất: cơ quan, số hiệu, ngày tháng, thời gian, địa điểm, thành phần
- Xuất kết quả ra `ket_qua_trich_xuat.json`

---

## Xử lý lỗi

- **Thiếu thông tin**: Hỏi lại user thay vì tự suy đoán
- **Trùng lịch**: Kiểm tra conflict trước khi tạo sự kiện
- **Lỗi Google API**: Kiểm tra token.json, chạy lại auth_init.py
- **Cổng bị chiếm**: Đổi port trong auth_init.py (mặc định 3000)

---

## Liên quan

- Chi tiết nghiệp vụ: [nghiep_vu.md](./nghiep_vu.md)
