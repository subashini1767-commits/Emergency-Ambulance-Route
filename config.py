import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'database.db')


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'emergency-ambulance-demo-secret')
    DATABASE = DATABASE_PATH
    JSON_SORT_KEYS = False
