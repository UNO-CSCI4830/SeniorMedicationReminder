"""One scheduled occurrence per medication, with a persisted UTC due time."""
from datetime import datetime, timedelta, timezone
import time
from zoneinfo import ZoneInfo

from database import get_db

DAYS = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')


def next_due(day, clock, timezone_name, created_at):
    zone = ZoneInfo(timezone_name)
    local = created_at.astimezone(zone)
    hour, minute = map(int, clock.split(':'))
    date = local.date() + timedelta(days=(DAYS.index(day) - local.weekday()) % 7)
    due = datetime(date.year, date.month, date.day, hour, minute, tzinfo=zone)
    # Resolve nonexistent spring-forward times by normalizing through UTC.
    due = due.astimezone(timezone.utc).astimezone(zone)
    if due.timestamp() < created_at.timestamp():
        date += timedelta(days=7)
        due = datetime(date.year, date.month, date.day, hour, minute, tzinfo=zone)
    return int(due.timestamp())


def overdue_text(seconds):
    if seconds < 60:
        return 'Due less than a minute ago'
    if seconds < 3600:
        amount, unit = int(seconds // 60), 'minute'
    elif seconds < 86400:
        amount, unit = int(seconds // 3600), 'hour'
    else:
        amount, unit = int(seconds // 86400), 'day'
    return f'Due {amount} {unit}{"s" if amount != 1 else ""} ago'


def medication_states():
    now = time.time()
    db = get_db()
    db.execute("UPDATE medications SET status = 'missed' WHERE status = 'upcoming' AND scheduled_at <= ?", (now,))
    db.commit()
    medications = []
    for row in db.execute('SELECT * FROM medications ORDER BY id DESC').fetchall():
        medication = dict(row)
        local = datetime.fromtimestamp(row['scheduled_at'], ZoneInfo(row['reminder_timezone']))
        medication['scheduled_time'] = local.strftime('%I:%M %p').lstrip('0')
        medication['scheduled_iso'] = local.isoformat()
        medication['scheduled_label'] = local.strftime('%a, %b %d at ') + medication['scheduled_time'] + local.strftime(' %Z')
        medication['late_label'] = overdue_text(max(0, now - row['scheduled_at'])) if row['status'] == 'missed' else ''
        medications.append(medication)
    return medications
