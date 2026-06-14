"""
SmartBank Phase 3 — Database Migration Script
Run this ONCE on your existing banking.db to add the notifications table.

Usage:
    python migrate_phase3.py
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
    ('Create notifications table', '''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'info',
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )'''),
]

print("SmartBank Phase 3 — Running migrations...\n")
for name, sql in migrations:
    try:
        cur.execute(sql)
        print(f"  ✓ {name}")
    except sqlite3.OperationalError as e:
        print(f"  - {name} (skipped: {e})")

conn.commit()
conn.close()
print("\nMigration complete! You can now run: python app.py\n")
print("New features available:")
print("  • QR Transfer — visit /profile to see your QR code")
print("  • Notifications — bell icon in the top bar, or visit /notifications")
print("  • Advanced Analytics — visit /admin/ for the upgraded dashboard\n")
