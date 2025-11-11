"""
Configuration Module for Dental Clinic Management System

PURPOSE:
    This file centralizes all application configuration settings.
    By keeping configurations in one place, we can easily modify settings
    without searching through the entire codebase.

WHAT IT CONTAINS:
    - Secret keys for session management and security
    - Database connection settings
    - File paths for data storage (backups, uploads, etc.)

WHY THIS APPROACH:
    - Separation of concerns: Configuration separate from business logic
    - Environment-based settings: Can override with environment variables
    - Security: Sensitive data can be loaded from environment instead of hardcoding
    - Maintainability: Easy to update settings in one location
"""

import os


class Config:
    """
    Application Configuration Class

    This class holds all configuration variables as class attributes.
    Flask reads these settings when the app starts up.

    USAGE:
        In app.py: app.config.from_object(Config)
        Access in code: Config.SECRET_KEY or app.config['SECRET_KEY']
    """

    # ============================================================================
    # SECURITY CONFIGURATION
    # ============================================================================

    # SECRET_KEY: Used by Flask for session encryption and CSRF tokens
    # HOW IT WORKS:
    #   1. Flask encrypts session cookies using this key
    #   2. Without the secret key, attackers cannot forge session cookies
    #   3. CSRF tokens are also generated using this key
    # SECURITY NOTE:
    #   - In production: MUST set SESSION_SECRET environment variable
    #   - Never commit real secret keys to version control
    #   - Generate with: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY = os.environ.get('SESSION_SECRET') or 'dev-secret-key-change-in-production'

    # ============================================================================
    # DATABASE CONFIGURATION
    # ============================================================================

    # DATABASE_NAME: SQLite database file path
    # WHAT IT IS:
    #   - Single file containing all tables and data
    #   - Created automatically in the project root directory
    # WHY SQLITE:
    #   - No separate database server needed
    #   - Perfect for academic demos and small applications
    #   - Single file makes backup/restore simple
    # PRODUCTION NOTE:
    #   - For production with many users, migrate to PostgreSQL
    DATABASE_NAME = 'dental_clinic.db'

    # ============================================================================
    # FILE STORAGE CONFIGURATION
    # ============================================================================

    # BACKUP_FOLDER: Directory where database backups are stored
    # HOW IT WORKS:
    #   - When owner clicks "Create Backup", database copied to this folder
    #   - Filenames include timestamps: backup_20251105_143022.db
    #   - Folder created automatically if it doesn't exist
    # LOCATION:
    #   - Relative path: Creates folder in project directory
    #   - On Windows: C:\path\to\project\backups\
    #   - On Mac/Linux: /path/to/project/backups/
    BACKUP_FOLDER = 'backups'


# ==============================================================================
# ENVIRONMENT VARIABLE EXPLANATION
# ==============================================================================
"""
ENVIRONMENT VARIABLES allow you to set configuration without changing code.

HOW TO USE:

Windows (PowerShell):
    $env:SESSION_SECRET = "your-secret-key-here"
    py app.py

Mac/Linux (Bash):
    export SESSION_SECRET="your-secret-key-here"
    python3 app.py

Python (in code):
    import os
    os.environ.get('SESSION_SECRET')  # Returns value or None

WHY USE ENVIRONMENT VARIABLES:
    1. Security: Secrets not in version control
    2. Flexibility: Different settings for dev/production
    3. Best Practice: Industry standard approach (12-factor app)

RECOMMENDED VARIABLES:
    - SESSION_SECRET: Random secret key
    - FLASK_ENV: 'development' or 'production'
    - DATABASE_URL: For PostgreSQL in production
"""
