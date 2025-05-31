# config
import os

basedir=os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "admin")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URI", "mysql+pymysql://user:password@localhost/music_school"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = 1800
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")