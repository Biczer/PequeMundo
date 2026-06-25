import os
from urllib.parse import quote_plus

_password = quote_plus('zZsidTQBUbMlHFdfwBVHJcLWCZuDesdw')


import os

class Config:
    SECRET_KEY = os.environ.get(
        'SECRET_KEY',
        'dev-secret-pequemundo-2024'
    )
    MP_ACCESS_TOKEN = os.environ.get(
        'MP_ACCESS_TOKEN',
        'TEST-7405494608123272-053123-046e81571c23bf9c73efb64662b94c28-585535158'
    )
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
