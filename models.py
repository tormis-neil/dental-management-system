"""
Database Models Module for Dental Clinic Management System

PURPOSE:
    This file defines the database structure and provides data access methods.
    It's the "Model" layer in the MVC (Model-View-Controller) architecture.
    All database interactions happen through this file.

WHAT IT CONTAINS:
    1. Database Connection: Function to connect to SQLite database
    2. Database Schema: Table definitions for users, patients, audit_logs, pending_requests
    3. User Class: Handles authentication, authorization, and user operations
    4. PendingRequest Class: Manages deletion approval workflow
    5. Initialization: Creates tables and default owner account on startup

WHY THIS APPROACH:
    - Separation of Concerns: Database logic separate from business logic (app.py)
    - Reusability: Methods can be called from anywhere in the application
    - Security: Centralized password hashing and validation
    - Type Safety: Type hints (int, str, Optional) improve code quality
    - Context Managers: Automatic database connection cleanup

DEPENDENCIES:
    - sqlite3: Python's built-in SQLite database library
    - flask_login.UserMixin: Provides user session management methods
    - werkzeug.security: For secure password hashing (PBKDF2-SHA256)
    - typing: For type hints (Optional, annotations)

DATABASE SCHEMA:
    - users: Staff accounts (owner, dentist, staff)
    - patients: Patient information and medical records
    - audit_logs: Activity tracking for compliance and security
    - pending_requests: Deletion approval workflow (staff requests, owner approves)
"""

# ==============================================================================
# IMPORTS
# ==============================================================================

from __future__ import annotations  # Allows class to reference itself in type hints
import sqlite3  # SQLite database engine
from typing import Optional  # For nullable type hints (Optional[str] = str or None)
from flask_login import UserMixin  # Provides user session management
from werkzeug.security import generate_password_hash, check_password_hash  # Password security

from config import Config  # Application configuration (database name)


# ==============================================================================
# DATABASE CONNECTION
# ==============================================================================

def get_db_connection() -> sqlite3.Connection:
    """
    Create and configure a connection to the SQLite database.

    PURPOSE:
        Provides a database connection with proper configuration.
        Used throughout the application for all database operations.

    HOW IT WORKS:
        1. Opens connection to database file specified in Config.DATABASE_NAME
        2. Sets row_factory to sqlite3.Row for dict-like access to rows
        3. Returns configured connection object

    ROW_FACTORY EXPLANATION:
        Without row_factory:
            row = cursor.fetchone()
            username = row[1]  # Access by index (error-prone)

        With row_factory = sqlite3.Row:
            row = cursor.fetchone()
            username = row["username"]  # Access by column name (readable)

    RETURNS:
        sqlite3.Connection: Configured database connection

    USAGE:
        # With context manager (automatically closes connection)
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM users")
            # Connection automatically closed after this block

    TECHNICAL DETAILS:
        - Connection is NOT thread-safe (SQLite limitation)
        - Each request should use its own connection
        - Context manager ensures connection is closed even if error occurs
    """
    # Connect to SQLite database file
    conn = sqlite3.connect(Config.DATABASE_NAME)

    # Enable dictionary-like row access (row["column_name"])
    conn.row_factory = sqlite3.Row

    return conn


# ==============================================================================
# DATABASE INITIALIZATION
# ==============================================================================

def init_db() -> None:
    """
    Initialize the database by creating all required tables if they don't exist.

    PURPOSE:
        Creates database schema on first run of the application.
        Safe to call multiple times (IF NOT EXISTS prevents errors).

    HOW IT WORKS:
        1. Opens database connection using context manager
        2. Executes SQL script that creates 4 tables
        3. Commits transaction to save changes permanently
        4. Connection automatically closes after 'with' block

    TABLES CREATED:
        1. users: Staff accounts with authentication
        2. patients: Patient records and medical information
        3. audit_logs: Activity tracking for compliance
        4. pending_requests: Deletion approval workflow

    WHY executescript():
        - Allows multiple SQL statements in one call
        - Automatically handles transaction management
        - Cleaner than calling execute() multiple times

    RETURNS:
        None: No return value (creates database as side effect)

    CALLED BY:
        This function is automatically called at module import (line 227)
    """
    with get_db_connection() as conn:
        # executescript runs multiple SQL statements separated by semicolons
        conn.executescript("""
        -- =====================================================================
        -- USERS TABLE: Staff accounts with role-based access control
        -- =====================================================================
        CREATE TABLE IF NOT EXISTS users (
            -- Primary key: Auto-incrementing unique identifier
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Username must be unique (enforced by UNIQUE constraint)
            username TEXT UNIQUE NOT NULL,

            -- Stores hashed password (NEVER store plaintext passwords!)
            password_hash TEXT NOT NULL,

            -- Optional: User's full display name
            full_name TEXT,

            -- Optional: User's email address
            email TEXT,

            -- Role determines permissions: owner > dentist/staff
            -- CHECK constraint ensures only valid roles can be inserted
            role TEXT NOT NULL CHECK(role IN ('owner','staff','dentist','admin')),

            -- Soft delete flag: 0 = deactivated, 1 = active
            is_active INTEGER DEFAULT 1,

            -- Timestamp of account creation (automatically set)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- =====================================================================
        -- PATIENTS TABLE: Patient information and medical records
        -- =====================================================================
        CREATE TABLE IF NOT EXISTS patients (
            -- Primary key: Unique patient ID
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Required fields for patient identification
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,

            -- Personal information (optional but recommended)
            date_of_birth TEXT,  -- Format: YYYY-MM-DD
            gender TEXT,          -- e.g., Male, Female, Other
            phone TEXT,
            email TEXT,
            address TEXT,

            -- Emergency contact information
            emergency_contact_name TEXT,
            emergency_contact_phone TEXT,

            -- Medical information for treatment planning
            medical_history TEXT,   -- Past medical conditions, surgeries
            allergies TEXT,          -- Drug allergies, latex allergy, etc.
            existing_condition TEXT, -- Current medical conditions (diabetes, etc.)
            dentist_notes TEXT,      -- Clinical notes from dentist

            -- Metadata: Who created and who is treating this patient
            created_by INTEGER,      -- User ID who added this patient
            assigned_dentist TEXT,   -- Dentist assigned to this patient

            -- Timestamps for record tracking
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- =====================================================================
        -- AUDIT_LOGS TABLE: Activity tracking for security and compliance
        -- =====================================================================
        CREATE TABLE IF NOT EXISTS audit_logs (
            -- Primary key
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Who performed the action (references users.id)
            user_id INTEGER,

            -- Denormalized username for faster queries (trade-off: slight redundancy)
            username TEXT,

            -- Type of action performed (LOGIN, ADD_PATIENT, DELETE_STAFF, etc.)
            action_type TEXT,

            -- Additional details about the action
            details TEXT,

            -- When the action occurred
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- =====================================================================
        -- PENDING_REQUESTS TABLE: Deletion approval workflow
        -- =====================================================================
        -- PURPOSE: Staff can request patient deletion, but only owners can approve
        -- WORKFLOW: Staff → Request → Owner → Approve/Deny → Delete
        CREATE TABLE IF NOT EXISTS pending_requests (
            -- Primary key
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Which patient is being requested for deletion
            patient_id INTEGER NOT NULL,

            -- Which user (staff/dentist) requested the deletion
            requested_by INTEGER NOT NULL,

            -- Status: pending → approved/denied
            -- CHECK constraint ensures only valid statuses
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending','approved','denied')),

            -- When the request was created
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            -- Which owner approved/denied the request
            approved_by INTEGER,

            -- When the request was approved/denied
            approved_at TIMESTAMP,

            -- Foreign key constraints ensure referential integrity
            -- If patient is deleted, request is also deleted (CASCADE behavior optional)
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (requested_by) REFERENCES users(id)
        );
        """)

        # Save all changes to database permanently
        conn.commit()


# ==============================================================================
# USER CLASS: Authentication and Authorization
# ==============================================================================

class User(UserMixin):
    """
    User model representing a staff member with authentication capabilities.

    PURPOSE:
        Handles user authentication, authorization, and user-related operations.
        Integrates with Flask-Login for session management.

    INHERITS FROM:
        UserMixin: Provides default implementations for Flask-Login methods:
            - is_authenticated: Always True for logged-in users
            - is_active: Checks if account is active
            - is_anonymous: Always False for real users
            - get_id(): Returns user identifier as string

    ATTRIBUTES:
        id (int): Unique user identifier (primary key)
        username (str): Login username
        password_hash (str): Hashed password (NEVER stored in plaintext)
        role (str): User role (owner, dentist, staff, admin)
        full_name (Optional[str]): Display name
        email (Optional[str]): Email address
        is_active_flag (int): 1 = active, 0 = deactivated

    ROLES AND PERMISSIONS:
        - owner: Full access (add/edit/delete staff, approve deletions, backups)
        - dentist: Add/edit/view patients, request deletions
        - staff: Add/edit/view patients, request deletions
        - admin: Future use (currently unused)

    USAGE EXAMPLE:
        # Authenticate user
        user = User.get_by_username("owner")
        if user and user.verify_password("12345"):
            login_user(user)  # Start session

        # Check permissions
        if user.is_owner():
            # Allow access to staff management
            pass
    """

    def __init__(
        self,
        id: int,
        username: str,
        password_hash: str,
        role: str,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        is_active: int = 1
    ) -> None:
        """
        Initialize a User object with data from database.

        PARAMETERS:
            id: Unique user identifier from database
            username: Login username
            password_hash: Hashed password (never plaintext!)
            role: User role (owner/dentist/staff/admin)
            full_name: Optional display name
            email: Optional email address
            is_active: 1 if active, 0 if deactivated

        NOTE:
            This constructor is typically called by static methods (get_by_id, get_by_username)
            after fetching user data from database. You don't usually call this directly.
        """
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.full_name = full_name
        self.email = email
        self.is_active_flag = is_active  # Store as _flag to avoid naming conflict with property

    def get_id(self) -> str:
        """
        Return user ID as string (required by Flask-Login).

        PURPOSE:
            Flask-Login uses this method to store user ID in session cookie.
            Must return a string (not integer) for serialization.

        RETURNS:
            str: User ID converted to string

        WHY OVERRIDE:
            UserMixin provides a default implementation, but we override it
            for explicit clarity and to ensure correct behavior.
        """
        return str(self.id)

    @property
    def is_active(self) -> bool:
        """
        Check if user account is active (required by Flask-Login).

        PURPOSE:
            Flask-Login checks this property to determine if user can log in.
            Deactivated accounts (is_active=0) cannot log in.

        @property DECORATOR:
            Allows accessing like an attribute: user.is_active
            Instead of calling method: user.is_active()

        RETURNS:
            bool: True if active, False if deactivated

        USAGE:
            if current_user.is_active:
                # User can access the system
                pass
        """
        return bool(self.is_active_flag)

    # ==========================================================================
    # ROLE CHECKING METHODS
    # ==========================================================================
    # These methods check user role for authorization.
    # Used in decorators (utils.py) and templates to control access.
    # ==========================================================================

    def is_owner(self) -> bool:
        """
        Check if user has owner role.

        RETURNS:
            bool: True if role is 'owner', False otherwise

        USAGE:
            if current_user.is_owner():
                # Show staff management menu
                pass
        """
        return self.role == "owner"

    def is_staff(self) -> bool:
        """
        Check if user has staff role.

        RETURNS:
            bool: True if role is 'staff', False otherwise
        """
        return self.role == "staff"

    def is_dentist(self) -> bool:
        """
        Check if user has dentist role.

        RETURNS:
            bool: True if role is 'dentist', False otherwise
        """
        return self.role == "dentist"

    def is_admin(self) -> bool:
        """
        Check if user has admin role.

        NOTE:
            Admin role is currently unused in the application.
            Reserved for future features (system configuration, etc.)

        RETURNS:
            bool: True if role is 'admin', False otherwise
        """
        return self.role == "admin"

    def verify_password(self, password: str) -> bool:
        """
        Verify if provided password matches the stored hash.

        PURPOSE:
            Used during login to authenticate user.
            NEVER compare passwords directly - always use hashing!

        HOW IT WORKS:
            1. Takes plaintext password from login form
            2. Hashes it using same algorithm as stored hash
            3. Compares the two hashes (timing-attack safe)
            4. Returns True if match, False if not

        PARAMETERS:
            password (str): Plaintext password from user input

        RETURNS:
            bool: True if password is correct, False otherwise

        SECURITY NOTES:
            - Uses Werkzeug's check_password_hash (PBKDF2-SHA256)
            - Timing-attack resistant (takes same time whether correct or not)
            - Plaintext password never stored or logged

        USAGE:
            user = User.get_by_username("owner")
            if user and user.verify_password("12345"):
                # Password correct - log in user
                login_user(user)
            else:
                # Password incorrect - show error
                flash("Invalid credentials")
        """
        return check_password_hash(self.password_hash, password)

    # ==========================================================================
    # STATIC METHODS: Database operations that don't require a User instance
    # ==========================================================================

    @staticmethod
    def get_by_id(user_id: int) -> Optional["User"]:
        """
        Fetch user from database by ID.

        PURPOSE:
            Retrieve user object when you have their ID.
            Used by Flask-Login's user_loader to restore session.

        HOW IT WORKS:
            1. Query database for user with matching ID
            2. If found: Create User object with database data
            3. If not found: Return None

        PARAMETERS:
            user_id (int): User's unique identifier

        RETURNS:
            Optional[User]: User object if found, None if not found

        TYPE HINTS:
            Optional["User"] means: Returns User or None
            "User" in quotes because class isn't fully defined yet

        USAGE:
            # Flask-Login user_loader callback
            @login_manager.user_loader
            def load_user(user_id):
                return User.get_by_id(int(user_id))

        SQL INJECTION PREVENTION:
            Using parameterized query (?) instead of string formatting
            SAFE:   "WHERE id = ?", (user_id,)
            UNSAFE: f"WHERE id = {user_id}"
        """
        with get_db_connection() as conn:
            # Execute parameterized query (? prevents SQL injection)
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

        # If user found, create User object from database row
        if row:
            return User(
                int(row["id"]),
                str(row["username"]),
                str(row["password_hash"]),
                str(row["role"]),
                str(row["full_name"]) if row["full_name"] else None,  # Handle NULL values
                str(row["email"]) if row["email"] else None,          # Handle NULL values
                int(row["is_active"]),
            )

        # User not found
        return None

    @staticmethod
    def get_by_username(username: str) -> Optional["User"]:
        """
        Fetch user from database by username.

        PURPOSE:
            Retrieve user object during login process.
            Username is unique, so returns at most one user.

        HOW IT WORKS:
            Same as get_by_id(), but searches by username instead of ID.

        PARAMETERS:
            username (str): Login username to search for

        RETURNS:
            Optional[User]: User object if found, None if not found

        USAGE:
            # During login
            user = User.get_by_username(request.form["username"])
            if user and user.verify_password(request.form["password"]):
                login_user(user)
        """
        with get_db_connection() as conn:
            # Query by username (UNIQUE constraint ensures only one match)
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if row:
            return User(
                int(row["id"]),
                str(row["username"]),
                str(row["password_hash"]),
                str(row["role"]),
                str(row["full_name"]) if row["full_name"] else None,
                str(row["email"]) if row["email"] else None,
                int(row["is_active"]),
            )
        return None

    @staticmethod
    def create_user(username: str, password: str, role: str, full_name: str, email: str) -> bool:
        """
        Create a new user account in the database.

        PURPOSE:
            Add new staff members (managers create dentist/staff accounts).

        HOW IT WORKS:
            1. Hash the plaintext password using Werkzeug's generate_password_hash
            2. Insert new row into users table with hashed password
            3. Commit transaction to save permanently
            4. Return True on success, False if username already exists

        PARAMETERS:
            username (str): Unique login username
            password (str): Plaintext password (will be hashed before storing)
            role (str): User role (owner, dentist, staff)
            full_name (str): Display name
            email (str): Email address

        RETURNS:
            bool: True if user created successfully, False if username already exists

        PASSWORD HASHING:
            - Uses PBKDF2-SHA256 algorithm (industry standard)
            - Automatically adds salt (random data to prevent rainbow tables)
            - Generates hash like: pbkdf2:sha256:260000$abc123$def456...
            - Same password + different salt = different hash (good for security)

        ERROR HANDLING:
            - sqlite3.IntegrityError raised if username already exists (UNIQUE constraint)
            - Caught and returns False instead of crashing

        USAGE:
            # In staff management route (owner only)
            success = User.create_user(
                username="john_dentist",
                password="secure_password",
                role="dentist",
                full_name="Dr. John Smith",
                email="john@example.com"
            )
            if success:
                flash("User created successfully")
            else:
                flash("Username already exists")
        """
        # Hash password before storing (NEVER store plaintext!)
        # generate_password_hash uses PBKDF2-SHA256 with 260,000 iterations
        password_hash = generate_password_hash(password)

        try:
            with get_db_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO users (username, password_hash, full_name, email, role)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (username, password_hash, full_name, email, role),
                )
                conn.commit()
            return True  # User created successfully
        except sqlite3.IntegrityError:
            # UNIQUE constraint violation - username already exists
            return False

    @staticmethod
    def get_users_by_ids(user_ids: list[int]) -> dict[int, str]:
        """
        Fetch multiple usernames by their IDs in a single query.

        PURPOSE:
            Efficient bulk lookup of usernames for display purposes.
            Used in audit log to show username instead of just user ID.

        WHY BULK QUERY:
            Bad approach (N queries):
                for user_id in user_ids:
                    username = User.get_by_id(user_id).username  # N database queries!

            Good approach (1 query):
                usernames = User.get_users_by_ids(user_ids)  # Single query

        HOW IT WORKS:
            1. Check if list is empty (return empty dict if so)
            2. Create SQL query with IN clause: WHERE id IN (?, ?, ?)
            3. Execute query with list of IDs
            4. Build dictionary mapping ID → username

        PARAMETERS:
            user_ids (list[int]): List of user IDs to fetch

        RETURNS:
            dict[int, str]: Dictionary mapping user ID to username
                           Example: {1: "owner", 2: "john_dentist", 3: "jane_staff"}

        TECHNICAL DETAILS:
            - Uses dynamic placeholders: ','.join('?' for _ in user_ids)
            - For [1, 2, 3] creates: "WHERE id IN (?, ?, ?)"
            - Dictionary comprehension: {row['id']: row['username'] for row in rows}

        USAGE:
            # Get usernames for audit log display
            user_ids = [1, 2, 3, 5, 7]
            username_map = User.get_users_by_ids(user_ids)
            # Result: {1: "owner", 2: "dentist1", 3: "staff1", ...}
        """
        # Handle empty list (return empty dict)
        if not user_ids:
            return {}

        # Create placeholders for SQL IN clause
        # [1, 2, 3] → "?, ?, ?" (three question marks)
        placeholders = ','.join('?' for _ in user_ids)

        # Build query with dynamic placeholders
        # Result: "SELECT id, username FROM users WHERE id IN (?, ?, ?)"
        query = f"SELECT id, username FROM users WHERE id IN ({placeholders})"

        with get_db_connection() as conn:
            # Execute query with list of IDs
            rows = conn.execute(query, user_ids).fetchall()

        # Convert list of rows to dictionary: {id: username}
        # Dictionary comprehension: iterate through rows and build dict
        return {row['id']: row['username'] for row in rows}


# ==============================================================================
# PENDING REQUEST CLASS: Deletion Approval Workflow
# ==============================================================================

class PendingRequest:
    """
    Manages the patient deletion approval workflow.

    PURPOSE:
        Implements two-step deletion process:
        1. Staff/Dentist requests deletion → Status: pending
        2. Owner approves/denies → Status: approved/denied
        3. If approved, patient is deleted from database

    WHY THIS APPROACH:
        - Security: Prevents accidental/malicious deletions
        - Audit Trail: Records who requested and who approved
        - Compliance: Many healthcare systems require approval workflows

    WORKFLOW:
        Staff clicks "Request Delete" → create(patient_id, staff_id)
        Owner sees pending request → approve(request_id, owner_id) OR deny(request_id, owner_id)
        If approved → app.py deletes patient and request record

    DESIGN PATTERN:
        Static methods only (no instance needed).
        This class is a namespace for related functions.
    """

    @staticmethod
    def create(patient_id: int, requested_by: int) -> None:
        """
        Create a new deletion request for a patient.

        PURPOSE:
            Staff/dentist can request patient deletion, but cannot delete directly.

        HOW IT WORKS:
            1. Insert new row into pending_requests table
            2. Set status to 'pending' (default value)
            3. Record timestamp (automatic via DEFAULT CURRENT_TIMESTAMP)

        PARAMETERS:
            patient_id (int): Which patient to delete
            requested_by (int): User ID of staff/dentist making request

        RETURNS:
            None: No return value (creates database record as side effect)

        USAGE:
            # In patient edit page (staff user)
            if request.method == "POST" and "request_delete" in request.form:
                PendingRequest.create(patient_id, current_user.id)
                flash("Deletion request submitted to owner")
        """
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO pending_requests (patient_id, requested_by) VALUES (?, ?)",
                (patient_id, requested_by),
            )
            conn.commit()

    @staticmethod
    def get_all_pending():
        """
        Fetch all pending deletion requests with patient and requester information.

        PURPOSE:
            Display pending requests to owner for approval/denial.
            Joins three tables to get complete information.

        HOW IT WORKS:
            1. Query pending_requests table (status = 'pending')
            2. JOIN with patients table to get patient name
            3. JOIN with users table to get requester username
            4. Order by request time (newest first)
            5. Convert sqlite3.Row objects to dictionaries

        JOIN EXPLANATION:
            FROM pending_requests pr
            JOIN patients p ON pr.patient_id = p.id
                → For each request, get the patient's information
            JOIN users u ON pr.requested_by = u.id
                → For each request, get the requester's username

        RETURNS:
            list[dict]: List of dictionaries, each containing:
                - id: Request ID
                - patient_id: Patient's ID
                - requested_by: Requester's user ID
                - status: 'pending'
                - requested_at: Timestamp
                - first_name: Patient's first name
                - last_name: Patient's last name
                - requested_by_name: Username of requester

        USAGE:
            # In pending requests page (owner only)
            pending = PendingRequest.get_all_pending()
            for request in pending:
                print(f"{request['requested_by_name']} wants to delete "
                      f"{request['first_name']} {request['last_name']}")
        """
        with get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT pr.*, p.first_name, p.last_name, u.username AS requested_by_name
                FROM pending_requests pr
                JOIN patients p ON pr.patient_id = p.id
                JOIN users u ON pr.requested_by = u.id
                WHERE pr.status = 'pending'
                ORDER BY pr.requested_at DESC
                """
            ).fetchall()

        # Convert sqlite3.Row objects to dictionaries for easier access
        # dict(row) converts row to dict: {column_name: value}
        return [dict(row) for row in rows]

    @staticmethod
    def approve(request_id: int, approved_by: int) -> None:
        """
        Approve a deletion request (owner only).

        PURPOSE:
            Owner approves the deletion request.
            After this, app.py will delete the actual patient record.

        HOW IT WORKS:
            1. Update pending_requests table
            2. Set status to 'approved'
            3. Record who approved (approved_by = owner's user ID)
            4. Record when approved (approved_at = current timestamp)

        PARAMETERS:
            request_id (int): ID of the request to approve
            approved_by (int): User ID of the owner approving

        RETURNS:
            None: No return value (updates database record)

        WORKFLOW:
            1. Owner clicks "Approve" button
            2. This method updates status to 'approved'
            3. app.py deletes the patient from database
            4. app.py deletes the approved request record (cleanup)

        USAGE:
            # In approve request route (owner only)
            PendingRequest.approve(request_id, current_user.id)
            # Then delete patient from database
            conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        """
        with get_db_connection() as conn:
            conn.execute(
                """
                UPDATE pending_requests
                SET status = 'approved', approved_by = ?, approved_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (approved_by, request_id),
            )
            conn.commit()

    @staticmethod
    def deny(request_id: int, approved_by: int) -> None:
        """
        Deny a deletion request (owner only).

        PURPOSE:
            Owner denies the deletion request.
            Patient record remains in database.

        HOW IT WORKS:
            Same as approve(), but sets status to 'denied' instead.

        PARAMETERS:
            request_id (int): ID of the request to deny
            approved_by (int): User ID of the owner denying

        RETURNS:
            None: No return value (updates database record)

        WORKFLOW:
            1. Owner clicks "Deny" button
            2. This method updates status to 'denied'
            3. Request remains in database (for audit purposes)
            4. Patient remains in database (not deleted)

        USAGE:
            # In deny request route (owner only)
            PendingRequest.deny(request_id, current_user.id)
            flash("Deletion request denied")
        """
        with get_db_connection() as conn:
            conn.execute(
                """
                UPDATE pending_requests
                SET status = 'denied', approved_by = ?, approved_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (approved_by, request_id),
            )
            conn.commit()


# ==============================================================================
# APPLICATION INITIALIZATION
# ==============================================================================
# The code below runs automatically when this module is imported.
# It ensures database tables exist and creates a default owner account.
# ==============================================================================

# Create all database tables if they don't exist
# Safe to call multiple times (IF NOT EXISTS prevents errors)
init_db()

# Create default owner account if it doesn't exist
# This allows first-time users to log in without manual database setup
with get_db_connection() as conn:
    # Check if owner account already exists (username='manager' for backward compatibility)
    existing_owner = conn.execute("SELECT id FROM users WHERE username = 'manager'").fetchone()

    if not existing_owner:
        # Owner doesn't exist - create it
        conn.execute(
            """
            INSERT INTO users (username, password_hash, full_name, email, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "manager",                        # Username: manager (kept for backward compatibility)
                generate_password_hash("12345"),  # Password: 12345 (hashed)
                "Clinic Owner",                   # Full name
                "manager@example.com",            # Email
                "owner",                          # Role: owner
            ),
        )
        conn.commit()
        print("Default owner account created: username=manager, password=12345")


# ==============================================================================
# MODULE SUMMARY
# ==============================================================================
"""
CLASSES PROVIDED:

1. User (UserMixin):
    - Authentication and session management
    - Role-based authorization methods
    - Database CRUD operations for users

2. PendingRequest:
    - Deletion approval workflow
    - Request creation, approval, denial

FUNCTIONS PROVIDED:

- get_db_connection(): Create database connection with Row factory
- init_db(): Create database tables

DATABASE SCHEMA:

1. users: Staff accounts (owner, dentist, staff)
2. patients: Patient records and medical information
3. audit_logs: Activity tracking for compliance
4. pending_requests: Deletion approval workflow

SECURITY FEATURES:

- Password hashing (PBKDF2-SHA256)
- SQL injection prevention (parameterized queries)
- Role-based access control
- Soft delete capability (is_active flag)
- Audit trail for all actions

USAGE PATTERNS:

1. Authentication:
    user = User.get_by_username("manager")
    if user and user.verify_password("12345"):
        login_user(user)

2. Authorization:
    if current_user.is_manager():
        # Allow staff management
        pass

3. Deletion Workflow:
    # Staff requests
    PendingRequest.create(patient_id, staff_id)

    # Owner approves
    requests = PendingRequest.get_all_pending()
    PendingRequest.approve(request_id, owner_id)

    # Then delete patient
    conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
"""
