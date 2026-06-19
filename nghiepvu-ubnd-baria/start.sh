#!/usr/bin/env bash
set -e

echo "===================================="
echo " UBND Phường Bà Rịa - Render"
echo " Khởi động Web App..."
echo "===================================="

DATA_DIR="${DATA_DIR:-/data}"
echo "[*] DATA_DIR: $DATA_DIR"

# Create persistent directories
mkdir -p "$DATA_DIR/config" \
         "$DATA_DIR/instance" \
         "$DATA_DIR/uploads" \
         "$DATA_DIR/output" \
         "$DATA_DIR/logs" \
         "$DATA_DIR/scripts"

# Write Google credentials from Render env vars
if [ -n "$GOOGLE_CLIENT_SECRET_BASE64" ]; then
    echo "$GOOGLE_CLIENT_SECRET_BASE64" | base64 -d > "$DATA_DIR/config/client_secret.json" 2>/dev/null
    echo "[*] Written client_secret.json"
fi
if [ -n "$GOOGLE_TOKEN_BASE64" ]; then
    echo "$GOOGLE_TOKEN_BASE64" | base64 -d > "$DATA_DIR/config/token.json" 2>/dev/null
    echo "[*] Written token.json"
fi

# Ensure symlinks for backward compatibility
ln -sfn "$DATA_DIR/instance" instance
ln -sfn "$DATA_DIR/output" output
ln -sfn "$DATA_DIR/logs" logs
ln -sfn "$DATA_DIR/uploads" uploads

# Symlink credentials into scripts/ so agents can find them
touch "$DATA_DIR/config/token.json" "$DATA_DIR/config/client_secret.json"
ln -sf "$DATA_DIR/config/token.json" scripts/token.json 2>/dev/null || true
ln -sf "$DATA_DIR/config/client_secret.json" scripts/client_secret.json 2>/dev/null || true

echo "===================================="
echo "🚀 Starting gunicorn on port ${PORT:-5000}"
echo "===================================="

exec gunicorn webapp:app -c gunicorn.conf.py
