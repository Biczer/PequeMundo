import os
from urllib.parse import quote_plus

_password = quote_plus('zZsidTQBUbMlHFdfwBVHJcLWCZuDesdw')


import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    MP_ACCESS_TOKEN = os.environ.get('MP_ACCESS_TOKEN')

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") + "?sslmode=require"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
