from datetime import datetime

from flask import Blueprint, jsonify, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_db

auth_bp = Blueprint('auth', __name__)


def get_driver_login_duration_seconds(db, driver_id):
    rows = db.execute(
        "SELECT created_at, activity_type FROM portal_activity WHERE driver_id = ? AND date(created_at) = date('now') ORDER BY created_at ASC",
        (driver_id,),
    ).fetchall()

    total_seconds = 0
    active_start = None
    now = datetime.now()

    for row in rows:
        activity_time = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
        if row['activity_type'] == 'login_success':
            active_start = activity_time
        elif row['activity_type'] == 'logout' and active_start is not None:
            total_seconds += (activity_time - active_start).total_seconds()
            active_start = None

    if active_start is not None:
        total_seconds += (now - active_start).total_seconds()

    return int(total_seconds)


@auth_bp.route('/login', methods=['GET'])
def login_page():
    now = datetime.now()
    db = get_db()
    db.execute(
        'INSERT INTO portal_activity (activity_type, created_at) VALUES (?, ?)',
        ('login_page_visit', now.strftime('%Y-%m-%d %H:%M:%S')),
    )
    db.commit()
    page_visits = db.execute(
        "SELECT COUNT(*) AS total FROM portal_activity WHERE activity_type = 'login_page_visit'"
    ).fetchone()['total']
    driver_users = db.execute(
        "SELECT COUNT(DISTINCT driver_id) AS total FROM portal_activity WHERE activity_type = 'login_success'"
    ).fetchone()['total']
    return render_template(
        'login.html',
        portal_time=now.strftime('%I:%M:%S %p'),
        portal_date=now.strftime('%d %b %Y'),
        login_page_time=now.strftime('%I:%M:%S %p'),
        portal_page_visits=page_visits,
        portal_driver_users=driver_users,
    )


@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required.'}), 400

    db = get_db()
    row = db.execute(
        'SELECT id, username, full_name, age, phone, reward_points, role, password_hash FROM drivers WHERE username = ?',
        (username,)
    ).fetchone()

    if row is None or not check_password_hash(row['password_hash'], password):
        return jsonify({'success': False, 'message': 'Invalid username or password.'}), 401

    session.permanent = True
    session['user_id'] = row['id']
    session['username'] = row['username']
    session['full_name'] = row['full_name']
    session['logged_in'] = True
    session['driver_age'] = row['age'] if row['age'] is not None else 30
    session['driver_phone'] = row['phone'] or '+91 00000 00000'
    db.execute(
        'INSERT INTO portal_activity (driver_id, activity_type, created_at) VALUES (?, ?, ?)',
        (row['id'], 'login_success', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
    )
    db.commit()

    return jsonify({
        'success': True,
        'message': 'Login successful.',
        'driver': {
            'id': row['id'],
            'username': row['username'],
            'full_name': row['full_name'],
            'age': row['age'],
            'phone': row['phone'],
            'reward_points': row['reward_points'],
            'role': row['role']
        }
    })


@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    full_name = (data.get('full_name') or '').strip()
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()
    age = data.get('age')
    phone = (data.get('phone') or '').strip()

    if not full_name or not username or not password:
        return jsonify({'success': False, 'message': 'Driver name, username, and password are required.'}), 400
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Password must contain at least 6 characters.'}), 400
    try:
        if age is not None:
            age = int(age)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Driver age must be a number.'}), 400

    db = get_db()
    try:
        cursor = db.execute(
            'INSERT INTO drivers (username, password_hash, full_name, age, phone, reward_points, role) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (username, generate_password_hash(password), full_name, age, phone or None, 0, 'driver'),
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        if 'UNIQUE constraint failed' in str(exc):
            return jsonify({'success': False, 'message': 'That username is already registered.'}), 409
        raise

    session.permanent = True
    session['user_id'] = cursor.lastrowid
    session['username'] = username
    session['full_name'] = full_name
    session['logged_in'] = True
    session['driver_age'] = age if age is not None else 30
    session['driver_phone'] = phone or '+91 00000 00000'
    db.execute(
        'INSERT INTO portal_activity (driver_id, activity_type, created_at) VALUES (?, ?, ?)',
        (cursor.lastrowid, 'login_success', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
    )
    db.commit()
    return jsonify({'success': True, 'message': 'Account created successfully.', 'driver': {
        'id': cursor.lastrowid,
        'username': username,
        'full_name': full_name,
        'age': age,
        'phone': phone or 'Not provided',
        'reward_points': 0,
        'role': 'driver'
    }}), 201


@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    driver_id = session.get('user_id')
    if driver_id:
        db = get_db()
        db.execute(
            'INSERT INTO portal_activity (driver_id, activity_type, created_at) VALUES (?, ?, ?)',
            (driver_id, 'logout', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        )
        db.commit()
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully.'})
