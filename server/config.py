from os import environ
from datetime import timedelta

CLIENT_ID = environ.get('CLIENT_ID')
CLIENT_SECRET = environ.get('CLIENT_SECRET')
REDIRECT_URI = environ.get('REDIRECT_URI')
SECRET_KEY = environ.get('SECRET_KEY')
JWT_SECRET_KEY = environ.get('SECRET_KEY')
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
SQLALCHEMY_DATABASE_URI = "sqlite:///project.db"
