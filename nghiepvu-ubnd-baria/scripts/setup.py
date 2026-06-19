"""
Setup: Cài đặt dependencies cho UBND Bà Rịa Skill
"""
import subprocess
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REQUIREMENTS = [
    "pdfplumber",
    "google-auth>=2.0",
    "google-auth-oauthlib>=1.0",
    "google-api-python-client>=2.0",
    "python-dotenv>=1.0",
    "python-docx>=1.0",
]

def install():
    print("📦 UBND Bà Rịa — Setup")
    print("=" * 45)
    for pkg in REQUIREMENTS:
        print(f"  → {pkg}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])
    print("\n✅ Dependencies đã cài đặt!")

if __name__ == "__main__":
    install()
    print("\nTiếp theo:")
    print("  1. python scripts/auth_init.py")
    print("  2. python scripts/create_sheets.py")
    print("  3. python scripts/run_all.py")