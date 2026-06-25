import os

class Config:
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "pequemundo_desarrollo_2026"
    )

    MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
