import re
from calendar import Calendar
from datetime import date, datetime, time, timedelta, timezone
from functools import wraps
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db
from scheduling import DAYS, medication_states, next_due

main = Blueprint('main', __name__)

# Requires users to log in before accessing protected pages
def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            return redirect(url_for("main.login"))
        return view(**kwargs)

    return wrapped_view

# Checks whether a user has a logged-in session
# Redirects visitors who aren't logged in to the login page
# Allows logged-in users to continue to the requested page
# Lets us reuse this check across multiple routes

@main.post('/medications/<int:medication_id>/delete')
@login_required
def delete_medication(medication_id):
    db = get_db()
    cursor = db.execute('DELETE FROM medications WHERE id = ? AND user_id = ?', (medication_id, session['user_id']))
    if cursor.rowcount == 0:
        abort(404)
    db.commit()
    return redirect(url_for('main.home'), code=303)


@main.route('/')
@login_required # Tells Flask to check whether someone is logged in before displaying the dashboard
def home():
    return render_template('index.html', medications=medication_states(session['user_id']))

#Registration
@main.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        first_name = request.form.get("firstname", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not first_name or not email or not password:
            return render_template("signup.html", error="Please fill in all required fields.")

        if password != confirm_password:
            return render_template("signup.html", error="Passwords do not match.")

        if len(password) < 8:
            return render_template("signup.html", error="Password must be at least 8 characters.")

        db = get_db()

        existing_user = db.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()

        if existing_user:
            return render_template("signup.html", error="An account with that email already exists.")

        password_hash = generate_password_hash(password)

        db.execute(
            "INSERT INTO users (first_name, email, password_hash) VALUES (?, ?, ?)",
            (first_name, email, password_hash)
        )
        db.commit()

        return redirect(url_for("main.login"))

    return render_template("signup.html")

# Collects the first name, email, and password
# Checks that the passwords match
# Requires a password of at least 8 characters
# Prevents duplicate email accounts
# Hashes the password before saving it
# Sends the user to the login page after successful registration


#Login
@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db()

        user = db.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            return render_template(
                "login.html",
                error="Invalid email or password."
            )

        session["user_id"] = user["id"]
        session["user_name"] = user["first_name"]

        return redirect(url_for("main.home"))

    return render_template("login.html")

# Accepts login submissions through POST
# Finds the account by email
# Checks the submitted password against the stored hash
# Saves the user's ID and first name in their session
# Redirects successful logins to the dashboard

@main.post("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("main.login"))
# Logs the user out by clearing their session and sends them back to the login page


@main.get('/schedule')
@login_required
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
    for medication in medication_states(session['user_id']):
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
@login_required
def medication_statuses():
    response = jsonify([{'id': item['id'], 'status': item['status'], 'late_label': item['late_label'], 'scheduled_at': item['scheduled_at']} for item in medication_states(session['user_id'])])
    response.headers['Cache-Control'] = 'no-store'
    return response


@main.post('/api/medications')
@main.patch('/api/medications/<int:medication_id>')
@login_required
def add_medication(medication_id=None):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='Please submit medication details as JSON.'), 400
    name = data.get('name')
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 200:
        return jsonify(error='Medication name is required and must be at most 200 characters.'), 400
    dose = data.get('dose_amount')
    if not isinstance(dose, str) or not dose.strip() or len(dose.strip()) > 200:
        return jsonify(error='Amount per reminder is required and must be at most 200 characters.'), 400
    frequency = data.get('reminder_frequency', 'once')
    if frequency not in ('once', 'daily', 'weekly'):
        return jsonify(error='Choose a valid reminder frequency.'), 400
    day = data.get('reminder_day')
    if frequency != 'daily' and day not in DAYS:
        return jsonify(error='Choose a valid day of the week.'), 400
    time = data.get('reminder_time')
    if not isinstance(time, str) or not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', time):
        return jsonify(error='Enter a valid reminder time.'), 400
    db = get_db()
    user_id = session['user_id']
    existing = None
    if medication_id is not None:
        db.execute('BEGIN IMMEDIATE')
        existing = db.execute(
            'SELECT * FROM medications WHERE id = ? AND user_id = ?', (medication_id, user_id)
        ).fetchone()
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
        db.execute('UPDATE medications SET name = ?, dose_amount = ? WHERE id = ? AND user_id = ?',
                   (name.strip(), dose.strip(), medication_id, user_id))
        db.commit()
        return jsonify(id=medication_id, status=existing['status'])

    now = datetime.now(timezone.utc)
    due = next_due(None if frequency == 'daily' else day, time, zone, now)
    if frequency == 'daily':
        day = DAYS[datetime.fromtimestamp(due, ZoneInfo(zone)).weekday()]
    values = (name.strip(), dose.strip(), day, time, due, zone, frequency)
    if existing:
        db.execute('''
            UPDATE medications
            SET name = ?, dose_amount = ?, reminder_day = ?, reminder_time = ?,
                scheduled_at = ?, reminder_timezone = ?, reminder_frequency = ?,
                status = 'upcoming', created_at = ?
            WHERE id = ? AND user_id = ?
        ''', (*values, now.strftime('%Y-%m-%d %H:%M:%S'), medication_id, user_id))
        db.commit()
        return jsonify(id=medication_id, status='upcoming')

    cursor = db.execute(
        'INSERT INTO medications (name, dose_amount, reminder_day, reminder_time, scheduled_at, '
        'reminder_timezone, reminder_frequency, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (*values, user_id),
    )
    db.commit()
    return jsonify(id=cursor.lastrowid, status='upcoming'), 201


@main.post('/medications/<int:medication_id>/status')
@login_required
def update_status(medication_id):
    status = request.form.get('status')
    if status != 'taken':
        abort(400, description='Use Mark as taken to confirm this medication.')
    db = get_db()
    cursor = db.execute('UPDATE medications SET status = ? WHERE id = ? AND user_id = ?', (status, medication_id, session['user_id']))
    if cursor.rowcount == 0:
        abort(404)
    db.commit()
    return redirect(url_for('main.home'), code=303)

#routes to profile page
@main.route("/profile")
@login_required
def profile():
    return render_template("profile.html")

#routes to account setting
@main.route("/account-settings")
@login_required
def account_settings():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)
        ).fetchone()

    msg_type = request.args.get("msg")

    return render_template("accountSetting.html", user=user, msg=msg_type)

#routes to delete account
@main.route("/delete-account", methods=["POST"])
@login_required
def delete_account():
    db = get_db()

    user_id = session["user_id"]
    db.execute("DELETE FROM medications WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()

    session.clear()

    return redirect(url_for("main.login", msg="Your account has been deleted."))

# allows user to change password
@main.route("/change-password", methods=["POST"])
@login_required
def change_password():
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not current_password or not new_password or not confirm_password:
        return render_template("accountSetting.html", error="Please fill in all required fields.")

    if current_password == new_password:
        return render_template("accountSetting.html", error="New password must be different from current password.")

    if len(new_password) < 8:
        return render_template("accountSetting.html", error="Password must be atleast 8 characters.")

    if new_password != confirm_password:
        return render_template("accountSetting.html", error="New passwords do not match.")

    db = get_db()
    user = db.execute("SELECT password_hash FROM users WHERE id = ?", (session["user_id"],)
        ).fetchone()

    if not user or not check_password_hash(user["password_hash"], current_password):
        return render_template("accountSetting.html", error="Current password is incorrect.")

    new_hash = generate_password_hash(new_password)
    db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, session["user_id"])
        )
    db.commit()

    return render_template("accountSetting.html", success="Password updated!")
