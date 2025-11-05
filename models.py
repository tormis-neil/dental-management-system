from __future__ import annotations
import sqlite3
from typing import Optional
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(Config.DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            role TEXT NOT NULL CHECK(role IN ('manager','staff','dentist','admin')),
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            date_of_birth TEXT,
            gender TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            emergency_contact_name TEXT,
            emergency_contact_phone TEXT,
            medical_history TEXT,
            allergies TEXT,
            existing_condition TEXT,
            dentist_notes TEXT,
            created_by INTEGER,
            assigned_dentist TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            action_type TEXT,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS pending_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            requested_by INTEGER NOT NULL,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending','approved','denied')),
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_by INTEGER,
            approved_at TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (requested_by) REFERENCES users(id)
        );
        """)
        conn.commit()


class User(UserMixin):
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
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.full_name = full_name
        self.email = email
        self.is_active_flag = is_active

    def get_id(self) -> str:
        return str(self.id)

    @property
    def is_active(self) -> bool:
        return bool(self.is_active_flag)

    def is_manager(self) -> bool:
        return self.role == "manager"

    def is_staff(self) -> bool:
        return self.role == "staff"

    def is_dentist(self) -> bool:
        return self.role == "dentist"

    def is_admin(self) -> bool:
        return self.role == "admin"

    def verify_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_by_id(user_id: int) -> Optional["User"]:
        with get_db_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
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
    def get_by_username(username: str) -> Optional["User"]:
        with get_db_connection() as conn:
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
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def get_users_by_ids(user_ids: list[int]) -> dict[int, str]:
        if not user_ids:
            return {}
        placeholders = ','.join('?' for _ in user_ids)
        query = f"SELECT id, username FROM users WHERE id IN ({placeholders})"
        with get_db_connection() as conn:
            rows = conn.execute(query, user_ids).fetchall()
        return {row['id']: row['username'] for row in rows}


class PendingRequest:
    @staticmethod
    def create(patient_id: int, requested_by: int) -> None:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO pending_requests (patient_id, requested_by) VALUES (?, ?)",
                (patient_id, requested_by),
            )
            conn.commit()

    @staticmethod
    def get_all_pending():
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
        return [dict(row) for row in rows]

    @staticmethod
    def approve(request_id: int, approved_by: int) -> None:
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


init_db()

with get_db_connection() as conn:
    existing_manager = conn.execute("SELECT id FROM users WHERE username = 'manager'").fetchone()
    if not existing_manager:
        conn.execute(
            """
            INSERT INTO users (username, password_hash, full_name, email, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "manager",
                generate_password_hash("12345"),
                "Clinic Manager",
                "manager@example.com",
                "manager",
            ),
        )
        conn.commit()
        print("Default manager account created: username=manager, password=12345")
