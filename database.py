"""SQLite connections and schema for the medication dashboard."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from flask import current_app, g


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
        get_db().execute('''
            CREATE TABLE IF NOT EXISTS medications (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                dosage TEXT NOT NULL,
                pills_per_day INTEGER NOT NULL CHECK (pills_per_day > 0),
                reminder_day TEXT NOT NULL,
                reminder_time TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'upcoming'
                    CHECK (status IN ('upcoming', 'taken', 'missed')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Add scheduling fields without deleting existing medications or statuses.
        columns = {row['name'] for row in get_db().execute('PRAGMA table_info(medications)')}
        if 'scheduled_at' not in columns:
            get_db().execute('ALTER TABLE medications ADD COLUMN scheduled_at INTEGER')
        if 'reminder_timezone' not in columns:
            get_db().execute('ALTER TABLE medications ADD COLUMN reminder_timezone TEXT')
        from scheduling import next_due
        for row in get_db().execute('SELECT * FROM medications WHERE scheduled_at IS NULL').fetchall():
            zone = app.config['REMINDER_TIMEZONE']
            created = datetime.fromisoformat(row['created_at']).replace(tzinfo=timezone.utc)
            due = next_due(row['reminder_day'], row['reminder_time'], zone, created)
            get_db().execute('UPDATE medications SET scheduled_at = ?, reminder_timezone = ? WHERE id = ?', (due, zone, row['id']))
        get_db().commit()
