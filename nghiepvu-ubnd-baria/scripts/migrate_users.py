#!/usr/bin/env python3
"""
Migrate users from users.json to SQLite database.
Run this ONCE after switching to SQLAlchemy.

Usage: python scripts/migrate_users.py
"""
import os
import sys
import json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from webapp import app, db
from models import User

USERS_JSON = os.path.join(BASE, 'scripts', 'users.json')
DEFAULT_PASSWORD = 'ubnd@2024'


def migrate():
    if not os.path.exists(USERS_JSON):
        print("⚠️  Không tìm thấy scripts/users.json")
        return

    with open(USERS_JSON, 'r', encoding='utf-8') as f:
        users_data = json.load(f)

    if not users_data:
        print("⚠️  users.json trống")
        return

    with app.app_context():
        db.create_all()
        count = 0
        skipped = 0

        for email, info in users_data.items():
            if User.query.filter_by(email=email).first():
                print(f"  ⏭️  {email} - đã tồn tại, bỏ qua")
                skipped += 1
                continue

            user = User(email=email, fullname=info.get('fullname', email))
            user.set_password(DEFAULT_PASSWORD)
            db.session.add(user)
            count += 1
            print(f"  ✅ {email} - {info.get('fullname', '')}")

        db.session.commit()

        print(f"\n{'='*50}")
        print(f"📋 Migrated: {count} users")
        if skipped:
            print(f"⏭️  Skipped: {skipped} users (already exist)")
        print(f"🔑 Default password: {DEFAULT_PASSWORD}")
        print(f"⚠️  Change passwords after first login via Settings!")
        print(f"{'='*50}")


if __name__ == '__main__':
    migrate()
