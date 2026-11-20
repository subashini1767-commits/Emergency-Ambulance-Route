class Driver:
    def __init__(self, id, username, full_name, role='driver'):
        self.id = id
        self.username = username
        self.full_name = full_name
        self.role = role

    @staticmethod
    def from_row(row):
        if row is None:
            return None
        return Driver(
            id=row['id'],
            username=row['username'],
            full_name=row['full_name'],
            role=row.get('role', 'driver')
        )
