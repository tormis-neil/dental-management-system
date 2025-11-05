"""
Utility Functions Module for Dental Clinic Management System

PURPOSE:
    This file contains helper functions and decorators that are reused
    throughout the application. Instead of repeating code, we centralize
    common operations here.

WHAT IT CONTAINS:
    1. Decorators: Functions that modify other functions (e.g., @manager_required)
    2. Activity Logging: Track all user actions for security and auditing
    3. Database Backup/Restore: Create and restore database copies
    4. Helper Functions: Reusable utility functions (age calculation, etc.)

WHY THIS APPROACH:
    - DRY Principle (Don't Repeat Yourself): Write once, use everywhere
    - Maintainability: Fix bugs in one place
    - Testability: Easy to test individual utility functions
    - Organization: Keeps app.py cleaner and more focused

DEPENDENCIES:
    - functools: For @wraps decorator (preserves function metadata)
    - flask: For flash messages and redirects
    - flask_login: For current_user access
    - shutil: For file operations (copy database)
    - datetime: For timestamps and date calculations
"""

# ==============================================================================
# IMPORTS
# ==============================================================================

from functools import wraps  # Preserves function metadata when creating decorators
from flask import flash, redirect, url_for  # For user feedback and navigation
from flask_login import current_user  # Access currently logged-in user
import shutil  # For file copy operations (backup/restore)
import os  # For file path operations
from datetime import datetime  # For timestamps and date calculations
from config import Config  # Application configuration settings
from models import get_db_connection  # Database connection function


# ==============================================================================
# AUTHORIZATION DECORATORS
# ==============================================================================
# Decorators are functions that wrap other functions to add functionality.
# They're used to restrict access to certain routes based on user role.
# ==============================================================================

def manager_required(f):
    """
    Decorator to restrict route access to managers only.

    PURPOSE:
        Ensures only users with 'manager' role can access certain routes.
        Used on routes like /staff, /backup, /pending_requests.

    HOW IT WORKS:
        1. Wraps the original function with a new function
        2. Before calling original function, checks if user is manager
        3. If not manager: Show error message and redirect to dashboard
        4. If manager: Call the original function normally

    USAGE:
        @app.route("/staff")
        @login_required          # First check if logged in
        @manager_required        # Then check if manager
        def staff():
            # Only managers can reach this code
            pass

    PARAMETERS:
        f: The function to wrap (the route handler)

    RETURNS:
        decorated_function: The wrapped function with authorization check

    EXAMPLE:
        Without decorator (repetitive):
            def staff():
                if not current_user.is_manager():
                    flash("Access denied")
                    return redirect(url_for("dashboard"))
                # Staff management code here

        With decorator (clean):
            @manager_required
            def staff():
                # Staff management code here
    """
    @wraps(f)  # Preserves original function's name and docstring
    def decorated_function(*args, **kwargs):
        # Check 1: Is user authenticated? (logged in)
        # Check 2: Does user have manager role?
        if not current_user.is_authenticated or not current_user.is_manager():
            # User is not authorized - show error message
            flash("Access denied. Manager privileges required.", "danger")
            # Redirect to safe page (dashboard)
            return redirect(url_for("dashboard"))

        # User is authorized - call the original function
        return f(*args, **kwargs)

    return decorated_function


def login_required_custom(f):
    """
    Custom login required decorator (alternative to Flask-Login's @login_required).

    PURPOSE:
        Checks if user is logged in before allowing access to route.
        Similar to Flask-Login's built-in decorator, but with custom message.

    NOTE:
        Currently not used in the application (we use Flask-Login's @login_required).
        Kept for reference and potential future customization.

    HOW IT WORKS:
        1. Check if current_user.is_authenticated is True
        2. If not: Show login prompt and redirect to login page
        3. If yes: Allow access to the route

    USAGE:
        @app.route("/dashboard")
        @login_required_custom
        def dashboard():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        if not current_user.is_authenticated:
            # User not logged in - show warning message
            flash("Please log in to access this page.", "warning")
            # Redirect to login page
            return redirect(url_for("login"))

        # User is logged in - proceed to route
        return f(*args, **kwargs)

    return decorated_function


# ==============================================================================
# AUDIT LOGGING FUNCTIONS
# ==============================================================================
# These functions record all user activities for security and compliance.
# Every important action (login, add patient, delete, etc.) is logged.
# ==============================================================================

def log_activity(user_id: int, username: str, action_type: str, details: str = "") -> None:
    """
    Record user activity in the audit_logs table.

    PURPOSE:
        Track all user actions for:
        - Security: Detect suspicious behavior
        - Compliance: Meet regulatory requirements (HIPAA for healthcare)
        - Debugging: Understand what happened when problems occur
        - Auditing: Review who did what and when

    HOW IT WORKS:
        1. Receive activity information (who, what, when)
        2. Connect to database
        3. Insert new row into audit_logs table
        4. Commit transaction to save permanently

    PARAMETERS:
        user_id (int): ID of user who performed action
        username (str): Username for easy reading (denormalized for performance)
        action_type (str): Type of action (LOGIN, ADD_PATIENT, DELETE_STAFF, etc.)
        details (str): Additional information about the action

    RETURNS:
        None: No return value (fire-and-forget logging)

    EXAMPLE USAGE:
        # When user logs in
        log_activity(user.id, user.username, "LOGIN", "User logged in")

        # When patient is added
        log_activity(current_user.id, current_user.username,
                    "ADD_PATIENT", f"Added patient John Doe")

        # When staff is deleted
        log_activity(current_user.id, current_user.username,
                    "DELETE_STAFF", f"Deleted staff ID 5")

    ERROR HANDLING:
        - If logging fails, prints error but doesn't crash application
        - Logging failures should not prevent main operations from working
    """
    try:
        # Open database connection (automatically closed after 'with' block)
        with get_db_connection() as conn:
            # Insert new log entry
            # Using parameterized query (?) prevents SQL injection
            conn.execute(
                "INSERT INTO audit_logs (user_id, username, action_type, details) VALUES (?, ?, ?, ?)",
                (user_id, username, action_type, details)
            )
            # Save changes to database
            conn.commit()

    except Exception as e:
        # If logging fails, print error but don't crash application
        # Logging is important but shouldn't break core functionality
        print(f"Failed to log activity: {e}")
        # In production, this should use proper logging: logger.error(f"...")


# ==============================================================================
# DATABASE BACKUP AND RESTORE FUNCTIONS
# ==============================================================================
# These functions handle creating and restoring database backups.
# Critical for data protection and disaster recovery.
# ==============================================================================

def backup_database() -> str:
    """
    Create a backup copy of the database.

    PURPOSE:
        Protect data by creating snapshots that can be restored later.
        Essential for:
        - Disaster recovery (hard drive failure, corruption)
        - Testing (restore to known state)
        - Migrations (save before upgrading)

    HOW IT WORKS:
        1. Generate filename with current timestamp
        2. Ensure backup folder exists
        3. Copy database file to backup folder
        4. Return filename so user knows which file was created

    FILENAME FORMAT:
        backup_YYYYMMDD_HHMMSS.db
        Example: backup_20251105_143022.db
        This makes backups sortable and easy to identify

    RETURNS:
        str: Name of the backup file created

    EXAMPLE USAGE:
        # In app.py backup route
        backup_filename = backup_database()
        # Returns: "backup_20251105_143022.db"

    TECHNICAL DETAILS:
        - Uses shutil.copy2() which preserves file metadata (timestamps)
        - Creates backup folder if it doesn't exist (os.makedirs)
        - Timestamp format: YYYYMMDD_HHMMSS for sortability
    """
    # Generate timestamp for filename (e.g., "20251105_143022")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create backup filename (e.g., "backup_20251105_143022.db")
    backup_filename = f"backup_{timestamp}.db"

    # Full path to backup file (e.g., "backups/backup_20251105_143022.db")
    backup_path = os.path.join(Config.BACKUP_FOLDER, backup_filename)

    # Create backup folder if it doesn't exist
    # exist_ok=True means no error if folder already exists
    os.makedirs(Config.BACKUP_FOLDER, exist_ok=True)

    # Copy database file to backup location
    # shutil.copy2() preserves file metadata (creation time, etc.)
    shutil.copy2(Config.DATABASE_NAME, backup_path)

    # Return filename so caller knows what was created
    return backup_filename


def restore_database(backup_filename: str) -> None:
    """
    Restore database from a backup file.

    PURPOSE:
        Replace current database with a previous backup.
        Used for:
        - Recovering from data corruption
        - Undoing mistakes (accidental deletions)
        - Rolling back failed migrations

    HOW IT WORKS:
        1. Construct full path to backup file
        2. Verify backup file exists
        3. Copy backup over current database
        4. Application uses restored database immediately

    PARAMETERS:
        backup_filename (str): Name of backup file to restore
                              (e.g., "backup_20251105_143022.db")

    RETURNS:
        None: No return value

    RAISES:
        FileNotFoundError: If backup file doesn't exist

    EXAMPLE USAGE:
        # In app.py restore route
        restore_database("backup_20251105_143022.db")
        # Current database is now replaced with backup

    WARNING:
        - This OVERWRITES the current database!
        - All data since backup will be lost
        - Should prompt user for confirmation before calling
        - Consider backing up current database before restoring

    TECHNICAL DETAILS:
        - Uses shutil.copy2() which preserves metadata
        - Raises FileNotFoundError if backup doesn't exist
        - No transaction needed (file-level operation)
    """
    # Construct full path to backup file
    backup_path = os.path.join(Config.BACKUP_FOLDER, backup_filename)

    # Check if backup file exists
    if os.path.exists(backup_path):
        # Copy backup file over current database
        # This REPLACES the current database completely
        shutil.copy2(backup_path, Config.DATABASE_NAME)
    else:
        # Backup file not found - raise error
        # Caller should handle this exception
        raise FileNotFoundError(f"Backup file {backup_filename} not found")


def get_backup_files() -> list:
    """
    Get list of all available backup files with metadata.

    PURPOSE:
        Display available backups to user so they can:
        - See backup history
        - Choose which backup to restore
        - Download backups for safekeeping

    HOW IT WORKS:
        1. Check if backup folder exists
        2. List all .db files in backup folder
        3. For each file, get metadata (size, creation time)
        4. Sort by creation time (newest first)
        5. Return list of dictionaries with file info

    RETURNS:
        list: List of dictionaries, each containing:
            - filename (str): Name of backup file
            - created (str): Human-readable creation time
            - size (int): File size in bytes

    RETURN FORMAT:
        [
            {
                'filename': 'backup_20251105_143022.db',
                'created': '2025-11-05 14:30:22',
                'size': 28672
            },
            {
                'filename': 'backup_20251104_120000.db',
                'created': '2025-11-04 12:00:00',
                'size': 25600
            }
        ]

    EXAMPLE USAGE:
        # In app.py backup route
        backups = get_backup_files()
        return render_template('backup.html', backups=backups)

        # In template:
        {% for backup in backups %}
            {{ backup.filename }} - {{ backup.created }} - {{ backup.size }} bytes
        {% endfor %}

    EDGE CASES:
        - If backup folder doesn't exist: Returns empty list
        - If no backup files: Returns empty list
        - Files sorted newest first for user convenience
    """
    # Check if backup folder exists
    if not os.path.exists(Config.BACKUP_FOLDER):
        # No backup folder = no backups
        return []

    # Initialize empty list to store backup info
    backups = []

    # Loop through all files in backup folder
    for filename in os.listdir(Config.BACKUP_FOLDER):
        # Only include .db files (ignore other files)
        if filename.endswith('.db'):
            # Construct full file path
            filepath = os.path.join(Config.BACKUP_FOLDER, filename)

            # Get file statistics (size, timestamps, etc.)
            stats = os.stat(filepath)

            # Add backup info to list
            backups.append({
                'filename': filename,  # e.g., "backup_20251105_143022.db"
                # Convert timestamp to readable format: "2025-11-05 14:30:22"
                'created': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'size': stats.st_size  # File size in bytes
            })

    # Sort backups by creation time (newest first)
    # Lambda function extracts 'created' field for comparison
    backups.sort(key=lambda x: x['created'], reverse=True)

    # Return list of backup dictionaries
    return backups


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================
# General-purpose utility functions used across the application.
# ==============================================================================

def calculate_age(date_of_birth: str):
    """
    Calculate a person's age from their date of birth.

    PURPOSE:
        Display patient age without storing it in database.
        Age changes over time, so we calculate it dynamically.

    HOW IT WORKS:
        1. Parse date of birth string into datetime object
        2. Get today's date
        3. Calculate year difference
        4. Adjust if birthday hasn't occurred this year yet

    PARAMETERS:
        date_of_birth (str): Date in 'YYYY-MM-DD' format
                            Example: '1990-05-15'

    RETURNS:
        int: Age in years, or None if date_of_birth is invalid/empty

    ALGORITHM EXPLANATION:
        Basic calculation: today.year - birth.year
        But need to handle birthday timing:

        Example 1: Born May 15, 1990
                  Today is Nov 5, 2025
                  - Year difference: 2025 - 1990 = 35
                  - Birthday already passed (May < Nov)
                  - Age: 35 ✓

        Example 2: Born Nov 15, 1990
                  Today is Nov 5, 2025
                  - Year difference: 2025 - 1990 = 35
                  - Birthday not yet (Nov 15 > Nov 5)
                  - Age: 35 - 1 = 34 ✓

        Tuple comparison: (today.month, today.day) < (birth.month, birth.day)
        - If True: Birthday hasn't occurred, subtract 1
        - If False: Birthday already passed, use year difference

    EXAMPLE USAGE:
        age = calculate_age('1990-05-15')
        # Returns: 35 (in 2025)

        age = calculate_age('2000-01-01')
        # Returns: 25 (in 2025)

        age = calculate_age('')
        # Returns: None (empty date)

    ERROR HANDLING:
        - Returns None if date_of_birth is None or empty
        - Returns None if date format is invalid
        - Catches ValueError and AttributeError exceptions
    """
    # Check if date_of_birth is provided
    if not date_of_birth:
        return None  # No date = no age

    try:
        # Parse date string into datetime object
        # strptime = "string parse time"
        # Format: 'YYYY-MM-DD' → '1990-05-15'
        dob = datetime.strptime(date_of_birth, '%Y-%m-%d')

        # Get today's date
        today = datetime.today()

        # Calculate age with birthday adjustment
        # Step 1: Calculate year difference
        age = today.year - dob.year

        # Step 2: Adjust if birthday hasn't occurred this year
        # Compare (month, day) tuples
        # If today's month/day is before birth month/day, subtract 1
        age = age - ((today.month, today.day) < (dob.month, dob.day))

        return age

    except (ValueError, AttributeError):
        # ValueError: Invalid date format
        # AttributeError: date_of_birth is not a string
        return None  # Return None if can't calculate age


# ==============================================================================
# MODULE SUMMARY
# ==============================================================================
"""
FUNCTIONS PROVIDED:

DECORATORS:
    - manager_required: Restrict route to managers
    - login_required_custom: Restrict route to authenticated users

LOGGING:
    - log_activity: Record user actions in audit log

BACKUP:
    - backup_database: Create database backup
    - restore_database: Restore from backup
    - get_backup_files: List available backups

HELPERS:
    - calculate_age: Calculate age from date of birth

USAGE PATTERNS:

1. Route Protection:
    @app.route("/staff")
    @login_required
    @manager_required
    def staff():
        pass

2. Activity Logging:
    log_activity(current_user.id, current_user.username,
                "ADD_PATIENT", "Added John Doe")

3. Backup Operations:
    filename = backup_database()
    restore_database(filename)
    backups = get_backup_files()

4. Age Calculation:
    age = calculate_age(patient.date_of_birth)
"""
