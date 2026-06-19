@echo off
chcp 65001 >nul
title UBND Bà Rịa - Hệ thống tự động hóa

echo ====================================
echo  UBND Phường Bà Rịa
echo  Hệ thống tự động hóa nghiệp vụ
echo ====================================
echo.

:: Kiểm tra Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python chưa được cài đặt!
    echo     Tải tại: https://python.org
    pause
    exit /b 1
)

:: Cài đặt dependencies
echo [*] Đang cài đặt thư viện...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [!] Lỗi cài đặt thư viện
    pause
    exit /b 1
)

:: Kiểm tra file .env
if not exist scripts\.env (
    echo [!] Chưa có file scripts/.env
    echo     Tạo từ scripts/.env.example hoặc liên hệ quản trị
    pause
    exit /b 1
)

:: Kiểm tra token
if not exist scripts\token.json (
    echo [*] Chưa có token Google OAuth
    echo     Đang mở trình duyệt để xác thực...
    python scripts/auth_init.py
)

:: Khởi động
echo.
echo [*] Khởi động Web App...
echo     Mở trình duyệt: http://localhost:5000
echo     Nhấn Ctrl+C để dừng
echo.
python webapp.py
pause
