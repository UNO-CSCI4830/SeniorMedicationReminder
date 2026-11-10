import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request, url_for, session
from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash #Add security imports
from scheduling import medication_states, next_due
from functools import wraps

main = Blueprint('main', __name__)
DAYS = {'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'}

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

#Drug Selection
@main.route("/drug_selection")
@login_required
def drug_selection():
    return render_template("Drug_selection.html")

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


@main.get('/api/medications/statuses')
@login_required
def medication_statuses():
    response = jsonify([{'id': item['id'], 'status': item['status'], 'late_label': item['late_label']} for item in medication_states(session['user_id'])])
    response.headers['Cache-Control'] = 'no-store'
    return response


@main.post('/api/medications')
@login_required
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
        'INSERT INTO medications (name, dosage, pills_per_day, reminder_day, reminder_time, scheduled_at, reminder_timezone, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (fields['name'], fields['dosage'], int(pills), day, time, due, zone, session['user_id']),
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

    db.execute("DELETE FROM users WHERE id =?", (session["user_id"],))
    db.commit()

    session.clear()

    return redirect(url_for("main.login", msg="Your account has been deleted."))


