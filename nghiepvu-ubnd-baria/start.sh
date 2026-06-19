#!/usr/bin/env bash
set -e

echo "===================================="
echo " UBND Phường Bà Rịa"
echo " Hệ thống tự động hóa nghiệp vụ"
echo "===================================="

# Kiểm tra Python
command -v python3 >/dev/null 2>&1 || { echo "[!] Chưa cài Python"; exit 1; }

# Cài đặt dependencies
pip install -r requirements.txt -q

# Kiểm tra .env
[ -f scripts/.env ] || { echo "[!] Thiếu scripts/.env"; exit 1; }

# Kiểm tra token
[ -f scripts/token.json ] || python3 scripts/auth_console.py

# Khởi động
echo ""
echo "[*] Web App: http://localhost:5000"
echo "    Nhấn Ctrl+C để dừng"
python3 webapp.py
