import re
from calendar import Calendar
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request, url_for
from database import get_db
from scheduling import medication_states, next_due

main = Blueprint('main', __name__)
DAYS = {'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'}


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
    requested_month = request.args.get('month', today.strftime('%Y-%m'))
    try:
        month = datetime.strptime(requested_month, '%Y-%m').date()
    except ValueError:
        abort(400, description='Choose a valid calendar month.')
    if not 2 <= month.year <= 9998:
        abort(400, description='Choose a valid calendar year.')
    previous_month = (month - timedelta(days=1)).strftime('%Y-%m')
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
    for items in reminders.values():
        items.sort(key=lambda item: (item['reminder_time'], item['name'].casefold()))
    return render_template('schedule.html', month=month, today=today,
                           weeks=Calendar(firstweekday=6).monthdatescalendar(month.year, month.month),
                           previous_month=previous_month, next_month=next_month.strftime('%Y-%m'),
                           reminders=reminders)


@main.get('/api/medications/statuses')
def medication_statuses():
    response = jsonify([{'id': item['id'], 'status': item['status'], 'late_label': item['late_label'], 'scheduled_at': item['scheduled_at']} for item in medication_states()])
    response.headers['Cache-Control'] = 'no-store'
    return response


@main.post('/api/medications')
def add_medication():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='Please submit medication details as JSON.'), 400
    fields = {}
    for field, label, limit in [('name', 'Medication name', 200), ('dosage', 'Dosage', 100)]:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
            return jsonify(error=f'{label} is required and must be at most {limit} characters.'), 400
        fields[field] = value.strip()
    pills = data.get('pills_per_day')
    if not isinstance(pills, (str, int)) or isinstance(pills, bool) or not re.fullmatch(r'[1-9][0-9]{0,2}', str(pills)):
        return jsonify(error='Enter a whole number of pills from 1 to 999.'), 400
    frequency = data.get('reminder_frequency', 'once')
    if frequency not in ('once', 'daily', 'weekly'):
        return jsonify(error='Choose a valid reminder frequency.'), 400
    day = data.get('reminder_day')
    if not isinstance(day, str) or day not in DAYS:
        return jsonify(error='Choose a valid day of the week.'), 400
    time = data.get('reminder_time')
    if not isinstance(time, str) or not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', time):
        return jsonify(error='Enter a valid reminder time.'), 400
    zone = data.get('reminder_timezone', current_app.config['REMINDER_TIMEZONE'])
    try:
        if not isinstance(zone, str):
            raise ValueError()
        ZoneInfo(zone)
    except (ZoneInfoNotFoundError, ValueError):
        return jsonify(error='Choose a valid reminder timezone.'), 400
    due = next_due(day, time, zone, datetime.now(timezone.utc))
    db = get_db()
    cursor = db.execute(
        'INSERT INTO medications (name, dosage, pills_per_day, reminder_day, reminder_time, scheduled_at, reminder_timezone, reminder_frequency) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (fields['name'], fields['dosage'], int(pills), day, time, due, zone, frequency),
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
