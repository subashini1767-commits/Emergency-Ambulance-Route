from datetime import datetime

import requests
from flask import Blueprint, jsonify, render_template, request, session

from database.db import get_db
from routes.auth import get_driver_login_duration_seconds
from services.geocoding_service import GeocodingService
from services.hospital_service import HospitalService

emergency_bp = Blueprint('emergency', __name__)

TAMIL_NADU_BOUNDS = {
    'min_latitude': 8.0,
    'max_latitude': 13.6,
    'min_longitude': 76.2,
    'max_longitude': 80.4,
}


def is_tamil_nadu_location(latitude, longitude):
    return (
        TAMIL_NADU_BOUNDS['min_latitude'] <= latitude <= TAMIL_NADU_BOUNDS['max_latitude']
        and TAMIL_NADU_BOUNDS['min_longitude'] <= longitude <= TAMIL_NADU_BOUNDS['max_longitude']
    )


@emergency_bp.route('/dashboard', methods=['GET'])
def dashboard_page():
    if 'user_id' not in session or not session.get('logged_in'):
        return render_template('login.html', error='Please log in to access the dashboard.')

    db = get_db()
    driver = db.execute(
        'SELECT full_name, age, phone, reward_points FROM drivers WHERE id = ?',
        (session['user_id'],),
    ).fetchone()
    daily_minutes = get_driver_login_duration_seconds(db, session['user_id'])
    return render_template(
        'dashboard.html',
        driver_name=(driver['full_name'] if driver else session.get('full_name', 'Driver')),
        driver_age=(driver['age'] if driver and driver['age'] is not None else session.get('driver_age', 30)),
        driver_phone=(driver['phone'] if driver and driver['phone'] else session.get('driver_phone', '+91 00000 00000')),
        reward_points=(driver['reward_points'] if driver else 0),
        daily_login_seconds=daily_minutes,
    )


@emergency_bp.route('/api/locations/geocode', methods=['POST'])
def geocode_location():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Login required.'}), 401

    data = request.get_json(silent=True) or {}
    address = (data.get('address') or '').strip()

    if not address:
        return jsonify({'success': False, 'message': 'Emergency address is required.'}), 400

    try:
        result = GeocodingService.geocode_address(address)
        return jsonify({'success': True, 'location': result})
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    except RuntimeError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 500


@emergency_bp.route('/api/hospitals/nearest', methods=['POST'])
def nearest_hospitals():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Login required.'}), 401

    data = request.get_json(silent=True) or {}
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    address = (data.get('address') or '').strip()

    if latitude is None or longitude is None:
        return jsonify({'success': False, 'message': 'Latitude and longitude are required.'}), 400

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Latitude and longitude must be numeric.'}), 400

    if not is_tamil_nadu_location(latitude, longitude):
        return jsonify({
            'success': False,
            'message': 'This demo currently supports emergency locations within Tamil Nadu only.'
        }), 400

    hospitals = HospitalService.find_nearby_hospitals(latitude, longitude)
    best = HospitalService.select_best_hospital(hospitals)

    if address:
        db = get_db()
        db.execute(
            'INSERT INTO emergency_requests (driver_id, emergency_address, latitude, longitude, status, created_at) VALUES (?, ?, ?, ?, ?, ?)',
            (session['user_id'], address, latitude, longitude, 'active', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
        )
        db.commit()

    return jsonify({
        'success': True,
        'count': len(hospitals),
        'hospitals': hospitals,
        'recommended_hospital': best,
        'message': (
            f'{len(hospitals)} nearby local hospitals with available beds calculated successfully.'
            if best else
            'No nearby hospital currently has available beds.'
        )
    })


@emergency_bp.route('/api/hospitals/route', methods=['POST'])
def route_info():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Login required.'}), 401

    data = request.get_json(silent=True) or {}
    start_lat = data.get('start_lat')
    start_lng = data.get('start_lng')
    hospital_lat = data.get('hospital_lat')
    hospital_lng = data.get('hospital_lng')

    try:
        start_lat = float(start_lat)
        start_lng = float(start_lng)
        hospital_lat = float(hospital_lat)
        hospital_lng = float(hospital_lng)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Route coordinates must be numeric.'}), 400

    distance = HospitalService.calculate_distance_km(start_lat, start_lng, hospital_lat, hospital_lng)
    traffic = HospitalService.get_traffic_level(distance)
    travel_time = HospitalService.estimate_travel_time_km(distance, traffic)
    polyline = [[start_lat, start_lng], [hospital_lat, hospital_lng]]

    try:
        response = requests.get(
            f'https://router.project-osrm.org/route/v1/driving/{start_lng},{start_lat};{hospital_lng},{hospital_lat}',
            params={'overview': 'full', 'geometries': 'geojson'},
            headers={'User-Agent': 'EmergencyAmbulanceRouteOptimizer/1.0'},
            timeout=8,
        )
        response.raise_for_status()
        route_data = response.json()
        routes = route_data.get('routes') or []
        if routes:
            osrm_route = routes[0]
            polyline = [[lat, lng] for lng, lat in osrm_route['geometry']['coordinates']]
            distance = osrm_route['distance'] / 1000
            travel_time = max(1, round(osrm_route['duration'] / 60))
    except (requests.RequestException, KeyError, TypeError, ValueError):
        pass

    return jsonify({
        'success': True,
        'route': {
            'start': {'lat': start_lat, 'lng': start_lng},
            'destination': {'lat': hospital_lat, 'lng': hospital_lng},
            'distance_km': round(distance, 2),
            'travel_time_minutes': travel_time,
            'traffic_level': traffic,
            'polyline': polyline
        }
    })


@emergency_bp.route('/api/emergency/finish', methods=['POST'])
def finish_emergency():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Login required.'}), 401

    db = get_db()
    cursor = db.execute(
        "UPDATE emergency_requests SET status = 'completed' WHERE driver_id = ? AND status = 'active'",
        (session['user_id'],),
    )
    db.execute(
        'UPDATE drivers SET reward_points = reward_points + 25 WHERE id = ?',
        (session['user_id'],),
    )
    db.commit()
    return jsonify({
        'success': True,
        'message': 'Emergency route finished successfully.',
        'updated_requests': cursor.rowcount,
        'reward_awarded': 25,
    })
