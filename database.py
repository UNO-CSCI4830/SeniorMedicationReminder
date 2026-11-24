"""SQLite connections and schema for the medication dashboard."""
import sqlite3
from pathlib import Path
from flask import current_app, g


MEDICATION_COLUMNS = '''
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    dose_amount TEXT NOT NULL,
    reminder_day TEXT NOT NULL,
    reminder_time TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'upcoming'
        CHECK (status IN ('upcoming', 'taken', 'missed')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    scheduled_at INTEGER,
    reminder_timezone TEXT,
    reminder_frequency TEXT NOT NULL DEFAULT 'once',
    user_id INTEGER REFERENCES users(id)
'''


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON') # Enables foreign key enforcement for each database connection
    return g.db


def close_db(error=None):
    connection = g.pop('db', None)
    if connection is not None:
        connection.close()


def init_db(app):
    Path(app.config['DATABASE']).parent.mkdir(parents=True, exist_ok=True)
    app.teardown_appcontext(close_db)
    with app.app_context():
        db = get_db()
        db.execute('BEGIN IMMEDIATE')
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                phone TEXT UNIQUE,
                guardian_email TEXT COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        columns = [row["name"] for row in db.execute("PRAGMA table_info(users)")]
        if "phone" not in columns:
            db.execute("ALTER TABLE users ADD COLUMN phone TEXT")
            db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_phone ON users(phone)")
        if "guardian_email" not in columns:
            db.execute("ALTER TABLE users ADD COLUMN guardian_email TEXT COLLATE NOCASE")
        db.execute(f'CREATE TABLE IF NOT EXISTS medications ({MEDICATION_COLUMNS})')
        db.execute('''
            CREATE TABLE IF NOT EXISTS medication_history (
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                medication_id INTEGER NOT NULL,
                scheduled_at INTEGER NOT NULL,
                reminder_timezone TEXT NOT NULL,
                name TEXT NOT NULL,
                dose_amount TEXT NOT NULL,
                taken INTEGER NOT NULL,
                recorded_at INTEGER,
                PRIMARY KEY (user_id, medication_id, scheduled_at)
            )
        ''')
        db.execute('''
            CREATE INDEX IF NOT EXISTS idx_medication_history_date
            ON medication_history (user_id, scheduled_at)
        ''')
        db.commit()
