import os

class Config:
    SECRET_KEY = os.environ.get('SESSION_SECRET') or 'dev-secret-key-change-in-production'
    DATABASE_NAME = 'dental_clinic.db'
    BACKUP_FOLDER = 'backups'
