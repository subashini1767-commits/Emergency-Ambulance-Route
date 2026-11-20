import sqlite3

from flask import g
from werkzeug.security import generate_password_hash

from config import DATABASE_PATH

DEMO_DRIVERS = {
    'driver01': ('Aisha Patel', 'driver123', 29, '+91 98765 12345'),
    'driver02': ('Daniel Obasi', 'driver456', 34, '+91 99887 65432'),
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS drivers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    age INTEGER,
    phone TEXT,
    reward_points INTEGER NOT NULL DEFAULT 0,
    role TEXT NOT NULL DEFAULT 'driver'
);

CREATE TABLE IF NOT EXISTS hospitals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    address TEXT NOT NULL,
    phone TEXT
);

CREATE TABLE IF NOT EXISTS hospital_bed_availability (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital_id INTEGER NOT NULL,
    beds_available INTEGER NOT NULL,
    last_updated TEXT NOT NULL,
    FOREIGN KEY(hospital_id) REFERENCES hospitals(id)
);

CREATE TABLE IF NOT EXISTS emergency_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_id INTEGER NOT NULL,
    emergency_address TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    hospital_id INTEGER,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    FOREIGN KEY(driver_id) REFERENCES drivers(id),
    FOREIGN KEY(hospital_id) REFERENCES hospitals(id)
);

CREATE TABLE IF NOT EXISTS portal_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_id INTEGER,
    activity_type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(driver_id) REFERENCES drivers(id)
);
"""

SEED_DATA = """
INSERT OR IGNORE INTO hospitals (id, name, latitude, longitude, address, phone) VALUES
    (1, 'City General Hospital', 12.9720, 77.5940, 'MG Road, Bengaluru', '+91 80 1234 0001'),
    (2, 'LifeCare Emergency Center', 12.9830, 77.6090, 'Koramangala, Bengaluru', '+91 80 1234 0002'),
    (3, 'MediBridge Trauma Hospital', 12.9650, 77.5800, 'Indiranagar, Bengaluru', '+91 80 1234 0003'),
    (4, 'Sunrise Multi-Specialty', 12.9460, 77.5730, 'Jayanagar, Bengaluru', '+91 80 1234 0004'),
    (5, 'Green Valley Hospital', 12.9900, 77.6200, 'HSR Layout, Bengaluru', '+91 80 1234 0005');

INSERT OR IGNORE INTO hospitals (id, name, latitude, longitude, address, phone) VALUES
    (6, 'Rajiv Gandhi Government General Hospital', 13.0827, 80.2707, 'Park Town, Chennai, Tamil Nadu', '+91 44 2530 5000'),
    (7, 'Coimbatore Medical College Hospital', 11.0168, 76.9558, 'Avinashi Road, Coimbatore, Tamil Nadu', '+91 422 257 0170'),
    (8, 'Madurai Government Rajaji Hospital', 9.9252, 78.1198, 'Alagar Koyil Road, Madurai, Tamil Nadu', '+91 452 253 2535'),
    (9, 'Tiruchirappalli Government Hospital', 10.7905, 78.7047, 'Puthur, Tiruchirappalli, Tamil Nadu', '+91 431 277 1400'),
    (10, 'Government Vellore Medical College Hospital', 12.9165, 79.1325, 'Adukkamparai, Vellore, Tamil Nadu', '+91 416 228 1000'),
    (11, 'Government Mohan Kumaramangalam Medical College Hospital', 11.6643, 78.1460, 'Salem, Tamil Nadu', '+91 427 221 0000'),
    (12, 'Thanjavur Medical College Hospital', 10.7867, 79.1378, 'Medical College Road, Thanjavur, Tamil Nadu', '+91 4362 240 101'),
    (13, 'Tirunelveli Government Medical College Hospital', 8.7139, 77.7567, 'High Ground, Tirunelveli, Tamil Nadu', '+91 462 257 2733'),
    (14, 'Government Medical College Hospital, Sivaganga', 9.8433, 78.4809, 'Sivaganga, Tamil Nadu', '+91 4577 240 200'),
    (15, 'Government Hospital, Kanyakumari', 8.0883, 77.5385, 'Asaripallam, Nagercoil, Tamil Nadu', '+91 4652 223 333'),
    (16, 'Coimbatore City Emergency Hospital', 11.0185, 76.9665, 'Gandhipuram, Coimbatore, Tamil Nadu', '+91 422 400 1100'),
    (17, 'Kovai Trauma and Critical Care Centre', 11.0112, 76.9588, 'Ram Nagar, Coimbatore, Tamil Nadu', '+91 422 400 1200'),
    (18, 'Avinashi Road Emergency Hospital', 11.0245, 76.9780, 'Avinashi Road, Coimbatore, Tamil Nadu', '+91 422 400 1300'),
    (19, 'North Coimbatore Medical Centre', 11.0400, 76.9500, 'Saibaba Colony, Coimbatore, Tamil Nadu', '+91 422 400 1400'),
    (20, 'Kovai Government Emergency Unit', 11.0050, 76.9505, 'Ukkadam, Coimbatore, Tamil Nadu', '+91 422 400 1500');

INSERT OR IGNORE INTO hospital_bed_availability (hospital_id, beds_available, last_updated) VALUES
    (6, 24, '2026-08-19 08:00:00'),
    (7, 18, '2026-08-19 08:00:00'),
    (8, 21, '2026-08-19 08:00:00'),
    (9, 14, '2026-08-19 08:00:00'),
    (10, 16, '2026-08-19 08:00:00'),
    (11, 12, '2026-08-19 08:00:00'),
    (12, 10, '2026-08-19 08:00:00'),
    (13, 15, '2026-08-19 08:00:00'),
    (14, 8, '2026-08-19 08:00:00'),
    (15, 11, '2026-08-19 08:00:00'),
    (16, 14, '2026-08-21 08:00:00'),
    (17, 9, '2026-08-21 08:00:00'),
    (18, 11, '2026-08-21 08:00:00'),
    (19, 7, '2026-08-21 08:00:00'),
    (20, 6, '2026-08-21 08:00:00');

INSERT OR IGNORE INTO hospital_bed_availability (hospital_id, beds_available, last_updated) VALUES
    (1, 12, '2026-08-18 08:00:00'),
    (2, 0, '2026-08-18 08:05:00'),
    (3, 7, '2026-08-18 08:10:00'),
    (4, 15, '2026-08-18 08:20:00'),
    (5, 9, '2026-08-18 08:25:00');
"""


def get_db():
    if 'db' not in g:
        connection = sqlite3.connect(DATABASE_PATH)
        connection.row_factory = sqlite3.Row
        g.db = connection
    return g.db


def close_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db(app):
    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA)

        columns = {row[1] for row in db.execute('PRAGMA table_info(drivers)').fetchall()}
        if 'age' not in columns:
            db.execute('ALTER TABLE drivers ADD COLUMN age INTEGER')
        if 'phone' not in columns:
            db.execute('ALTER TABLE drivers ADD COLUMN phone TEXT')
        if 'reward_points' not in columns:
            db.execute('ALTER TABLE drivers ADD COLUMN reward_points INTEGER NOT NULL DEFAULT 0')

        db.executescript(SEED_DATA)

        for username, (full_name, password, age, phone) in DEMO_DRIVERS.items():
            db.execute(
                'INSERT OR IGNORE INTO drivers (username, password_hash, full_name, age, phone, reward_points, role) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (username, generate_password_hash(password), full_name, age, phone, 0, 'driver')
            )
            db.execute(
                'UPDATE drivers SET password_hash = ?, full_name = ?, age = ?, phone = ?, reward_points = ?, role = ? WHERE username = ?',
                (generate_password_hash(password), full_name, age, phone, 0, 'driver', username)
            )

        db.commit()
        app.teardown_appcontext(close_db)
