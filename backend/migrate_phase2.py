"""
SmartBank Phase 2 — Database Migration Script
Run this ONCE on your existing banking.db to add Phase 2 tables and columns.

Usage:
    python migrate_phase2.py
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'banking.db')

if not os.path.exists(db_path):
    print(f"ERROR: Database not found at {db_path}")
    print("Make sure you have run the app at least once to create the database.")
    exit(1)

conn = sqlite3.connect(db_path)
cur  = conn.cursor()

migrations = [
    ('Add is_verified to users',
     'ALTER TABLE users ADD COLUMN is_verified INTEGER NOT NULL DEFAULT 0'),
    ('Add verification_token to users',
     'ALTER TABLE users ADD COLUMN verification_token TEXT'),
    ('Create password_reset_tokens table', '''
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            token TEXT UNIQUE NOT NULL,
            expires_at DATETIME NOT NULL,
            used INTEGER NOT NULL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )'''),
    ('Create audit_logs table', '''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )'''),
]

print("SmartBank Phase 2 — Running migrations...\n")
for name, sql in migrations:
    try:
        cur.execute(sql)
        print(f"  ✓ {name}")
    except sqlite3.OperationalError as e:
        print(f"  - {name} (skipped: {e})")

# Mark all existing users as verified (they registered before email verification existed)
cur.execute('UPDATE users SET is_verified = 1 WHERE is_verified = 0')
updated = cur.rowcount
if updated:
    print(f"\n  ✓ Marked {updated} existing user(s) as verified (pre-Phase 2 accounts)")

conn.commit()
conn.close()
print("\nMigration complete! You can now run: python app.py\n")
