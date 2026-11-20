import folium
import requests
import streamlit as st
from streamlit_folium import st_folium
from werkzeug.security import check_password_hash

from app import app as flask_app
from database.db import get_db
from services.hospital_service import HospitalService

st.set_page_config(
    page_title='Emergency Ambulance Route Optimization System',
    page_icon='🚑',
    layout='wide',
)

TAMIL_NADU_BOUNDS = (8.0, 13.6, 76.2, 80.4)
DEMO_LOCATIONS = {
    'chennai': (13.0827, 80.2707),
    'coimbatore': (11.0168, 76.9558),
    'madurai': (9.9252, 78.1198),
    'salem': (11.6643, 78.1460),
    'tiruchirappalli': (10.7905, 78.7047),
    'trichy': (10.7905, 78.7047),
    'vellore': (12.9165, 79.1325),
    'thanjavur': (10.7867, 79.1378),
    'tirunelveli': (8.7139, 77.7567),
    'nagercoil': (8.1773, 77.4344),
    'kanyakumari': (8.0883, 77.5385),
}


def in_tamil_nadu(latitude, longitude):
    min_lat, max_lat, min_lng, max_lng = TAMIL_NADU_BOUNDS
    return min_lat <= latitude <= max_lat and min_lng <= longitude <= max_lng


def login(username, password):
    with flask_app.app_context():
        row = get_db().execute(
            'SELECT id, username, full_name, role, password_hash FROM drivers WHERE username = ?',
            (username.strip(),),
        ).fetchone()
        if row and check_password_hash(row['password_hash'], password):
            return {key: row[key] for key in row.keys()}
    return None


def geocode(address):
    address = address.strip()
    if not address:
        raise ValueError('Enter an accident location in Tamil Nadu.')

    response = requests.get(
        'https://nominatim.openstreetmap.org/search',
        params={
            'q': f'{address}, Tamil Nadu, India',
            'format': 'json',
            'limit': 1,
            'countrycodes': 'in',
            'viewbox': '76.2,13.6,80.4,8.0',
            'bounded': 1,
        },
        headers={'User-Agent': 'EmergencyAmbulanceRouteOptimizer/1.0'},
        timeout=10,
    )
    response.raise_for_status()
    locations = response.json()
    if not locations:
        raise ValueError('Location not found. Enter a Tamil Nadu city or address.')
    latitude = float(locations[0]['lat'])
    longitude = float(locations[0]['lon'])
    if not in_tamil_nadu(latitude, longitude):
        raise ValueError('This demo supports Tamil Nadu locations only.')
    return latitude, longitude, locations[0].get('display_name', address)


def geocode_with_demo_fallback(address):
    try:
        return geocode(address)
    except (requests.RequestException, ValueError):
        key = address.strip().lower()
        for city, coordinates in DEMO_LOCATIONS.items():
            if city in key:
                return coordinates[0], coordinates[1], f'{city.title()}, Tamil Nadu (demo location)'
        raise ValueError('Location lookup failed. Try Chennai, Coimbatore, Madurai, Salem, or Vellore.')


def get_hospitals(latitude, longitude):
    with flask_app.app_context():
        return HospitalService.find_nearby_hospitals(latitude, longitude, max_distance_km=700, limit=7)


def get_route(start_lat, start_lng, hospital):
    distance = HospitalService.calculate_distance_km(
        start_lat, start_lng, hospital['latitude'], hospital['longitude']
    )
    points = [[start_lat, start_lng], [hospital['latitude'], hospital['longitude']]]
    duration = HospitalService.estimate_travel_time_km(
        distance, HospitalService.get_traffic_level(distance)
    )
    try:
        response = requests.get(
            f"https://router.project-osrm.org/route/v1/driving/{start_lng},{start_lat};{hospital['longitude']},{hospital['latitude']}",
            params={'overview': 'full', 'geometries': 'geojson'},
            headers={'User-Agent': 'EmergencyAmbulanceRouteOptimizer/1.0'},
            timeout=8,
        )
        response.raise_for_status()
        route = response.json()['routes'][0]
        points = [[lat, lng] for lng, lat in route['geometry']['coordinates']]
        distance = route['distance'] / 1000
        duration = max(1, round(route['duration'] / 60))
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
        pass
    return points, round(distance, 2), duration


def build_map(latitude, longitude, hospitals, selected, route_points=None):
    map_view = folium.Map(location=[latitude, longitude], zoom_start=11, tiles='OpenStreetMap')
    folium.Marker(
        [latitude, longitude],
        tooltip='Accident / emergency location',
        icon=folium.Icon(color='red', icon='plus'),
    ).add_to(map_view)
    bounds = [[latitude, longitude]]
    for hospital in hospitals:
        color = 'green' if selected and hospital['id'] == selected['id'] else 'blue'
        folium.Marker(
            [hospital['latitude'], hospital['longitude']],
            tooltip=hospital['name'],
            popup=f"{hospital['name']} | {hospital['beds_available']} beds | {hospital['distance_km']} km",
            icon=folium.Icon(color=color, icon='plus-sign'),
        ).add_to(map_view)
        bounds.append([hospital['latitude'], hospital['longitude']])
    if selected and route_points:
        folium.PolyLine(route_points, color='#d32f2f', weight=6, tooltip='Recommended shortest route').add_to(map_view)
        bounds.extend(route_points)
    map_view.fit_bounds(bounds)
    return map_view


def main():
    st.title('Emergency Ambulance Route Optimization System')
    st.caption('Python frontend and Python Flask backend | Tamil Nadu emergency routing demo')

    if 'driver' not in st.session_state:
        with st.form('sign_in_form'):
            st.subheader('Sign in')
            username = st.text_input('Username', placeholder='driver01')
            password = st.text_input('Password', type='password', placeholder='driver123')
            sign_in = st.form_submit_button('Sign in')
        if sign_in:
            driver = login(username, password)
            if driver:
                st.session_state.driver = driver
                st.rerun()
            st.error('Invalid username or password.')
        st.info('Demo login: driver01 / driver123')
        return

    driver = st.session_state.driver
    with st.sidebar:
        st.success(f"Signed in: {driver['full_name']}")
        if st.button('Back to sign-in'):
            st.session_state.clear()
            st.rerun()

    st.subheader('Emergency location')
    address = st.text_input('Enter accident location in Tamil Nadu', placeholder='Anna Nagar, Chennai')
    find_route = st.button('Find nearby hospitals and route', type='primary')

    if find_route:
        try:
            latitude, longitude, display_name = geocode_with_demo_fallback(address)
            hospitals = get_hospitals(latitude, longitude)
            available = [hospital for hospital in hospitals if hospital['beds_available'] > 0]
            if not available:
                st.warning('No nearby hospital currently reports available beds.')
                return
            selected = min(available, key=lambda hospital: (hospital['distance_km'], hospital['travel_time_minutes']))
            route_points, route_distance, route_eta = get_route(latitude, longitude, selected)
            selected = {**selected, 'distance_km': route_distance, 'travel_time_minutes': route_eta}
            st.session_state.search = {
                'latitude': latitude,
                'longitude': longitude,
                'display_name': display_name,
                'hospitals': hospitals,
                'selected': selected,
                'route_points': route_points,
            }
        except (requests.RequestException, ValueError) as error:
            st.error(str(error))

    search = st.session_state.get('search')
    if not search:
        return

    st.success(f"Accident location found: {search['display_name']}")
    st_folium(
        build_map(
            search['latitude'], search['longitude'], search['hospitals'],
            search['selected'], search['route_points'],
        ),
        width=None,
        height=520,
        key='emergency_map',
    )

    st.subheader('Nearby hospitals')
    for hospital in search['hospitals']:
        left, middle, right = st.columns([3, 2, 1])
        left.write(f"**{hospital['name']}**\n\n{hospital['address']}")
        middle.write(f"Distance: **{hospital['distance_km']} km**\n\nAvailable beds: **{hospital['beds_available']}**")
        if right.button('Go', key=f"go-{hospital['id']}", disabled=hospital['beds_available'] <= 0):
            if hospital['beds_available'] > 0:
                points, distance, eta = get_route(search['latitude'], search['longitude'], hospital)
                st.session_state.search['selected'] = {**hospital, 'distance_km': distance, 'travel_time_minutes': eta}
                st.session_state.search['route_points'] = points
                st.rerun()

    selected = search['selected']
    st.info(f"Recommended: {selected['name']} | {selected['distance_km']} km | ETA {selected['travel_time_minutes']} minutes | {selected['beds_available']} beds")
    if 'finished' not in st.session_state:
        st.session_state.finished = False
    if st.button('Finish emergency', type='secondary', disabled=st.session_state.finished):
        st.session_state.finished = True
        with flask_app.app_context():
            get_db().execute(
                "UPDATE emergency_requests SET status = 'completed' WHERE driver_id = ? AND status = 'active'",
                (driver['id'],),
            )
            get_db().commit()
        st.success('Emergency route finished and recorded.')


if __name__ == '__main__':
    main()
