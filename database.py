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
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.execute(f'CREATE TABLE IF NOT EXISTS medications ({MEDICATION_COLUMNS})')
        db.commit()
