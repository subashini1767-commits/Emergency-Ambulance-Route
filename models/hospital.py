class Hospital:
    def __init__(self, id, name, latitude, longitude, address, phone, beds_available=0):
        self.id = id
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.address = address
        self.phone = phone
        self.beds_available = beds_available

    @staticmethod
    def from_row(row):
        if row is None:
            return None
        return Hospital(
            id=row['id'],
            name=row['name'],
            latitude=row['latitude'],
            longitude=row['longitude'],
            address=row['address'],
            phone=row['phone'],
            beds_available=row.get('beds_available', 0)
        )
