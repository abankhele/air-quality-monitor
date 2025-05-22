
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    #Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    #Openaq
    OPENAQ_API_KEY = os.getenv('OPENAQ_API_KEY')
    OPENAQ_BASE_URL = os.getenv('OPENAQ_API_URL')
    # Celery
    CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
