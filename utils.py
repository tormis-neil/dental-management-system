from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
import shutil
import os
from datetime import datetime
from config import Config
from models import get_db_connection

def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_manager():
            flash("Access denied. Manager privileges required.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function

def login_required_custom(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def log_activity(user_id: int, username: str, action_type: str, details: str = "") -> None:
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO audit_logs (user_id, username, action_type, details) VALUES (?, ?, ?, ?)",
                (user_id, username, action_type, details)
            )
            conn.commit()
    except Exception as e:
        print(f"Failed to log activity: {e}")

def backup_database() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.db"
    backup_path = os.path.join(Config.BACKUP_FOLDER, backup_filename)
    
    os.makedirs(Config.BACKUP_FOLDER, exist_ok=True)
    shutil.copy2(Config.DATABASE_NAME, backup_path)
    
    return backup_filename

def restore_database(backup_filename: str) -> None:
    backup_path = os.path.join(Config.BACKUP_FOLDER, backup_filename)
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, Config.DATABASE_NAME)
    else:
        raise FileNotFoundError(f"Backup file {backup_filename} not found")

def get_backup_files() -> list:
    if not os.path.exists(Config.BACKUP_FOLDER):
        return []
    
    backups = []
    for filename in os.listdir(Config.BACKUP_FOLDER):
        if filename.endswith('.db'):
            filepath = os.path.join(Config.BACKUP_FOLDER, filename)
            stats = os.stat(filepath)
            backups.append({
                'filename': filename,
                'created': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'size': stats.st_size
            })
    
    backups.sort(key=lambda x: x['created'], reverse=True)
    return backups

def calculate_age(date_of_birth: str):
    """Calculate age from date of birth string in YYYY-MM-DD format"""
    if not date_of_birth:
        return None
    try:
        from datetime import datetime
        dob = datetime.strptime(date_of_birth, '%Y-%m-%d')
        today = datetime.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except (ValueError, AttributeError):
        return None
