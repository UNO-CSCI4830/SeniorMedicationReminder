"""SQLite connections and schema for the medication dashboard."""
import sqlite3
from datetime import datetime, timezone
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
    reminder_frequency TEXT NOT NULL DEFAULT 'once'
'''


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
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
        db.execute(f'CREATE TABLE IF NOT EXISTS medications ({MEDICATION_COLUMNS})')
        # Add scheduling fields without deleting existing medications or statuses.
        columns = {row['name'] for row in db.execute('PRAGMA table_info(medications)')}
        if 'scheduled_at' not in columns:
            db.execute('ALTER TABLE medications ADD COLUMN scheduled_at INTEGER')
        if 'reminder_timezone' not in columns:
            db.execute('ALTER TABLE medications ADD COLUMN reminder_timezone TEXT')
        if 'reminder_frequency' not in columns:
            db.execute("ALTER TABLE medications ADD COLUMN reminder_frequency TEXT NOT NULL DEFAULT 'once'")
        if 'pills_per_day' in columns:
            db.execute(f'CREATE TABLE medications_new ({MEDICATION_COLUMNS})')
            db.execute('''
                INSERT INTO medications_new (
                    id, name, dose_amount, reminder_day, reminder_time, status,
                    created_at, scheduled_at, reminder_timezone, reminder_frequency
                )
                SELECT id, name,
                    pills_per_day || CASE WHEN pills_per_day = 1
                        THEN ' pill (' || dosage || ')'
                        ELSE ' pills (' || dosage || ' each)' END,
                    reminder_day, reminder_time, status, created_at, scheduled_at,
                    reminder_timezone, reminder_frequency
                FROM medications
            ''')
            db.execute('DROP TABLE medications')
            db.execute('ALTER TABLE medications_new RENAME TO medications')
        from scheduling import next_due
        for row in db.execute('SELECT * FROM medications WHERE scheduled_at IS NULL').fetchall():
            zone = app.config['REMINDER_TIMEZONE']
            created = datetime.fromisoformat(row['created_at']).replace(tzinfo=timezone.utc)
            due = next_due(row['reminder_day'], row['reminder_time'], zone, created)
            db.execute('UPDATE medications SET scheduled_at = ?, reminder_timezone = ? WHERE id = ?', (due, zone, row['id']))
        db.commit()
