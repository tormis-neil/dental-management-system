"""
Main Application Module for Dental Clinic Management System

PURPOSE:
    This is the core Flask application file that handles all HTTP requests and responses.
    It's the "Controller" layer in the MVC (Model-View-Controller) architecture.
    All web routes (URLs) and business logic are defined here.

WHAT IT CONTAINS:
    1. Flask Application Setup: Initializes Flask app with security features
    2. Authentication Routes: Login, logout, session management
    3. Dashboard Route: Overview page with statistics and recent activity
    4. Patient Routes: CRUD operations for patient records
    5. Staff Management Routes: CRUD operations for staff accounts (owner only)
    6. Pending Requests Routes: Deletion approval workflow (owner only)
    7. Profile Management Routes: User can update their own profile
    8. Audit Log Routes: View activity history
    9. Backup/Restore Routes: Database backup and restore (owner only)

WHY THIS APPROACH:
    - RESTful Routes: URLs follow REST conventions (/patients, /patients/add, etc.)
    - Role-Based Access: Decorators restrict routes based on user role
    - Security First: CSRF protection, password hashing, login required
    - Audit Trail: All important actions are logged for compliance
    - User Feedback: Flash messages inform users of success/errors

SECURITY FEATURES:
    - CSRF Protection: All POST requests require valid token
    - Authentication: Flask-Login manages user sessions
    - Authorization: Role-based access control (owner/dentist/staff)
    - SQL Injection Prevention: Parameterized queries throughout
    - Password Hashing: PBKDF2-SHA256 for all passwords
    - Activity Logging: All actions recorded in audit_logs table

DEPENDENCIES:
    - Flask: Web framework
    - Flask-Login: User session management
    - Flask-WTF: CSRF protection
    - Werkzeug: Password hashing and file utilities
    - SQLite3: Database (accessed via models.py)
"""

# ==============================================================================
# IMPORTS
# ==============================================================================

# Flask core imports for web functionality
from flask import (
    Flask,                  # Main Flask application class
    render_template,        # Render Jinja2 templates with data
    request,                # Access request data (forms, query params, etc.)
    redirect,               # Redirect to another route
    url_for,                # Generate URLs from route names
    flash,                  # Display one-time messages to user
    session,                # Access session data (cookies)
    send_file               # Send file downloads to user
)

# Flask-Login for user authentication and session management
from flask_login import (
    LoginManager,           # Manages user sessions
    login_user,             # Log in a user (create session)
    logout_user,            # Log out a user (destroy session)
    login_required,         # Decorator: route requires login
    current_user            # Access currently logged-in user
)

# Flask-WTF for CSRF protection (Cross-Site Request Forgery)
from flask_wtf import CSRFProtect

# Werkzeug utilities for security
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import safe_join  # Safely join file paths (prevent directory traversal)

# Type hints for better code quality
from typing import Optional

# Standard library imports
import os  # File system operations

# Import from our modules
from config import Config  # Application configuration
from models import User, get_db_connection, init_db, PendingRequest  # Database models
from utils import (
    owner_required,         # Decorator: route requires owner role
    login_required_custom,  # Custom login decorator (unused, but available)
    log_activity,           # Log user actions to audit_logs
    backup_database,        # Create database backup
    restore_database,       # Restore database from backup
    get_backup_files,       # List available backups
    calculate_age           # Calculate age from date of birth
)


# ==============================================================================
# FLASK APPLICATION SETUP
# ==============================================================================

# Create Flask application instance
# __name__ tells Flask where to find templates and static files
app = Flask(__name__)

# Load configuration from Config class (config.py)
# This sets SECRET_KEY, DATABASE_NAME, BACKUP_FOLDER
app.config.from_object(Config)

# Enable CSRF protection for all POST requests
# This prevents Cross-Site Request Forgery attacks
# All forms must include {{ csrf_token() }} in templates
csrf = CSRFProtect(app)


# ==============================================================================
# FLASK-LOGIN SETUP
# ==============================================================================
# Flask-Login manages user sessions (who is logged in, what is their user ID).
# It stores user ID in encrypted session cookie.
# ==============================================================================

# Create LoginManager instance and attach to Flask app
login_manager = LoginManager(app)

# Set the route name for login page
# If user tries to access @login_required route without being logged in,
# they will be redirected to this route
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id: str) -> Optional[User]:
    """
    Load user from database by ID (called by Flask-Login for every request).

    PURPOSE:
        Flask-Login stores user ID in session cookie.
        On each request, it calls this function to load the full User object.
        This allows us to access current_user in routes and templates.

    HOW IT WORKS:
        1. Flask-Login reads user ID from session cookie
        2. Calls this function with user ID as string
        3. We convert to int and query database
        4. Return User object or None if not found

    PARAMETERS:
        user_id (str): User ID from session cookie (always a string)

    RETURNS:
        Optional[User]: User object if found, None if not found or invalid

    CALLED BY:
        Flask-Login automatically on every request after user logs in

    SECURITY NOTE:
        If this returns None, user is logged out automatically
    """
    return User.get_by_id(int(user_id))


# Initialize database (create tables if they don't exist)
# This runs once when the application starts
init_db()


# ==============================================================================
# AUTHENTICATION ROUTES
# ==============================================================================
# Routes for login, logout, and root redirect.
# These handle user authentication and session management.
# ==============================================================================

@app.route("/")
def index():
    """
    Root route (homepage) - redirects to login page.

    PURPOSE:
        Redirect users to login page when they visit the root URL.

    SECURITY:
        No @login_required decorator - anyone can access this route.
        This is intentional so new users can reach the login page.

    RETURNS:
        Redirect to login page
    """
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Login page and authentication handler.

    PURPOSE:
        Display login form (GET request) and authenticate users (POST request).

    HOW IT WORKS:
        GET request:
            1. Display login.html template with form

        POST request:
            1. Get username and password from form
            2. Query database for user with that username
            3. Verify password hash matches
            4. If valid: Log in user, create session, log activity, redirect to dashboard
            5. If invalid: Show error message, display form again

    METHODS:
        GET: Display login form
        POST: Process login credentials

    FORM FIELDS:
        - username (str): Login username
        - password (str): Plaintext password (will be hashed for comparison)

    SECURITY FEATURES:
        - Password verification using hash comparison (never store plaintext)
        - Activity logging (tracks all login attempts)
        - Flash message feedback (success or error)
        - CSRF protection (automatic via CSRFProtect)

    RETURNS:
        GET: Rendered login.html template
        POST (success): Redirect to dashboard
        POST (failure): Rendered login.html with error message
    """
    if request.method == "POST":
        # Get form data (empty string if field is missing)
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # Query database for user with this username
        user = User.get_by_username(username)

        # Verify user exists and password is correct
        if user and user.verify_password(password):
            # Authentication successful!

            # Create session for this user (Flask-Login)
            login_user(user)

            # Log this login for audit trail
            log_activity(user.id, user.username, "LOGIN", "User logged in")

            # Show welcome message to user
            flash(f"Welcome back, {user.full_name or user.username}!", "success")

            # Redirect to dashboard
            return redirect(url_for("dashboard"))
        else:
            # Authentication failed - either user doesn't exist or password is wrong
            # DON'T specify which one (security: don't leak username existence)
            flash("Invalid username or password.", "danger")

    # GET request or POST with error: Display login form
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """
    Logout route - destroys user session.

    PURPOSE:
        Log out the current user and redirect to login page.

    HOW IT WORKS:
        1. Log the logout activity (audit trail)
        2. Destroy user session (Flask-Login)
        3. Show confirmation message
        4. Redirect to login page

    PERMISSIONS:
        @login_required: User must be logged in to log out
        (This prevents error if someone accesses /logout without being logged in)

    SECURITY:
        - Activity logged before logout (ensures current_user still available)
        - Session destroyed completely (no lingering access)

    RETURNS:
        Redirect to login page with success message
    """
    # Log logout activity BEFORE logging out
    # (After logout_user(), current_user won't be available)
    log_activity(current_user.id, current_user.username, "LOGOUT", "User logged out")

    # Destroy user session
    logout_user()

    # Show confirmation message
    flash("You have been logged out.", "success")

    # Redirect to login page
    return redirect(url_for("login"))


# ==============================================================================
# DASHBOARD ROUTE
# ==============================================================================
# Main dashboard page showing statistics and recent activity.
# ==============================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """
    Dashboard page - overview with statistics and recent activity.

    PURPOSE:
        Display system overview with key metrics:
        - Total patients and staff counts
        - Recent patients (last 5)
        - Recent activities (last 5)
        - Pending deletion requests (for owners, top 3)

    PERMISSIONS:
        @login_required: All authenticated users can access dashboard

    HOW IT WORKS:
        1. Initialize variables to default values
        2. Query database for statistics and recent data
        3. If user is owner: Also fetch pending deletion requests
        4. Render dashboard.html with all data

    ROLE-SPECIFIC DISPLAY:
        - All users: See patient count, recent patients, recent activities
        - Owners only: Also see staff count and pending deletion requests
        - Staff/Dentists: See limited information

    DATABASE QUERIES:
        - Total patients: COUNT(*) from patients table
        - Total staff: COUNT(*) from users WHERE role='staff'
        - Recent patients: Last 5 patients by created_at
        - Recent activities: Last 5 audit log entries
        - Pending requests: Last 3 pending deletion requests (owners only)

    RETURNS:
        Rendered dashboard.html template with:
        - total_patients (int)
        - total_staff (int)
        - recent_patients (list[dict])
        - recent_activities (list[dict])
        - pending_requests (list[dict])
        - total_pending_count (int)
    """
    # Initialize variables with default values
    # (These will be populated from database queries)
    total_patients = 0
    total_staff = 0
    recent_patients = []
    recent_activities = []
    pending_requests_list = []
    total_pending_count = 0

    with get_db_connection() as conn:
        # Query: Count total patients
        total_patients = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]

        # Query: Count total staff members
        total_staff = conn.execute("SELECT COUNT(*) FROM users WHERE role='staff'").fetchone()[0]

        # Query: Get last 5 patients (most recently added)
        recent_patients = conn.execute("""
            SELECT first_name, last_name, phone, created_at
            FROM patients
            ORDER BY created_at DESC LIMIT 5
        """).fetchall()

        # Query: Get last 5 audit log entries (most recent activity)
        recent_activities = conn.execute("""
            SELECT username, action_type AS action, timestamp
            FROM audit_logs
            ORDER BY timestamp DESC LIMIT 5
        """).fetchall()

        # If user is owner, dentist, or admin: Show pending deletion requests
        if current_user.is_owner() or current_user.is_dentist() or current_user.is_admin():
            # Query: Get top 3 pending deletion requests
            # JOIN with patients to get patient name
            rows = conn.execute("""
                SELECT pr.id, p.first_name, p.last_name, pr.requested_by, pr.requested_at
                FROM pending_requests pr
                JOIN patients p ON pr.patient_id = p.id
                WHERE pr.status = 'pending'
                ORDER BY pr.requested_at DESC
                LIMIT 3
            """).fetchall()

            # Convert sqlite3.Row objects to dictionaries
            pending_requests_list = [dict(r) for r in rows]

            # Query: Count total pending requests (for badge display)
            total_pending_count = conn.execute(
                "SELECT COUNT(*) FROM pending_requests WHERE status = 'pending'"
            ).fetchone()[0]

            # Add requester username to each request
            # Step 1: Extract all user IDs
            user_ids = [r["requested_by"] for r in pending_requests_list]
            user_map = {}

            # Step 2: Bulk fetch usernames (efficient - one query instead of N queries)
            if user_ids:
                # Create dynamic placeholders for IN clause: WHERE id IN (?, ?, ?)
                rows_users = conn.execute(
                    f"SELECT id, username FROM users WHERE id IN ({','.join(['?']*len(user_ids))})",
                    user_ids
                ).fetchall()
                # Build mapping: {user_id: username}
                user_map = {r["id"]: r["username"] for r in rows_users}

            # Step 3: Add username to each request dictionary
            for r in pending_requests_list:
                r["requested_by_name"] = user_map.get(r["requested_by"], "Unknown")

    # Render dashboard template with all collected data
    return render_template(
        'dashboard.html',
        total_patients=total_patients,
        total_staff=total_staff,
        recent_patients=recent_patients,
        recent_activities=recent_activities,
        pending_requests=pending_requests_list,
        total_pending_count=total_pending_count
    )


# ==============================================================================
# PATIENT MANAGEMENT ROUTES
# ==============================================================================
# CRUD operations for patient records: List, Add, View, Edit, Delete.
# All authenticated users can manage patients (with some role restrictions).
# ==============================================================================

@app.route("/patients")
@login_required
def patients():
    """
    Patient list page with search and filter functionality.

    PURPOSE:
        Display all patients in a table with search and gender filter.

    PERMISSIONS:
        @login_required: All authenticated users can view patients

    QUERY PARAMETERS:
        - search (str): Search by name, phone, or patient ID
        - gender (str): Filter by gender (Male, Female, Other)

    HOW IT WORKS:
        1. Get search and filter parameters from URL query string
        2. Build SQL query dynamically based on filters
        3. Execute query and fetch all matching patients
        4. Calculate age for each patient (from date_of_birth)
        5. Render patients.html with patient list

    SQL QUERY CONSTRUCTION:
        - Base query: "SELECT * FROM patients WHERE 1=1"
        - Add search: AND (first_name LIKE ? OR last_name LIKE ? OR phone LIKE ? OR id LIKE ?)
        - Add gender filter: AND gender = ?
        - Order by: id DESC (newest first)

    EXAMPLE URLS:
        /patients → All patients
        /patients?search=john → Patients with "john" in name/phone/ID
        /patients?gender=Female → Female patients only
        /patients?search=123&gender=Male → Male patients with "123" in name/phone/ID

    RETURNS:
        Rendered patients.html template with:
        - patients (list[dict]): Patient records with calculated age
        - search (str): Current search query (for form repopulation)
        - gender (str): Current gender filter (for form repopulation)
    """
    # Get query parameters from URL (default to empty string)
    search = request.args.get("search", "")
    gender = request.args.get("gender", "")

    with get_db_connection() as conn:
        # Build dynamic SQL query based on filters
        query = "SELECT * FROM patients WHERE 1=1"  # WHERE 1=1 allows easy AND appending
        params = []  # Parameters for parameterized query (prevents SQL injection)

        # Add search filter if provided
        if search:
            # Search across multiple columns using LIKE (case-insensitive pattern matching)
            query += " AND (first_name LIKE ? OR last_name LIKE ? OR phone LIKE ? OR CAST(id AS TEXT) LIKE ?)"
            # Add % wildcards for partial matching: "john" matches "John Smith"
            search_param = f"%{search}%"
            # Same search param for all 4 columns
            params.extend([search_param, search_param, search_param, search_param])

        # Add gender filter if provided
        if gender:
            query += " AND gender = ?"
            params.append(gender)

        # Order by ID descending (newest patients first)
        query += " ORDER BY id DESC"

        # Execute query with parameters
        patients = conn.execute(query, params).fetchall()

    # Calculate age for each patient
    # sqlite3.Row objects are dict-like but not mutable, so convert to dict
    patients_list = []
    for p in patients:
        patient_dict = dict(p)  # Convert sqlite3.Row to dict
        patient_dict['age'] = calculate_age(patient_dict.get('date_of_birth'))  # Add age field
        patients_list.append(patient_dict)

    # Render template with patient list and current filters
    return render_template("patients.html", patients=patients_list, search=search, gender=gender)


@app.route("/patients/add", methods=["GET", "POST"])
@login_required
def add_patient():
    """
    Add new patient page and handler.

    PURPOSE:
        Display form to add new patient (GET) and process form submission (POST).

    PERMISSIONS:
        @login_required: All authenticated users can add patients
        Role-specific fields:
        - Owners/Dentists: Can fill medical fields (allergies, conditions, notes)
        - Staff: Can only fill basic information

    METHODS:
        GET: Display add_patient.html form
        POST: Process form and insert patient into database

    FORM FIELDS:
        Basic information (all roles):
        - first_name (str) *required*
        - last_name (str) *required*
        - date_of_birth (str) format: YYYY-MM-DD
        - gender (str)
        - phone (str)
        - email (str)
        - address (str)
        - emergency_contact_name (str)
        - emergency_contact_phone (str)

        Medical information (owners/dentists only):
        - allergies (str)
        - existing_condition (str)
        - dentist_notes (str)
        - assigned_dentist (str)

    HOW IT WORKS:
        POST request:
        1. Get all form fields
        2. Check role to determine which fields to accept
        3. Validate required fields (first_name, last_name)
        4. Insert patient into database
        5. Log activity
        6. Redirect to patients list with success message

    SECURITY:
        - Parameterized queries prevent SQL injection
        - Activity logged for audit trail
        - CSRF protection via CSRFProtect

    RETURNS:
        GET: Rendered add_patient.html form
        POST (success): Redirect to patients list with success message
        POST (error): Redirect to add_patient with error message
    """
    if request.method == "POST":
        # Get basic patient information from form
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        date_of_birth = request.form.get("date_of_birth")
        gender = request.form.get("gender")
        phone = request.form.get("phone")
        email = request.form.get("email")
        address = request.form.get("address")
        emergency_contact_name = request.form.get("emergency_contact_name")
        emergency_contact_phone = request.form.get("emergency_contact_phone")

        # Initialize medical fields to None (only owners/dentists can set these)
        allergies = None
        existing_condition = None
        dentist_notes = None
        assigned_dentist = None

        # Check user role to determine which fields they can fill
        if current_user.is_owner() or current_user.is_dentist() or current_user.is_admin():
            # Owners/dentists can fill all medical fields
            allergies = request.form.get("allergies")
            existing_condition = request.form.get("existing_condition")
            dentist_notes = request.form.get("dentist_notes")
            assigned_dentist = request.form.get("assigned_dentist")
        elif current_user.is_staff():
            # Staff can only assign themselves as the dentist
            assigned_dentist = current_user.full_name or current_user.username

        # Validate required fields
        if not first_name or not last_name:
            flash("First Name and Last Name are required.", "danger")
            return redirect(url_for("add_patient"))

        try:
            with get_db_connection() as conn:
                # Insert new patient record
                conn.execute(
                    """
                    INSERT INTO patients (
                        first_name, last_name, date_of_birth, gender, phone, email,
                        address, emergency_contact_name, emergency_contact_phone,
                        allergies, existing_condition, dentist_notes, assigned_dentist, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        first_name, last_name, date_of_birth, gender, phone, email,
                        address, emergency_contact_name, emergency_contact_phone,
                        allergies, existing_condition, dentist_notes, assigned_dentist, current_user.id
                    )
                )
                conn.commit()

            # Log activity for audit trail
            log_activity(current_user.id, current_user.username, "ADD_PATIENT",
                        f"Added patient {first_name} {last_name}")

            # Show success message
            flash("Patient added successfully!", "success")

            # Redirect to patients list
            return redirect(url_for("patients"))

        except Exception as e:
            # Database error - show error message and log to console
            print("Error adding patient:", e)
            flash("Failed to add patient.", "danger")
            return redirect(url_for("add_patient"))

    # GET request: Display form
    return render_template("add_patient.html")


@app.route("/patients/view/<int:patient_id>")
@login_required
def view_patient(patient_id):
    """
    View patient details page (read-only).

    PURPOSE:
        Display full patient information in read-only format.

    PERMISSIONS:
        @login_required: All authenticated users can view patients

    URL PARAMETERS:
        patient_id (int): ID of patient to view

    HOW IT WORKS:
        1. Query database for patient with given ID
        2. If not found: Show error and redirect to patients list
        3. If found: Calculate age and render view_patient.html

    EXAMPLE URL:
        /patients/view/5 → View patient with ID 5

    RETURNS:
        If patient found: Rendered view_patient.html with patient data
        If patient not found: Redirect to patients list with error message
    """
    with get_db_connection() as conn:
        # Query database for patient with given ID
        patient = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()

    # Check if patient exists
    if not patient:
        flash("Patient not found.", "danger")
        return redirect(url_for("patients"))

    # Convert sqlite3.Row to dict and add calculated age
    patient_dict = dict(patient)
    patient_dict['age'] = calculate_age(patient_dict.get('date_of_birth'))

    # Render view template with patient data
    return render_template("view_patient.html", patient=patient_dict)


@app.route("/patients/edit/<int:patient_id>", methods=["GET", "POST"])
@login_required
def edit_patient(patient_id):
    """
    Edit patient page and handler.

    PURPOSE:
        Display form to edit existing patient (GET) and process updates (POST).

    PERMISSIONS:
        @login_required: All authenticated users can edit patients
        Role-specific fields:
        - Owners/Dentists: Can edit all fields including medical information
        - Staff: Can only edit basic information (not medical fields)

    URL PARAMETERS:
        patient_id (int): ID of patient to edit

    METHODS:
        GET: Display edit_patient.html form with current patient data
        POST: Process form and update patient in database

    HOW IT WORKS:
        GET request:
        1. Query patient from database
        2. If not found: Show error and redirect
        3. If found: Render form with patient data pre-filled

        POST request:
        1. Get all form fields
        2. Check role to determine which fields to update
        3. Build and execute UPDATE query
        4. Log activity
        5. Redirect to patients list with success message

    ROLE-SPECIFIC UPDATES:
        Owners/Dentists:
        - Update all fields (basic + medical)

        Staff:
        - Update only basic information fields
        - Medical fields remain unchanged

    EXAMPLE URL:
        /patients/edit/5 → Edit patient with ID 5

    RETURNS:
        GET: Rendered edit_patient.html with patient data
        POST (success): Redirect to patients list with success message
        POST (patient not found): Redirect to patients list with error message
    """
    with get_db_connection() as conn:
        # Query patient from database
        patient = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()

        # Check if patient exists
        if not patient:
            flash("Patient not found.", "danger")
            return redirect(url_for("patients"))

        if request.method == "POST":
            # Get form data
            first_name = request.form.get("first_name")
            last_name = request.form.get("last_name")
            date_of_birth = request.form.get("date_of_birth")
            gender = request.form.get("gender")
            phone = request.form.get("phone")
            email = request.form.get("email")
            address = request.form.get("address")
            emergency_contact_name = request.form.get("emergency_contact_name")
            emergency_contact_phone = request.form.get("emergency_contact_phone")

            # Check role to determine which fields to update
            if current_user.is_owner() or current_user.is_dentist() or current_user.is_admin():
                # Owners/dentists can update all fields including medical
                allergies = request.form.get("allergies")
                existing_condition = request.form.get("existing_condition")
                dentist_notes = request.form.get("dentist_notes")
                assigned_dentist = request.form.get("assigned_dentist")

                # Update query with all fields
                conn.execute("""
                    UPDATE patients SET
                        first_name=?, last_name=?, date_of_birth=?, gender=?, phone=?,
                        email=?, address=?, emergency_contact_name=?, emergency_contact_phone=?,
                        allergies=?, existing_condition=?, dentist_notes=?, assigned_dentist=?,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                """, (
                    first_name, last_name, date_of_birth, gender, phone,
                    email, address, emergency_contact_name, emergency_contact_phone,
                    allergies, existing_condition, dentist_notes, assigned_dentist, patient_id
                ))
            else:
                # Staff can only update basic information (not medical fields)
                conn.execute("""
                    UPDATE patients SET
                        first_name=?, last_name=?, date_of_birth=?, gender=?, phone=?,
                        email=?, address=?, emergency_contact_name=?, emergency_contact_phone=?,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                """, (
                    first_name, last_name, date_of_birth, gender, phone,
                    email, address, emergency_contact_name, emergency_contact_phone, patient_id
                ))

            # Save changes
            conn.commit()

            # Log activity
            log_activity(current_user.id, current_user.username, "EDIT_PATIENT",
                        f"Edited patient ID {patient_id}")

            # Show success message
            flash("Patient updated successfully!", "success")

            # Redirect to patients list
            return redirect(url_for("patients"))

        # GET request: Convert patient to dict for template
        patient = dict(patient)

    # Render edit form with patient data
    return render_template("edit_patient.html", patient=patient)


@app.route("/patients/delete/<int:patient_id>", methods=["POST"])
@login_required
def delete_patient(patient_id):
    """
    Delete patient (owners and dentists only).

    PURPOSE:
        Permanently delete a patient record from database.

    PERMISSIONS:
        @login_required: Must be logged in
        Owners and dentists only: Staff must request deletion (see request_delete_patient)

    URL PARAMETERS:
        patient_id (int): ID of patient to delete

    METHOD:
        POST only (prevents accidental deletion via URL)

    HOW IT WORKS:
        1. Check if user is owner or dentist
        2. If not: Show error and redirect
        3. If yes: Query patient, delete record, log activity, redirect

    SECURITY:
        - POST-only route (prevents CSRF via GET)
        - Role check before deletion
        - Activity logged for audit trail
        - CSRF token required (automatic via CSRFProtect)

    WORKFLOW:
        Owners/Dentists: Click "Delete" → Confirm → Patient deleted immediately
        Staff: Must use "Request Delete" → Owner approves → Patient deleted

    EXAMPLE URL:
        POST /patients/delete/5 → Delete patient with ID 5

    RETURNS:
        Redirect to patients list with success or error message
    """
    # Check if user has permission to delete directly
    if not (current_user.is_owner() or current_user.is_dentist()):
        flash("Only owners and dentists can delete patients directly.", "danger")
        return redirect(url_for("patients"))

    with get_db_connection() as conn:
        # Check if patient exists
        patient = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()

        if not patient:
            flash("Patient not found.", "danger")
        else:
            # Delete patient record
            conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
            conn.commit()

            # Log activity
            log_activity(current_user.id, current_user.username, "DELETE_PATIENT",
                         f"Deleted patient ID {patient_id}")

            # Show success message
            flash("Patient deleted successfully!", "success")

    # Redirect to patients list
    return redirect(url_for("patients"))


@app.route('/patients/request_delete/<int:patient_id>', methods=['POST'])
@login_required
def request_delete_patient(patient_id):
    """
    Request patient deletion (staff only - requires owner approval).

    PURPOSE:
        Allow staff to request patient deletion (owners must approve).

    PERMISSIONS:
        @login_required: Must be logged in
        Staff only: Owners/dentists can delete directly (see delete_patient)

    URL PARAMETERS:
        patient_id (int): ID of patient to request deletion for

    METHOD:
        POST only

    HOW IT WORKS:
        1. Check if user is staff (only staff can request)
        2. Check if pending request already exists for this patient
        3. If exists: Show warning
        4. If not: Create pending request, log activity, show confirmation

    WORKFLOW:
        1. Staff clicks "Request Delete" button
        2. Pending request created in database (status='pending')
        3. Owner sees request in pending_requests page
        4. Owner approves/denies request
        5. If approved: Patient deleted by owner

    EXAMPLE URL:
        POST /patients/request_delete/5 → Request deletion of patient ID 5

    RETURNS:
        Redirect to patients list with confirmation or warning message
    """
    # Check if user is staff (only staff use request workflow)
    if not current_user.is_staff():
        flash("Only staff members can request deletions.", "danger")
        return redirect(url_for('patients'))

    with get_db_connection() as conn:
        # Check if pending request already exists for this patient
        existing = conn.execute(
            "SELECT id FROM pending_requests WHERE patient_id = ? AND status = 'pending'",
            (patient_id,)
        ).fetchone()

        if existing:
            # Request already exists - don't create duplicate
            flash("A deletion request for this patient already exists.", "warning")
            return redirect(url_for('patients'))

        # Create new pending request
        conn.execute(
            "INSERT INTO pending_requests (patient_id, requested_by) VALUES (?, ?)",
            (patient_id, current_user.id)
        )
        conn.commit()

    # Log activity
    log_activity(current_user.id, current_user.username, "REQUEST_DELETE",
                f"Requested deletion for patient ID {patient_id}")

    # Show confirmation message
    flash("Deletion request sent for approval.", "info")

    # Redirect to patients list
    return redirect(url_for('patients'))


# ==============================================================================
# PENDING REQUESTS ROUTES (Owner Only)
# ==============================================================================
# Routes for viewing and approving/denying patient deletion requests.
# Only owners can access these routes.
# ==============================================================================

@app.route("/pending_requests")
@login_required
@owner_required
def pending_requests_view():
    """
    View all pending deletion requests (owner only).

    PURPOSE:
        Display all pending patient deletion requests for owner approval.

    PERMISSIONS:
        @login_required: Must be logged in
        @owner_required: Only managers can view pending requests

    QUERY PARAMETERS:
        search (str): Search by patient name or request ID

    HOW IT WORKS:
        1. Fetch all pending deletion requests from database
        2. If search provided: Filter requests by patient name or ID
        3. Render pending_requests.html with filtered list

    DISPLAY:
        Each request shows:
        - Request ID
        - Patient name
        - Who requested deletion (username)
        - When requested (timestamp)
        - Actions: Approve / Deny buttons

    EXAMPLE URLS:
        /pending_requests → All pending requests
        /pending_requests?search=john → Requests for patients with "john" in name

    RETURNS:
        Rendered pending_requests.html with:
        - requests (list[dict]): Pending deletion requests
        - search (str): Current search query
    """
    # Get search query parameter
    search = request.args.get("search", "")

    # Fetch all pending deletion requests
    requests_list = PendingRequest.get_all_pending()

    # Apply search filter if provided
    if search:
        filtered_requests = []
        for req in requests_list:
            # Search in patient first name, last name, or request ID
            if (search.lower() in req['first_name'].lower() or
                search.lower() in req['last_name'].lower() or
                search in str(req['id'])):
                filtered_requests.append(req)
        requests_list = filtered_requests

    # Render template with filtered requests
    return render_template("pending_requests.html", requests=requests_list, search=search)


@app.route("/pending_requests/approve/<int:request_id>", methods=["POST"])
@login_required
@owner_required
def approve_request(request_id):
    """
    Approve deletion request and delete patient (owner only).

    PURPOSE:
        Owner approves deletion request and patient is permanently deleted.

    PERMISSIONS:
        @login_required: Must be logged in
        @owner_required: Only owners can approve deletions

    URL PARAMETERS:
        request_id (int): ID of pending request to approve

    METHOD:
        POST only

    HOW IT WORKS:
        1. Mark request as approved in pending_requests table
        2. Get patient ID from request
        3. Delete patient record from database
        4. Log activity
        5. Show success message
        6. Redirect to pending requests page

    WORKFLOW:
        1. Staff requests deletion → pending_requests table (status='pending')
        2. Owner clicks "Approve" → This route
        3. Request status updated to 'approved'
        4. Patient deleted from patients table
        5. Request remains in database for audit trail

    EXAMPLE URL:
        POST /pending_requests/approve/7 → Approve request ID 7

    RETURNS:
        Redirect to pending_requests_view with success message
    """
    # Mark request as approved (updates status and records who approved)
    PendingRequest.approve(request_id, current_user.id)

    with get_db_connection() as conn:
        # Get patient ID from the request
        row = conn.execute("SELECT patient_id FROM pending_requests WHERE id = ?", (request_id,)).fetchone()

        if row:
            patient_id = row["patient_id"]

            # Delete patient record
            conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
            conn.commit()

            # Log activity
            log_activity(current_user.id, current_user.username, "APPROVE_DELETE",
                         f"Approved deletion for patient ID {patient_id}")

    # Show success message
    flash("Deletion request approved and patient record removed.", "success")

    # Redirect back to pending requests page
    return redirect(url_for("pending_requests_view"))


@app.route("/pending_requests/deny/<int:request_id>", methods=["POST"])
@login_required
@owner_required
def deny_request(request_id):
    """
    Deny deletion request (owner only).

    PURPOSE:
        Owner denies deletion request - patient record remains in database.

    PERMISSIONS:
        @login_required: Must be logged in
        @owner_required: Only owners can deny deletions

    URL PARAMETERS:
        request_id (int): ID of pending request to deny

    METHOD:
        POST only

    HOW IT WORKS:
        1. Mark request as denied in pending_requests table
        2. Log activity
        3. Show info message
        4. Redirect to pending requests page

    OUTCOME:
        - Request status changed to 'denied'
        - Patient record remains in database (not deleted)
        - Request remains in database for audit trail

    EXAMPLE URL:
        POST /pending_requests/deny/7 → Deny request ID 7

    RETURNS:
        Redirect to pending_requests_view with info message
    """
    # Mark request as denied
    PendingRequest.deny(request_id, current_user.id)

    # Log activity
    log_activity(current_user.id, current_user.username, "DENY_DELETE", f"Denied deletion request ID {request_id}")

    # Show info message
    flash("Deletion request denied.", "info")

    # Redirect back to pending requests page
    return redirect(url_for("pending_requests_view"))


# ==============================================================================
# STAFF MANAGEMENT ROUTES (Owner Only)
# ==============================================================================
# CRUD operations for staff accounts: List, Add, Edit, Delete.
# Only owners can access these routes.
# ==============================================================================

@app.route("/staff")
@login_required
@owner_required
def staff():
    """
    Staff list page with search and filter (owner only).

    PURPOSE:
        Display all staff members in a table with search and status filter.

    PERMISSIONS:
        @login_required: Must be logged in
        @owner_required: Only owners can view staff list

    QUERY PARAMETERS:
        - search (str): Search by name, username, or staff ID
        - status (str): Filter by status ('active' or 'inactive')

    HOW IT WORKS:
        1. Get search and filter parameters from URL
        2. Build SQL query dynamically based on filters
        3. Execute query and fetch all matching staff
        4. Render staff.html with staff list

    EXAMPLE URLS:
        /staff → All staff
        /staff?search=john → Staff with "john" in name/username/ID
        /staff?status=active → Active staff only
        /staff?search=john&status=active → Active staff with "john" in name

    RETURNS:
        Rendered staff.html template with:
        - staff_list (list[dict]): Staff records
        - search (str): Current search query
        - status (str): Current status filter
    """
    # Get query parameters
    search = request.args.get("search", "")
    status = request.args.get("status", "")

    with get_db_connection() as conn:
        # Build dynamic SQL query
        query = "SELECT * FROM users WHERE role='staff'"  # Base query: only staff role
        params = []

        # Add search filter if provided
        if search:
            # Search in full_name, username, or ID
            query += " AND (full_name LIKE ? OR username LIKE ? OR CAST(id AS TEXT) LIKE ?)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])

        # Add status filter if provided
        if status == "active":
            query += " AND is_active = 1"
        elif status == "inactive":
            query += " AND is_active = 0"

        # Order by ID descending (newest first)
        query += " ORDER BY id DESC"

        # Execute query
        staff_list = conn.execute(query, params).fetchall()

    # Convert to list of dictionaries
    staff_list = [dict(s) for s in staff_list]

    # Render template
    return render_template("staff.html", staff_list=staff_list, search=search, status=status)


@app.route("/add_staff", methods=["GET", "POST"])
@login_required
@owner_required
def add_staff():
    """
    Add new staff member (owner only).

    PURPOSE:
        Display form to add new staff account (GET) and process submission (POST).

    PERMISSIONS:
        @login_required: Must be logged in
        @owner_required: Only owners can add staff

    METHODS:
        GET: Display add_staff.html form
        POST: Create new staff account

    FORM FIELDS:
        - username (str) *required* *unique*
        - password (str) *required*
        - full_name (str)
        - email (str)

    HOW IT WORKS:
        POST request:
        1. Get form data
        2. Call User.create_user() to create account (password is hashed)
        3. If success: Log activity, show success message, redirect to staff list
        4. If failure (username exists): Show error message

    SECURITY:
        - Password automatically hashed before storing
        - Username uniqueness enforced by database UNIQUE constraint
        - Activity logged for audit trail

    RETURNS:
        GET: Rendered add_staff.html form
        POST (success): Redirect to staff list with success message
        POST (username exists): Re-display form with error message
    """
    if request.method == "POST":
        # Get form data
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        full_name = request.form.get("full_name", "")
        email = request.form.get("email", "")
        role = "staff"  # Always create as staff role

        # Create user account (password is hashed inside User.create_user)
        created = User.create_user(username, password, role, full_name, email)

        if created:
            # Success - log activity and show message
            log_activity(current_user.id, current_user.username, "ADD_STAFF",
                         f"Added staff {full_name} ({username})")
            flash("Staff member added successfully!", "success")
            return redirect(url_for("staff"))
        else:
            # Failure - username already exists
            flash("Username already exists!", "danger")

    # GET request or POST with error: Display form
    return render_template("add_staff.html")


@app.route("/edit_staff/<int:staff_id>", methods=["GET", "POST"])
@login_required
@owner_required
def edit_staff(staff_id):
    """
    Edit staff member (owner only).

    PURPOSE:
        Display form to edit staff account (GET) and process updates (POST).

    PERMISSIONS:
        @login_required: Must be logged in
        @owner_required: Only owners can edit staff

    URL PARAMETERS:
        staff_id (int): ID of staff to edit

    METHODS:
        GET: Display edit_staff.html form with current staff data
        POST: Update staff account in database

    FORM FIELDS:
        - full_name (str)
        - email (str)
        - is_active (checkbox): 1 if checked, 0 if not
        - new_password (str): Optional - only update if provided

    HOW IT WORKS:
        POST request:
        1. Get form data
        2. Check if new password provided
        3. If yes: Update full_name, email, is_active, AND password_hash
        4. If no: Update full_name, email, is_active only
        5. Log activity, show success, redirect to staff list

    PASSWORD UPDATE:
        - New password is optional
        - If provided: Hash and update password_hash
        - If empty: Keep existing password unchanged

    EXAMPLE URL:
        /edit_staff/3 → Edit staff with ID 3

    RETURNS:
        GET: Rendered edit_staff.html with staff data
        POST (success): Redirect to staff list with success message
        POST (staff not found): Redirect to staff list with error message
    """
    with get_db_connection() as conn:
        # Query staff member
        staff = conn.execute("SELECT * FROM users WHERE id = ? AND role='staff'", (staff_id,)).fetchone()

        if not staff:
            flash("Staff member not found.", "danger")
            return redirect(url_for("staff"))

        if request.method == "POST":
            # Get form data
            full_name = request.form.get("full_name", "")
            email = request.form.get("email", "")
            # Checkbox: Present in form if checked, absent if not checked
            is_active = 1 if 'is_active' in request.form else 0
            new_password = request.form.get("new_password", "")

            # Check if password update requested
            if new_password:
                # Update with new password
                password_hash = generate_password_hash(new_password)
                conn.execute(
                    "UPDATE users SET full_name=?, email=?, is_active=?, password_hash=? WHERE id=?",
                    (full_name, email, is_active, password_hash, staff_id)
                )
            else:
                # Update without changing password
                conn.execute(
                    "UPDATE users SET full_name=?, email=?, is_active=? WHERE id=?",
                    (full_name, email, is_active, staff_id)
                )

            # Save changes
            conn.commit()

            # Log activity
            log_activity(current_user.id, current_user.username, "EDIT_STAFF",
                         f"Edited staff {full_name} (ID {staff_id})")

            # Show success message
            flash("Staff member updated!", "success")

            # Redirect to staff list
            return redirect(url_for("staff"))

    # GET request: Convert staff to dict for template
    staff = dict(staff)
    return render_template("edit_staff.html", staff=staff)


@app.route("/staff/delete/<int:staff_id>", methods=["POST"])
@login_required
@owner_required
def delete_staff(staff_id):
    """
    Delete staff member (owner only).

    PURPOSE:
        Permanently delete a staff account from database.

    PERMISSIONS:
        @login_required: Must be logged in
        @owner_required: Only owners can delete staff

    URL PARAMETERS:
        staff_id (int): ID of staff to delete

    METHOD:
        POST only (prevents accidental deletion via URL)

    HOW IT WORKS:
        1. Query staff member from database
        2. If not found: Show error
        3. If found: Delete record, log activity, show success
        4. Redirect to staff list

    SECURITY:
        - POST-only route (prevents CSRF via GET)
        - Owner-only access
        - Activity logged for audit trail
        - CSRF token required

    EXAMPLE URL:
        POST /staff/delete/3 → Delete staff with ID 3

    RETURNS:
        Redirect to staff list with success or error message
    """
    with get_db_connection() as conn:
        # Check if staff exists
        staff = conn.execute("SELECT * FROM users WHERE id=? AND role='staff'", (staff_id,)).fetchone()

        if not staff:
            flash("Staff member not found.", "danger")
        else:
            # Delete staff record
            conn.execute("DELETE FROM users WHERE id=?", (staff_id,))
            conn.commit()

            # Log activity
            log_activity(current_user.id, current_user.username, "DELETE_STAFF", f"Deleted staff ID {staff_id}")

            # Show success message
            flash("Staff member deleted.", "success")

    # Redirect to staff list
    return redirect(url_for("staff"))


# ==============================================================================
# PROFILE MANAGEMENT ROUTE
# ==============================================================================
# Route for users to view and update their own profile.
# ==============================================================================

@app.route("/my_profile", methods=["GET", "POST"])
@login_required
def my_profile():
    """
    User profile page - view and edit own profile.

    PURPOSE:
        Allow users to update their own profile information and password.

    PERMISSIONS:
        @login_required: All authenticated users can edit their own profile

    METHODS:
        GET: Display my_profile.html with current user data
        POST: Update user profile and optionally password

    FORM FIELDS:
        - full_name (str): Display name
        - email (str): Email address
        - current_password (str): Required if changing password
        - new_password (str): New password (optional)

    PASSWORD CHANGE WORKFLOW:
        1. User provides current_password and new_password
        2. Verify current_password is correct
        3. If correct: Hash new_password and update
        4. If incorrect: Show error, don't update

    HOW IT WORKS:
        POST request:
        1. Get form data
        2. Check if password change requested
        3. If yes: Verify current password, then update all fields including password
        4. If no: Update only full_name and email
        5. Log activity, show success, redirect

    SECURITY:
        - Current password required to change password
        - Password hashing before storage
        - Activity logged for audit trail

    RETURNS:
        GET: Rendered my_profile.html with current user data
        POST (success): Redirect to my_profile with success message
        POST (wrong password): Redirect to my_profile with error message
    """
    if request.method == "POST":
        # Get form data
        full_name = request.form.get("full_name", "")
        email = request.form.get("email", "")
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")

        with get_db_connection() as conn:
            # Check if password change requested (both fields filled)
            if new_password and current_password:
                # Verify current password is correct
                if current_user.verify_password(current_password):
                    # Current password correct - hash new password and update
                    password_hash = generate_password_hash(new_password)
                    conn.execute(
                        "UPDATE users SET full_name=?, email=?, password_hash=? WHERE id=?",
                        (full_name, email, password_hash, current_user.id)
                    )
                    conn.commit()

                    # Log activity
                    log_activity(current_user.id, current_user.username, "UPDATE_PROFILE",
                                "Updated profile and password")

                    # Show success message
                    flash("Profile and password updated successfully!", "success")
                else:
                    # Current password incorrect - show error
                    flash("Current password is incorrect.", "danger")
                    return redirect(url_for("my_profile"))
            else:
                # No password change - update only full_name and email
                conn.execute(
                    "UPDATE users SET full_name=?, email=? WHERE id=?",
                    (full_name, email, current_user.id)
                )
                conn.commit()

                # Log activity
                log_activity(current_user.id, current_user.username, "UPDATE_PROFILE",
                            "Updated profile")

                # Show success message
                flash("Profile updated successfully!", "success")

        # Update current_user object with new values (for display in template)
        current_user.full_name = full_name
        current_user.email = email

        # Redirect to profile page
        return redirect(url_for("my_profile"))

    # GET request: Display profile form
    return render_template("my_profile.html")


# ==============================================================================
# AUDIT LOGS ROUTE
# ==============================================================================
# Route to view activity logs (audit trail).
# ==============================================================================

@app.route("/audit_logs")
@login_required
def audit_logs():
    """
    Audit logs page - view activity history.

    PURPOSE:
        Display activity logs (audit trail) for security and compliance.

    PERMISSIONS:
        @login_required: All authenticated users can view logs
        Access level:
        - Owners: See all logs (all users' activities)
        - Other roles: See only their own logs

    HOW IT WORKS:
        1. Check if current user is owner
        2. If owner: Query all logs (last 100)
        3. If not: Query only logs for current user (last 100)
        4. Render audit_logs.html with log entries

    LOG ENTRIES:
        Each log shows:
        - username: Who performed the action
        - action_type: What action was performed (LOGIN, ADD_PATIENT, etc.)
        - details: Additional information about the action
        - timestamp: When the action occurred

    WHY LIMIT TO 100:
        - Performance: Don't load too many records at once
        - Usability: 100 recent entries is usually sufficient
        - Future enhancement: Add pagination for viewing older logs

    RETURNS:
        Rendered audit_logs.html template with:
        - logs (list[dict]): Activity log entries
    """
    with get_db_connection() as conn:
        # Check user role to determine which logs to show
        if current_user.is_owner():
            # Owners see all logs
            logs = conn.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 100").fetchall()
        else:
            # Other users see only their own logs
            logs = conn.execute(
                "SELECT * FROM audit_logs WHERE user_id=? ORDER BY timestamp DESC LIMIT 100",
                (current_user.id,)
            ).fetchall()

    # Convert to list of dictionaries
    logs = [dict(l) for l in logs]

    # Render template
    return render_template("audit_logs.html", logs=logs)


# ==============================================================================
# BACKUP AND RESTORE ROUTES (Owner Only)
# ==============================================================================
# Routes for database backup, restore, and download.
# Only owners can access these routes.
# ==============================================================================

@app.route("/backup")
@login_required
@owner_required
def backup():
    """
    Backup management page (owner only).

    PURPOSE:
        Display list of available backups with options to create, download, or restore.

    PERMISSIONS:
        @login_required: Must be logged in
        @owner_required: Only owners can manage backups

    HOW IT WORKS:
        1. Ensure backup folder exists
        2. Get list of all backup files
        3. Render backup.html with backup list

    DISPLAY:
        Each backup shows:
        - filename: backup_YYYYMMDD_HHMMSS.db
        - created: Human-readable creation time
        - size: File size in bytes
        - Actions: Download, Restore buttons

    ERROR HANDLING:
        If backup folder cannot be created or read:
        - Show error message
        - Redirect to dashboard

    RETURNS:
        Rendered backup.html template with:
        - backups (list[dict]): Available backup files
    """
    try:
        # Ensure backup folder exists
        os.makedirs(Config.BACKUP_FOLDER, exist_ok=True)

        # Get list of backup files
        backups = get_backup_files()

        # Render template
        return render_template("backup.html", backups=backups)

    except Exception as e:
        # Error accessing backup folder - show error and redirect
        flash(f"⚠️ Failed to load backups: {e}", "danger")
        return redirect(url_for("dashboard"))


@app.route("/create_backup", methods=["POST"])
@login_required
@owner_required
def create_backup():
    """
    Create database backup (owner only).

    PURPOSE:
        Create a timestamped backup of the current database.

    PERMISSIONS:
        @login_required: Must be logged in
        @owner_required: Only owners can create backups

    METHOD:
        POST only

    HOW IT WORKS:
        1. Ensure backup folder exists
        2. Call backup_database() to create backup file
        3. Log activity
        4. Show success message
        5. Redirect to backup page

    BACKUP FILE FORMAT:
        backup_YYYYMMDD_HHMMSS.db
        Example: backup_20251105_143022.db

    ERROR HANDLING:
        If backup creation fails:
        - Show error message
        - Redirect to backup page

    RETURNS:
        Redirect to backup page with success or error message
    """
    try:
        # Ensure backup folder exists
        os.makedirs(Config.BACKUP_FOLDER, exist_ok=True)

        # Create backup (returns filename)
        backup_filename = backup_database()

        # Log activity
        log_activity(current_user.id, current_user.username, "BACKUP", f"Created backup {backup_filename}")

        # Show success message
        flash("Backup created successfully!", "success")

    except Exception as e:
        # Backup creation failed - show error
        flash(f"Failed to create backup: {e}", "danger")

    # Redirect to backup page
    return redirect(url_for("backup"))


@app.route("/backup/download/<path:filename>")
@login_required
@owner_required
def download_backup(filename):
    """
    Download backup file (owner only).

    PURPOSE:
        Send backup file to user's browser for download.

    PERMISSIONS:
        @login_required: Must be logged in
        @owner_required: Only owners can download backups

    URL PARAMETERS:
        filename (path): Name of backup file to download

    HOW IT WORKS:
        1. Safely join backup folder path with filename (prevents directory traversal)
        2. Check if file exists
        3. If exists: Send file to browser with "Save As" dialog
        4. If not: Show error and redirect

    SECURITY:
        - safe_join() prevents directory traversal attacks
          (e.g., filename="../../../etc/passwd" is blocked)
        - Owner-only access
        - File existence check

    EXAMPLE URL:
        /backup/download/backup_20251105_143022.db

    RETURNS:
        If file exists: File download
        If file not found: Redirect to backup page with error message
    """
    try:
        # Safely construct file path (prevents directory traversal)
        backup_path = safe_join(Config.BACKUP_FOLDER, filename)

        # Check if file exists and path is valid
        if not backup_path or not os.path.exists(backup_path):
            flash("Backup file not found.", "danger")
            return redirect(url_for("backup"))

        # Send file to browser for download
        return send_file(
            os.path.abspath(backup_path),  # Absolute path to file
            as_attachment=True,            # Force "Save As" dialog
            download_name=filename,        # Filename shown in browser
            mimetype="application/octet-stream"  # Generic binary file type
        )

    except Exception as e:
        # Error during download - show error and redirect
        flash(f"⚠️ Error while downloading backup: {e}", "danger")
        return redirect(url_for("backup"))


@app.route("/backup/restore/<path:filename>", methods=["POST"])
@login_required
@owner_required
def restore_backup(filename):
    """
    Restore database from backup (owner only).

    PURPOSE:
        Replace current database with a backup file.

    PERMISSIONS:
        @login_required: Must be logged in
        @owner_required: Only owners can restore backups

    URL PARAMETERS:
        filename (path): Name of backup file to restore

    METHOD:
        POST only (prevents accidental restore via URL)

    HOW IT WORKS:
        1. Safely construct file path
        2. Check if file exists
        3. If exists: Copy backup over current database
        4. Log activity
        5. Show success message
        6. Redirect to backup page

    WARNING:
        - This OVERWRITES the current database!
        - All data since backup will be lost
        - Should prompt user for confirmation before calling this route

    SECURITY:
        - safe_join() prevents directory traversal
        - POST-only route
        - Owner-only access
        - Activity logged

    EXAMPLE URL:
        POST /backup/restore/backup_20251105_143022.db

    RETURNS:
        Redirect to backup page with success or error message
    """
    try:
        # Safely construct file path
        backup_path = safe_join(Config.BACKUP_FOLDER, filename)

        # Check if file exists
        if not backup_path or not os.path.exists(backup_path):
            flash("Backup file not found.", "danger")
            return redirect(url_for("backup"))

        # Restore database from backup (copies backup over current database)
        restore_database(filename)

        # Log activity
        log_activity(current_user.id, current_user.username, "RESTORE", f"Restored backup {filename}")

        # Show success message
        flash("Database successfully restored from backup!", "success")

    except Exception as e:
        # Restore failed - show error
        flash(f"Failed to restore backup: {e}", "danger")

    # Redirect to backup page
    return redirect(url_for("backup"))


# ==============================================================================
# SETTINGS ROUTE
# ==============================================================================
# Route for user settings (currently similar to profile page).
# ==============================================================================

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """
    Settings page - user preferences and account settings.

    PURPOSE:
        Allow users to update their account settings.
        Currently similar to my_profile route (potential for future differentiation).

    PERMISSIONS:
        @login_required: All authenticated users can access settings

    METHODS:
        GET: Display settings.html form
        POST: Update user settings

    FORM FIELDS:
        - full_name (str): Display name
        - current_password (str): Required if changing password
        - new_password (str): New password (optional)

    NOTE:
        This route is similar to my_profile.
        Future enhancements could include:
        - Email notifications preferences
        - UI theme selection
        - Language preferences
        - Dashboard customization

    RETURNS:
        GET: Rendered settings.html with current user data
        POST (success): Redirect to dashboard with success message
        POST (wrong password): Redirect to settings with error message
    """
    if request.method == "POST":
        # Get form data
        full_name = request.form.get("full_name", "")
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")

        with get_db_connection() as conn:
            # Check if password change requested
            if new_password and current_password:
                # Verify current password
                if current_user.verify_password(current_password):
                    # Password correct - update with new password
                    password_hash = generate_password_hash(new_password)
                    conn.execute(
                        "UPDATE users SET full_name=?, password_hash=? WHERE id=?",
                        (full_name, password_hash, current_user.id)
                    )
                    conn.commit()

                    # Show success message
                    flash("Settings and password updated successfully!", "success")
                else:
                    # Password incorrect - show error
                    flash("Current password is incorrect.", "danger")
                    return redirect(url_for("settings"))
            else:
                # No password change - update only full_name
                conn.execute(
                    "UPDATE users SET full_name=? WHERE id=?",
                    (full_name, current_user.id)
                )
                conn.commit()

                # Show success message
                flash("Settings updated successfully!", "success")

        # Update current_user object
        current_user.full_name = full_name

        # Redirect to dashboard
        return redirect(url_for("dashboard"))

    # GET request: Display settings form
    return render_template("settings.html")


# ==============================================================================
# APPLICATION ENTRY POINT
# ==============================================================================
# This runs only when script is executed directly (not imported as module).
# ==============================================================================

if __name__ == "__main__":
    """
    Run Flask development server.

    CONFIGURATION:
        - host='0.0.0.0': Listen on all network interfaces (accessible from other devices)
        - port=5000: HTTP port to listen on
        - debug=True: Enable debug mode (auto-reload, detailed errors)

    DEBUG MODE WARNING:
        Debug mode should NEVER be used in production!
        - Exposes sensitive information in error pages
        - Allows code execution from error console
        - Auto-reloads on code changes (performance impact)

    FOR PRODUCTION:
        Use a production WSGI server like Gunicorn or uWSGI:
        $ gunicorn -w 4 app:app

    FOR DEVELOPMENT:
        Simply run this script:
        $ python app.py
        or
        $ flask run
    """
    app.run(host='0.0.0.0', port=5000, debug=True)


# ==============================================================================
# MODULE SUMMARY
# ==============================================================================
"""
ROUTES PROVIDED:

AUTHENTICATION:
    GET  /                          → Redirect to login
    GET  /login                     → Display login form
    POST /login                     → Process login
    GET  /logout                    → Log out user

DASHBOARD:
    GET  /dashboard                 → Show overview and statistics

PATIENT MANAGEMENT:
    GET  /patients                  → List all patients (with search/filter)
    GET  /patients/add              → Display add patient form
    POST /patients/add              → Create new patient
    GET  /patients/view/<id>        → View patient details
    GET  /patients/edit/<id>        → Display edit patient form
    POST /patients/edit/<id>        → Update patient
    POST /patients/delete/<id>      → Delete patient (owners/dentists only)
    POST /patients/request_delete/<id> → Request deletion (staff only)

PENDING REQUESTS (Owner Only):
    GET  /pending_requests          → List pending deletion requests
    POST /pending_requests/approve/<id> → Approve and delete patient
    POST /pending_requests/deny/<id>    → Deny deletion request

STAFF MANAGEMENT (Owner Only):
    GET  /staff                     → List all staff (with search/filter)
    GET  /add_staff                 → Display add staff form
    POST /add_staff                 → Create new staff account
    GET  /edit_staff/<id>           → Display edit staff form
    POST /edit_staff/<id>           → Update staff account
    POST /staff/delete/<id>         → Delete staff account

PROFILE & SETTINGS:
    GET  /my_profile                → Display user profile
    POST /my_profile                → Update user profile
    GET  /settings                  → Display settings
    POST /settings                  → Update settings

AUDIT LOGS:
    GET  /audit_logs                → View activity logs

BACKUP & RESTORE (Owner Only):
    GET  /backup                    → List backups
    POST /create_backup             → Create new backup
    GET  /backup/download/<filename> → Download backup file
    POST /backup/restore/<filename>  → Restore from backup

SECURITY FEATURES:
    - CSRF protection on all POST requests
    - Password hashing (PBKDF2-SHA256)
    - SQL injection prevention (parameterized queries)
    - Role-based access control (decorators)
    - Activity logging (audit trail)
    - Session management (Flask-Login)

DESIGN PATTERNS:
    - MVC architecture (Model-View-Controller)
    - RESTful routes (/resource/action/<id>)
    - Decorator pattern (authorization)
    - Template inheritance (Jinja2)
    - Flash messages (user feedback)

ROLE PERMISSIONS:
    Owner:
        - Full access to all features
        - Manage staff accounts
        - Approve/deny deletion requests
        - Create/restore backups
        - View all audit logs

    Dentist:
        - Manage patients (add/edit/view/delete)
        - Edit medical information
        - View pending requests
        - View own audit logs

    Staff:
        - Manage patients (add/edit/view)
        - Cannot edit medical information
        - Request patient deletion (requires owner approval)
        - View own audit logs
"""
