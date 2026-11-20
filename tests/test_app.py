import uuid

import pytest
from app import app
from services.hospital_service import HospitalService


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_login_page_loads(client):
    response = client.get('/login')
    assert response.status_code == 200


def test_demo_login_success(client):
    response = client.post('/api/login', json={'username': 'driver01', 'password': 'driver123'})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload['success'] is True
    assert payload['driver']['username'] == 'driver01'


def test_nearby_hospitals_are_unique_and_have_beds(client):
    with app.app_context():
        hospitals = HospitalService.find_nearby_hospitals(13.0827, 80.2707)

    names = [hospital['name'] for hospital in hospitals]
    assert len(names) == len(set(names))
    assert all(hospital['beds_available'] > 0 for hospital in hospitals)


def test_driver_profile_fields_are_saved_on_register(client):
    username = f'driver_{uuid.uuid4().hex[:8]}'
    response = client.post(
        '/api/register',
        json={
            'full_name': 'Karthick Kumar',
            'username': username,
            'password': 'newdriver123',
            'age': 28,
            'phone': '+91 98765 43210',
        },
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload['success'] is True
    assert payload['driver']['age'] == 28
    assert payload['driver']['phone'] == '+91 98765 43210'
    assert payload['driver']['reward_points'] == 0
