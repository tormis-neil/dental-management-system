from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, send_file
)
from flask_login import (
    LoginManager, login_user,
    logout_user, login_required, current_user
)
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import safe_join
from typing import Optional
import os

from config import Config
from models import User, get_db_connection, init_db, PendingRequest
from utils import (
    manager_required, login_required_custom, log_activity,
    backup_database, restore_database, get_backup_files, calculate_age
)

app = Flask(__name__)
app.config.from_object(Config)
csrf = CSRFProtect(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id: str) -> Optional[User]:
    return User.get_by_id(int(user_id))

init_db()

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user = User.get_by_username(username)
        if user and user.verify_password(password):
            login_user(user)
            log_activity(user.id, user.username, "LOGIN", "User logged in")
            flash(f"Welcome back, {user.full_name or user.username}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    log_activity(current_user.id, current_user.username, "LOGOUT", "User logged out")
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.route('/dashboard')
@login_required
def dashboard():
    total_patients = 0
    total_staff = 0
    recent_patients = []
    recent_activities = []
    pending_requests_list = []
    total_pending_count = 0

    with get_db_connection() as conn:
        total_patients = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
        total_staff = conn.execute("SELECT COUNT(*) FROM users WHERE role='staff'").fetchone()[0]

        recent_patients = conn.execute("""
            SELECT first_name, last_name, phone, created_at 
            FROM patients 
            ORDER BY created_at DESC LIMIT 5
        """).fetchall()

        recent_activities = conn.execute("""
            SELECT username, action_type AS action, timestamp 
            FROM audit_logs 
            ORDER BY timestamp DESC LIMIT 5
        """).fetchall()

        if current_user.is_manager() or current_user.is_dentist() or current_user.is_admin():
            rows = conn.execute("""
                SELECT pr.id, p.first_name, p.last_name, pr.requested_by, pr.requested_at
                FROM pending_requests pr
                JOIN patients p ON pr.patient_id = p.id
                WHERE pr.status = 'pending'
                ORDER BY pr.requested_at DESC
                LIMIT 3
            """).fetchall()

            pending_requests_list = [dict(r) for r in rows]
            total_pending_count = conn.execute(
                "SELECT COUNT(*) FROM pending_requests WHERE status = 'pending'"
            ).fetchone()[0]

            user_ids = [r["requested_by"] for r in pending_requests_list]
            user_map = {}
            if user_ids:
                rows_users = conn.execute(
                    f"SELECT id, username FROM users WHERE id IN ({','.join(['?']*len(user_ids))})",
                    user_ids
                ).fetchall()
                user_map = {r["id"]: r["username"] for r in rows_users}

            for r in pending_requests_list:
                r["requested_by_name"] = user_map.get(r["requested_by"], "Unknown")

    return render_template(
        'dashboard.html',
        total_patients=total_patients,
        total_staff=total_staff,
        recent_patients=recent_patients,
        recent_activities=recent_activities,
        pending_requests=pending_requests_list,
        total_pending_count=total_pending_count
    )

@app.route("/patients")
@login_required
def patients():
    search = request.args.get("search", "")
    gender = request.args.get("gender", "")
    
    with get_db_connection() as conn:
        query = "SELECT * FROM patients WHERE 1=1"
        params = []
        
        if search:
            query += " AND (first_name LIKE ? OR last_name LIKE ? OR phone LIKE ? OR CAST(id AS TEXT) LIKE ?)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param, search_param])
        
        if gender:
            query += " AND gender = ?"
            params.append(gender)
        
        query += " ORDER BY id DESC"
        patients = conn.execute(query, params).fetchall()
    
    patients_list = []
    for p in patients:
        patient_dict = dict(p)
        patient_dict['age'] = calculate_age(patient_dict.get('date_of_birth'))
        patients_list.append(patient_dict)
    
    return render_template("patients.html", patients=patients_list, search=search, gender=gender)

@app.route("/patients/add", methods=["GET", "POST"])
@login_required
def add_patient():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        date_of_birth = request.form.get("date_of_birth")
        gender = request.form.get("gender")
        phone = request.form.get("phone")
        email = request.form.get("email")
        address = request.form.get("address")
        emergency_contact_name = request.form.get("emergency_contact_name")
        emergency_contact_phone = request.form.get("emergency_contact_phone")
        
        allergies = None
        existing_condition = None
        dentist_notes = None
        assigned_dentist = None
        
        if current_user.is_manager() or current_user.is_dentist() or current_user.is_admin():
            allergies = request.form.get("allergies")
            existing_condition = request.form.get("existing_condition")
            dentist_notes = request.form.get("dentist_notes")
            assigned_dentist = request.form.get("assigned_dentist")
        elif current_user.is_staff():
            assigned_dentist = current_user.full_name or current_user.username

        if not first_name or not last_name:
            flash("First Name and Last Name are required.", "danger")
            return redirect(url_for("add_patient"))

        try:
            with get_db_connection() as conn:
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
            log_activity(current_user.id, current_user.username, "ADD_PATIENT",
                        f"Added patient {first_name} {last_name}")
            flash("Patient added successfully!", "success")
            return redirect(url_for("patients"))
        except Exception as e:
            print("Error adding patient:", e)
            flash("Failed to add patient.", "danger")
            return redirect(url_for("add_patient"))

    return render_template("add_patient.html")

@app.route("/patients/view/<int:patient_id>")
@login_required
def view_patient(patient_id):
    with get_db_connection() as conn:
        patient = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    if not patient:
        flash("Patient not found.", "danger")
        return redirect(url_for("patients"))
    patient_dict = dict(patient)
    patient_dict['age'] = calculate_age(patient_dict.get('date_of_birth'))
    return render_template("view_patient.html", patient=patient_dict)

@app.route("/patients/edit/<int:patient_id>", methods=["GET", "POST"])
@login_required
def edit_patient(patient_id):
    with get_db_connection() as conn:
        patient = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
        if not patient:
            flash("Patient not found.", "danger")
            return redirect(url_for("patients"))

        if request.method == "POST":
            first_name = request.form.get("first_name")
            last_name = request.form.get("last_name")
            date_of_birth = request.form.get("date_of_birth")
            gender = request.form.get("gender")
            phone = request.form.get("phone")
            email = request.form.get("email")
            address = request.form.get("address")
            emergency_contact_name = request.form.get("emergency_contact_name")
            emergency_contact_phone = request.form.get("emergency_contact_phone")
            
            if current_user.is_manager() or current_user.is_dentist() or current_user.is_admin():
                allergies = request.form.get("allergies")
                existing_condition = request.form.get("existing_condition")
                dentist_notes = request.form.get("dentist_notes")
                assigned_dentist = request.form.get("assigned_dentist")
                
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
            
            conn.commit()
            log_activity(current_user.id, current_user.username, "EDIT_PATIENT",
                        f"Edited patient ID {patient_id}")
            flash("Patient updated successfully!", "success")
            return redirect(url_for("patients"))

        patient = dict(patient)
    return render_template("edit_patient.html", patient=patient)

@app.route("/patients/delete/<int:patient_id>", methods=["POST"])
@login_required
def delete_patient(patient_id):
    if not (current_user.is_manager() or current_user.is_dentist()):
        flash("Only managers and dentists can delete patients directly.", "danger")
        return redirect(url_for("patients"))

    with get_db_connection() as conn:
        patient = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
        if not patient:
            flash("Patient not found.", "danger")
        else:
            conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
            conn.commit()
            log_activity(current_user.id, current_user.username, "DELETE_PATIENT",
                         f"Deleted patient ID {patient_id}")
            flash("Patient deleted successfully!", "success")
    return redirect(url_for("patients"))

@app.route('/patients/request_delete/<int:patient_id>', methods=['POST'])
@login_required
def request_delete_patient(patient_id):
    if not current_user.is_staff():
        flash("Only staff members can request deletions.", "danger")
        return redirect(url_for('patients'))

    with get_db_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM pending_requests WHERE patient_id = ? AND status = 'pending'",
            (patient_id,)
        ).fetchone()

        if existing:
            flash("A deletion request for this patient already exists.", "warning")
            return redirect(url_for('patients'))

        conn.execute(
            "INSERT INTO pending_requests (patient_id, requested_by) VALUES (?, ?)",
            (patient_id, current_user.id)
        )
        conn.commit()

    log_activity(current_user.id, current_user.username, "REQUEST_DELETE",
                f"Requested deletion for patient ID {patient_id}")
    flash("Deletion request sent for approval.", "info")
    return redirect(url_for('patients'))

@app.route("/pending_requests")
@login_required
@manager_required
def pending_requests_view():
    search = request.args.get("search", "")
    requests_list = PendingRequest.get_all_pending()
    
    if search:
        filtered_requests = []
        for req in requests_list:
            if (search.lower() in req['first_name'].lower() or 
                search.lower() in req['last_name'].lower() or
                search in str(req['id'])):
                filtered_requests.append(req)
        requests_list = filtered_requests
    
    return render_template("pending_requests.html", requests=requests_list, search=search)

@app.route("/pending_requests/approve/<int:request_id>", methods=["POST"])
@login_required
@manager_required
def approve_request(request_id):
    PendingRequest.approve(request_id, current_user.id)
    with get_db_connection() as conn:
        row = conn.execute("SELECT patient_id FROM pending_requests WHERE id = ?", (request_id,)).fetchone()
        if row:
            patient_id = row["patient_id"]
            conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
            conn.commit()
            log_activity(current_user.id, current_user.username, "APPROVE_DELETE",
                         f"Approved deletion for patient ID {patient_id}")
    flash("Deletion request approved and patient record removed.", "success")
    return redirect(url_for("pending_requests_view"))

@app.route("/pending_requests/deny/<int:request_id>", methods=["POST"])
@login_required
@manager_required
def deny_request(request_id):
    PendingRequest.deny(request_id, current_user.id)
    log_activity(current_user.id, current_user.username, "DENY_DELETE", f"Denied deletion request ID {request_id}")
    flash("Deletion request denied.", "info")
    return redirect(url_for("pending_requests_view"))

@app.route("/staff")
@login_required
@manager_required
def staff():
    search = request.args.get("search", "")
    status = request.args.get("status", "")
    
    with get_db_connection() as conn:
        query = "SELECT * FROM users WHERE role='staff'"
        params = []
        
        if search:
            query += " AND (full_name LIKE ? OR username LIKE ? OR CAST(id AS TEXT) LIKE ?)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        if status == "active":
            query += " AND is_active = 1"
        elif status == "inactive":
            query += " AND is_active = 0"
        
        query += " ORDER BY id DESC"
        staff_list = conn.execute(query, params).fetchall()
    
    staff_list = [dict(s) for s in staff_list]
    return render_template("staff.html", staff_list=staff_list, search=search, status=status)

@app.route("/add_staff", methods=["GET", "POST"])
@login_required
@manager_required
def add_staff():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        full_name = request.form.get("full_name", "")
        email = request.form.get("email", "")
        role = "staff"
        created = User.create_user(username, password, role, full_name, email)
        if created:
            log_activity(current_user.id, current_user.username, "ADD_STAFF",
                         f"Added staff {full_name} ({username})")
            flash("Staff member added successfully!", "success")
            return redirect(url_for("staff"))
        else:
            flash("Username already exists!", "danger")
    return render_template("add_staff.html")

@app.route("/edit_staff/<int:staff_id>", methods=["GET", "POST"])
@login_required
@manager_required
def edit_staff(staff_id):
    with get_db_connection() as conn:
        staff = conn.execute("SELECT * FROM users WHERE id = ? AND role='staff'", (staff_id,)).fetchone()
        if not staff:
            flash("Staff member not found.", "danger")
            return redirect(url_for("staff"))
        if request.method == "POST":
            full_name = request.form.get("full_name", "")
            email = request.form.get("email", "")
            is_active = 1 if 'is_active' in request.form else 0
            new_password = request.form.get("new_password", "")
            if new_password:
                password_hash = generate_password_hash(new_password)
                conn.execute(
                    "UPDATE users SET full_name=?, email=?, is_active=?, password_hash=? WHERE id=?",
                    (full_name, email, is_active, password_hash, staff_id)
                )
            else:
                conn.execute(
                    "UPDATE users SET full_name=?, email=?, is_active=? WHERE id=?",
                    (full_name, email, is_active, staff_id)
                )
            conn.commit()
            log_activity(current_user.id, current_user.username, "EDIT_STAFF",
                         f"Edited staff {full_name} (ID {staff_id})")
            flash("Staff member updated!", "success")
            return redirect(url_for("staff"))
    staff = dict(staff)
    return render_template("edit_staff.html", staff=staff)

@app.route("/staff/delete/<int:staff_id>", methods=["POST"])
@login_required
@manager_required
def delete_staff(staff_id):
    with get_db_connection() as conn:
        staff = conn.execute("SELECT * FROM users WHERE id=? AND role='staff'", (staff_id,)).fetchone()
        if not staff:
            flash("Staff member not found.", "danger")
        else:
            conn.execute("DELETE FROM users WHERE id=?", (staff_id,))
            conn.commit()
            log_activity(current_user.id, current_user.username, "DELETE_STAFF", f"Deleted staff ID {staff_id}")
            flash("Staff member deleted.", "success")
    return redirect(url_for("staff"))

@app.route("/my_profile", methods=["GET", "POST"])
@login_required
def my_profile():
    if request.method == "POST":
        full_name = request.form.get("full_name", "")
        email = request.form.get("email", "")
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        
        with get_db_connection() as conn:
            if new_password and current_password:
                if current_user.verify_password(current_password):
                    password_hash = generate_password_hash(new_password)
                    conn.execute(
                        "UPDATE users SET full_name=?, email=?, password_hash=? WHERE id=?",
                        (full_name, email, password_hash, current_user.id)
                    )
                    conn.commit()
                    log_activity(current_user.id, current_user.username, "UPDATE_PROFILE",
                                "Updated profile and password")
                    flash("Profile and password updated successfully!", "success")
                else:
                    flash("Current password is incorrect.", "danger")
                    return redirect(url_for("my_profile"))
            else:
                conn.execute(
                    "UPDATE users SET full_name=?, email=? WHERE id=?",
                    (full_name, email, current_user.id)
                )
                conn.commit()
                log_activity(current_user.id, current_user.username, "UPDATE_PROFILE",
                            "Updated profile")
                flash("Profile updated successfully!", "success")
        
        current_user.full_name = full_name
        current_user.email = email
        return redirect(url_for("my_profile"))
    
    return render_template("my_profile.html")

@app.route("/audit_logs")
@login_required
def audit_logs():
    with get_db_connection() as conn:
        if current_user.is_manager():
            logs = conn.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 100").fetchall()
        else:
            logs = conn.execute(
                "SELECT * FROM audit_logs WHERE user_id=? ORDER BY timestamp DESC LIMIT 100",
                (current_user.id,)
            ).fetchall()
    logs = [dict(l) for l in logs]
    return render_template("audit_logs.html", logs=logs)

@app.route("/backup")
@login_required
@manager_required
def backup():
    try:
        os.makedirs(Config.BACKUP_FOLDER, exist_ok=True)
        backups = get_backup_files()
        return render_template("backup.html", backups=backups)
    except Exception as e:
        flash(f"⚠️ Failed to load backups: {e}", "danger")
        return redirect(url_for("dashboard"))

@app.route("/create_backup", methods=["POST"])
@login_required
@manager_required
def create_backup():
    try:
        os.makedirs(Config.BACKUP_FOLDER, exist_ok=True)
        backup_filename = backup_database()
        log_activity(current_user.id, current_user.username, "BACKUP", f"Created backup {backup_filename}")
        flash("Backup created successfully!", "success")
    except Exception as e:
        flash(f"Failed to create backup: {e}", "danger")
    return redirect(url_for("backup"))

@app.route("/backup/download/<path:filename>")
@login_required
@manager_required
def download_backup(filename):
    try:
        backup_path = safe_join(Config.BACKUP_FOLDER, filename)
        if not backup_path or not os.path.exists(backup_path):
            flash("Backup file not found.", "danger")
            return redirect(url_for("backup"))

        return send_file(
            os.path.abspath(backup_path),
            as_attachment=True,
            download_name=filename,
            mimetype="application/octet-stream"
        )
    except Exception as e:
        flash(f"⚠️ Error while downloading backup: {e}", "danger")
        return redirect(url_for("backup"))

@app.route("/backup/restore/<path:filename>", methods=["POST"])
@login_required
@manager_required
def restore_backup(filename):
    try:
        backup_path = safe_join(Config.BACKUP_FOLDER, filename)
        if not backup_path or not os.path.exists(backup_path):
            flash("Backup file not found.", "danger")
            return redirect(url_for("backup"))

        restore_database(filename)
        log_activity(current_user.id, current_user.username, "RESTORE", f"Restored backup {filename}")
        flash("Database successfully restored from backup!", "success")
    except Exception as e:
        flash(f"Failed to restore backup: {e}", "danger")
    return redirect(url_for("backup"))

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        full_name = request.form.get("full_name", "")
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        
        with get_db_connection() as conn:
            if new_password and current_password:
                if current_user.verify_password(current_password):
                    password_hash = generate_password_hash(new_password)
                    conn.execute(
                        "UPDATE users SET full_name=?, password_hash=? WHERE id=?",
                        (full_name, password_hash, current_user.id)
                    )
                    conn.commit()
                    flash("Settings and password updated successfully!", "success")
                else:
                    flash("Current password is incorrect.", "danger")
                    return redirect(url_for("settings"))
            else:
                conn.execute(
                    "UPDATE users SET full_name=? WHERE id=?",
                    (full_name, current_user.id)
                )
                conn.commit()
                flash("Settings updated successfully!", "success")
        
        current_user.full_name = full_name
        return redirect(url_for("dashboard"))
    
    return render_template("settings.html")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
