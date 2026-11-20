import math
from datetime import datetime

from database.db import get_db


class HospitalService:
    """Demo hospital service. It reads from SQLite and can later be replaced by a real API client."""

    @staticmethod
    def get_all_hospitals():
        db = get_db()
        query = """
            SELECT h.*, b.beds_available
            FROM hospitals h
            LEFT JOIN hospital_bed_availability b ON b.hospital_id = h.id
            WHERE h.address LIKE '%Tamil Nadu%'
              AND (b.id IS NULL OR b.id = (
                  SELECT MAX(latest.id)
                  FROM hospital_bed_availability latest
                  WHERE latest.hospital_id = h.id
              ))
        """
        rows = db.execute(query).fetchall()
        return [
            {
                'id': row['id'],
                'name': row['name'],
                'latitude': row['latitude'],
                'longitude': row['longitude'],
                'address': row['address'],
                'phone': row['phone'],
                'beds_available': row['beds_available'] or 0,
            }
            for row in rows
        ]

    @staticmethod
    def calculate_distance_km(lat1, lon1, lat2, lon2):
        radius_km = 6371.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return radius_km * c

    @staticmethod
    def estimate_travel_time_km(distance_km, traffic_level='normal'):
        base_speed = {
            'light': 32,
            'normal': 26,
            'heavy': 18,
            'severe': 12,
        }.get(traffic_level.lower(), 26)
        minutes = max(2, int((distance_km / base_speed) * 60))
        return minutes

    @staticmethod
    def get_traffic_level(distance_km):
        if distance_km < 4:
            return 'light'
        if distance_km < 8:
            return 'normal'
        if distance_km < 12:
            return 'heavy'
        return 'severe'

    @staticmethod
    def find_nearby_hospitals(latitude, longitude, max_distance_km=700, limit=7):
        nearby = []
        seen_hospitals = set()
        for hospital in HospitalService.get_all_hospitals():
            if hospital['beds_available'] <= 0:
                continue
            identity = (
                hospital['id'],
                hospital['name'].strip().casefold(),
                round(hospital['latitude'], 5),
                round(hospital['longitude'], 5),
            )
            if identity in seen_hospitals:
                continue
            seen_hospitals.add(identity)
            distance = HospitalService.calculate_distance_km(latitude, longitude, hospital['latitude'], hospital['longitude'])
            if distance <= max_distance_km:
                traffic_level = HospitalService.get_traffic_level(distance)
                travel_time = HospitalService.estimate_travel_time_km(distance, traffic_level)
                nearby.append({
                    'id': hospital['id'],
                    'name': hospital['name'],
                    'latitude': hospital['latitude'],
                    'longitude': hospital['longitude'],
                    'address': hospital['address'],
                    'phone': hospital['phone'],
                    'beds_available': hospital['beds_available'],
                    'distance_km': round(distance, 2),
                    'traffic_level': traffic_level,
                    'travel_time_minutes': travel_time,
                    'last_updated': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                })
        nearby.sort(key=lambda item: (item['distance_km'], item['travel_time_minutes']))
        return nearby[:limit]

    @staticmethod
    def select_best_hospital(hospitals):
        if not hospitals:
            return None

        valid = [h for h in hospitals if h['beds_available'] > 0]
        if not valid:
            return None

        def ranking(hospital):
            return (
                hospital['travel_time_minutes'],
                hospital['distance_km'],
                -hospital['beds_available'],
            )

        return sorted(valid, key=ranking)[0]
