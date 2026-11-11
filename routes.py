import re
from calendar import Calendar
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request, url_for
from database import get_db
from scheduling import DAYS, medication_states, next_due

main = Blueprint('main', __name__)


@main.post('/medications/<int:medication_id>/delete')
def delete_medication(medication_id):
    db = get_db()
    cursor = db.execute('DELETE FROM medications WHERE id = ?', (medication_id,))
    if cursor.rowcount == 0:
        abort(404)
    db.commit()
    return redirect(url_for('main.home'), code=303)


@main.route('/')
def home():
    return render_template('index.html', medications=medication_states())


@main.get('/schedule')
def schedule():
    today = datetime.now(ZoneInfo(current_app.config['REMINDER_TIMEZONE'])).date()
    try:
        if 'date' in request.args:
            selected_day = date.fromisoformat(request.args['date'])
        elif 'month' in request.args:
            requested_month = datetime.strptime(request.args['month'], '%Y-%m').date()
            selected_day = today if requested_month == today.replace(day=1) else requested_month
        else:
            selected_day = today
    except ValueError:
        abort(400, description='Choose a valid calendar date or month.')
    month = selected_day.replace(day=1)
    if not 2 <= month.year <= 9998:
        abort(400, description='Choose a valid calendar year.')
    previous_month = month - timedelta(days=1)
    next_month = (month + timedelta(days=32)).replace(day=1)
    reminders = {}
    for medication in medication_states():
        zone = ZoneInfo(medication['reminder_timezone'])
        scheduled = datetime.fromtimestamp(medication['scheduled_at'], zone).date()
        frequency = medication['reminder_frequency']
        if frequency == 'once':
            dates = [scheduled]
        else:
            created = datetime.fromisoformat(medication['created_at']).replace(tzinfo=timezone.utc)
            first_due = next_due(medication['reminder_day'], medication['reminder_time'], zone.key, created)
            first_day = datetime.fromtimestamp(first_due, zone).date()
            interval = 1 if frequency == 'daily' else 7
            offset = max(0, (month - first_day).days)
            first_in_month = first_day + timedelta(days=offset + (-offset % interval))
            dates = (first_in_month + timedelta(days=days)
                     for days in range(0, (next_month - first_in_month).days, interval))
        for day in dates:
            if month <= day < next_month:
                reminders.setdefault(day, []).append(medication)
    agenda = []
    for medication in reminders.get(selected_day, []):
        zone = ZoneInfo(medication['reminder_timezone'])
        occurrence = datetime.fromtimestamp(medication['scheduled_at'], zone)
        if occurrence.date() != selected_day:
            clock = time.fromisoformat(medication['reminder_time'])
            occurrence = datetime.combine(selected_day, clock, tzinfo=zone)
            occurrence = occurrence.astimezone(timezone.utc).astimezone(zone)
        agenda.append((occurrence, medication))
    agenda.sort(key=lambda entry: (entry[0].time(), entry[1]['name'].casefold()))
    previous_day = selected_day - timedelta(days=1)
    next_day = selected_day + timedelta(days=1)
    return render_template('schedule.html', month=month, today=today,
                           weeks=Calendar(firstweekday=6).monthdatescalendar(month.year, month.month),
                           previous_month=previous_month if previous_month.year >= 2 else None,
                           next_month=next_month if next_month.year <= 9998 else None,
                           previous_day=previous_day if previous_day.year >= 2 else None,
                           next_day=next_day if next_day.year <= 9998 else None,
                           selected_day=selected_day, agenda=agenda, reminders=reminders)


@main.get('/api/medications/statuses')
def medication_statuses():
    response = jsonify([{'id': item['id'], 'status': item['status'], 'late_label': item['late_label'], 'scheduled_at': item['scheduled_at']} for item in medication_states()])
    response.headers['Cache-Control'] = 'no-store'
    return response


@main.post('/api/medications')
@main.patch('/api/medications/<int:medication_id>')
def add_medication(medication_id=None):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='Please submit medication details as JSON.'), 400
    name = data.get('name')
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 200:
        return jsonify(error='Medication name is required and must be at most 200 characters.'), 400
    dose = data.get('dose_amount')
    legacy_request = 'dose_amount' not in data and ('dosage' in data or 'pills_per_day' in data)
    if legacy_request:
        dosage = data.get('dosage')
        pills = data.get('pills_per_day')
        if not isinstance(dosage, str) or not dosage.strip() or len(dosage.strip()) > 100:
            return jsonify(error='Dosage is required and must be at most 100 characters.'), 400
        if not isinstance(pills, (str, int)) or not re.fullmatch(r'[1-9][0-9]{0,2}', str(pills)):
            return jsonify(error='Enter a whole number of pills from 1 to 999.'), 400
        dose = f'1 pill ({dosage.strip()})' if int(pills) == 1 else f'{pills} pills ({dosage.strip()} each)'
    if not isinstance(dose, str) or not dose.strip() or len(dose.strip()) > 200:
        return jsonify(error='Amount per reminder is required and must be at most 200 characters.'), 400
    frequency = data.get('reminder_frequency', 'once')
    if frequency not in ('once', 'daily', 'weekly'):
        return jsonify(error='Choose a valid reminder frequency.'), 400
    day = data.get('reminder_day')
    if (frequency != 'daily' or legacy_request) and day not in DAYS:
        return jsonify(error='Choose a valid day of the week.'), 400
    time = data.get('reminder_time')
    if not isinstance(time, str) or not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', time):
        return jsonify(error='Enter a valid reminder time.'), 400
    db = get_db()
    existing = None
    if medication_id is not None:
        db.execute('BEGIN IMMEDIATE')
        existing = db.execute('SELECT * FROM medications WHERE id = ?', (medication_id,)).fetchone()
        if existing is None:
            return jsonify(error='This medication no longer exists.'), 404
    default_zone = existing['reminder_timezone'] if existing else current_app.config['REMINDER_TIMEZONE']
    zone = data.get('reminder_timezone', default_zone)
    try:
        if not isinstance(zone, str):
            raise ValueError()
        ZoneInfo(zone)
    except (ZoneInfoNotFoundError, ValueError):
        return jsonify(error='Choose a valid reminder timezone.'), 400
    if (existing and existing['reminder_frequency'] == frequency
            and existing['reminder_time'] == time and existing['reminder_timezone'] == zone
            and (frequency == 'daily' or existing['reminder_day'] == day)):
        db.execute('UPDATE medications SET name = ?, dose_amount = ? WHERE id = ?',
                   (name.strip(), dose.strip(), medication_id))
        db.commit()
        return jsonify(id=medication_id, status=existing['status'])

    now = datetime.now(timezone.utc)
    due = next_due(None if frequency == 'daily' and not legacy_request else day, time, zone, now)
    if frequency == 'daily' and not legacy_request:
        day = DAYS[datetime.fromtimestamp(due, ZoneInfo(zone)).weekday()]
    values = (name.strip(), dose.strip(), day, time, due, zone, frequency)
    if existing:
        db.execute('''
            UPDATE medications
            SET name = ?, dose_amount = ?, reminder_day = ?, reminder_time = ?,
                scheduled_at = ?, reminder_timezone = ?, reminder_frequency = ?,
                status = 'upcoming', created_at = ?
            WHERE id = ?
        ''', (*values, now.strftime('%Y-%m-%d %H:%M:%S'), medication_id))
        db.commit()
        return jsonify(id=medication_id, status='upcoming')

    cursor = db.execute(
        'INSERT INTO medications (name, dose_amount, reminder_day, reminder_time, scheduled_at, reminder_timezone, reminder_frequency) VALUES (?, ?, ?, ?, ?, ?, ?)',
        values,
    )
    db.commit()
    return jsonify(id=cursor.lastrowid, status='upcoming'), 201


@main.post('/medications/<int:medication_id>/status')
def update_status(medication_id):
    status = request.form.get('status')
    if status != 'taken':
        abort(400, description='Use Mark as taken to confirm this medication.')
    db = get_db()
    cursor = db.execute('UPDATE medications SET status = ? WHERE id = ?', (status, medication_id))
    if cursor.rowcount == 0:
        abort(404)
    db.commit()
    return redirect(url_for('main.home'), code=303)
