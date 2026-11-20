import requests

DEMO_LOCATIONS = {
    'gandhipuram': (11.0168, 76.9558),
    'coimbatore': (11.0168, 76.9558),
    'chennai': (13.0827, 80.2707),
    'madurai': (9.9252, 78.1198),
    'salem': (11.6643, 78.1460),
    'trichy': (10.7905, 78.7047),
    'tiruchirappalli': (10.7905, 78.7047),
    'vellore': (12.9165, 79.1325),
    'tirunelveli': (8.7139, 77.7567),
    'nagercoil': (8.1773, 77.4344),
}


class GeocodingService:
    """Simple geocoding adapter. It uses Nominatim for demo purposes and can be replaced later."""

    @staticmethod
    def geocode_address(address):
        if not address or not str(address).strip():
            raise ValueError('Address is required.')

        url = 'https://nominatim.openstreetmap.org/search'
        clean_address = str(address).strip()
        search_query = clean_address if 'tamil nadu' in clean_address.lower() else f'{clean_address}, Tamil Nadu, India'
        params = {
            'q': search_query,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'in',
            'viewbox': '76.2,13.6,80.4,8.0',
            'bounded': 1,
        }
        headers = {'User-Agent': 'EmergencyAmbulanceRouteOptimizer/1.0'}

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            result = data[0]
            latitude = float(result['lat'])
            longitude = float(result['lon'])
            if not 8.0 <= latitude <= 13.6 or not 76.2 <= longitude <= 80.4:
                raise ValueError('Please enter a location within Tamil Nadu.')
            return {
                'latitude': latitude,
                'longitude': longitude,
                'display_name': result.get('display_name', clean_address)
            }
        except (requests.RequestException, ValueError):
            address_lower = clean_address.lower()
            for place, (latitude, longitude) in DEMO_LOCATIONS.items():
                if place in address_lower:
                    return {
                        'latitude': latitude,
                        'longitude': longitude,
                        'display_name': f'{clean_address.title()} (demo location)'
                    }
            raise ValueError(
                'Location not found. Please enter a valid Tamil Nadu location, '
                'for example Gandhipuram, Coimbatore.'
            )
