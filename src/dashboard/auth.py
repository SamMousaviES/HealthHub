import functools
import hmac
import os
import secrets
import sqlite3
from datetime import datetime, timezone

from flask import has_request_context, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .config import APP_TITLE, GYM_USER_DB_FILE


REGISTRATION_DISABLED_HOSTS = {"dashboard.sam-mousavi.com"}


def normalize_username(value: str | None):
    return str(value or "").strip().lower()


def dashboard_username() -> str:
    return normalize_username(os.getenv("DASHBOARD_USERNAME", "sam")) or "sam"


def dashboard_password() -> str:
    return os.getenv("DASHBOARD_PASSWORD", "")


def configured_extra_default_usernames() -> list[str]:
    raw = str(os.getenv("DASHBOARD_EXTRA_DEFAULT_USERS", "melina,nora") or "").strip()
    if not raw:
        return []
    names = []
    seen = set()
    for item in raw.split(","):
        current = normalize_username(item)
        if not current or current == dashboard_username() or current in seen:
            continue
        seen.add(current)
        names.append(current)
    return names


def default_dashboard_account_specs() -> list[dict]:
    primary_username = dashboard_username()
    specs = [
        {
            "username": primary_username,
            "password": dashboard_password(),
            "display_name": primary_username.title(),
            "first_name": primary_username.title(),
            "last_name": "",
            "role": "admin",
        }
    ]
    known_member_specs = {
        "melina": {
            "username": "melina",
            "password": os.getenv("DASHBOARD_MELINA_PASSWORD", "11001100"),
            "display_name": "Melina",
            "first_name": "Melina",
            "last_name": "",
            "role": "member",
        },
        "nora": {
            "username": "nora",
            "password": os.getenv("DASHBOARD_NORA_PASSWORD", "11001100"),
            "display_name": "Nora",
            "first_name": "Nora",
            "last_name": "",
            "role": "member",
        },
    }
    for username in configured_extra_default_usernames():
        spec = known_member_specs.get(username)
        if spec:
            specs.append(spec)
    return specs


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _db_connection():
    GYM_USER_DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(GYM_USER_DB_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def _ensure_sqlite_column(connection, table_name: str, column_name: str, definition: str):
    columns = {row["name"] for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()}
    if column_name not in columns:
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def compose_display_name(first_name: str | None, last_name: str | None, username: str | None = None, fallback: str | None = None) -> str:
    parts = [str(first_name or "").strip(), str(last_name or "").strip()]
    joined = " ".join(part for part in parts if part).strip()
    if joined:
        return joined
    fallback_text = str(fallback or "").strip()
    if fallback_text:
        return fallback_text
    current_username = normalize_username(username)
    return current_username.title() if current_username else ""


def ensure_auth_storage():
    with _db_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                display_name TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS auth_accounts (
                user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'member',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        _ensure_sqlite_column(connection, "users", "first_name", "TEXT")
        _ensure_sqlite_column(connection, "users", "last_name", "TEXT")
        _ensure_sqlite_column(connection, "auth_accounts", "role", "TEXT NOT NULL DEFAULT 'member'")
        _ensure_sqlite_column(connection, "auth_accounts", "is_active", "INTEGER NOT NULL DEFAULT 1")


def ensure_dashboard_seed_accounts():
    ensure_auth_storage()
    timestamp = _now_iso()
    with _db_connection() as connection:
        for spec in default_dashboard_account_specs():
            username = normalize_username(spec.get("username"))
            if not username:
                continue
            first_name = str(spec.get("first_name", "")).strip()
            last_name = str(spec.get("last_name", "")).strip()
            display_name = compose_display_name(first_name, last_name, username, spec.get("display_name"))
            connection.execute(
                """
                INSERT INTO users (username, display_name, first_name, last_name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(username) DO UPDATE SET
                    display_name = CASE
                        WHEN users.display_name IS NULL OR TRIM(users.display_name) = '' THEN excluded.display_name
                        ELSE users.display_name
                    END,
                    first_name = CASE
                        WHEN users.first_name IS NULL OR TRIM(users.first_name) = '' THEN excluded.first_name
                        ELSE users.first_name
                    END,
                    last_name = CASE
                        WHEN users.last_name IS NULL OR TRIM(users.last_name) = '' THEN excluded.last_name
                        ELSE users.last_name
                    END,
                    updated_at = excluded.updated_at
                """,
                (username, display_name, first_name, last_name, timestamp, timestamp),
            )
            user_row = connection.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if not user_row:
                continue
            existing_auth = connection.execute(
                "SELECT user_id FROM auth_accounts WHERE user_id = ?",
                (user_row["id"],),
            ).fetchone()
            if existing_auth:
                connection.execute(
                    """
                    UPDATE auth_accounts
                    SET role = ?, is_active = 1, updated_at = ?
                    WHERE user_id = ?
                    """,
                    (spec.get("role", "member"), timestamp, user_row["id"]),
                )
                continue
            connection.execute(
                """
                INSERT INTO auth_accounts (user_id, password_hash, role, is_active, created_at, updated_at)
                VALUES (?, ?, ?, 1, ?, ?)
                """,
                (
                    user_row["id"],
                    generate_password_hash(str(spec.get("password", ""))),
                    spec.get("role", "member"),
                    timestamp,
                    timestamp,
                ),
            )


def _seed_account_defaults_map() -> dict[str, dict]:
    return {
        normalize_username(item.get("username")): item
        for item in default_dashboard_account_specs()
        if normalize_username(item.get("username"))
    }


def _account_row_for_username(username: str | None):
    current_username = normalize_username(username)
    if not current_username or not GYM_USER_DB_FILE.exists():
        return None
    ensure_auth_storage()
    with _db_connection() as connection:
        return connection.execute(
            """
            SELECT
                users.id,
                users.username,
                users.display_name,
                users.first_name,
                users.last_name,
                auth_accounts.password_hash,
                auth_accounts.role,
                auth_accounts.is_active
            FROM users
            LEFT JOIN auth_accounts ON auth_accounts.user_id = users.id
            WHERE users.username = ?
            LIMIT 1
            """,
            (current_username,),
        ).fetchone()


def dashboard_accounts() -> dict[str, dict]:
    defaults = _seed_account_defaults_map()
    if not GYM_USER_DB_FILE.exists():
        return defaults
    ensure_auth_storage()
    with _db_connection() as connection:
        rows = connection.execute(
            """
            SELECT users.username, users.display_name, users.first_name, users.last_name, auth_accounts.role
            FROM users
            JOIN auth_accounts ON auth_accounts.user_id = users.id
            WHERE COALESCE(auth_accounts.is_active, 1) = 1
            ORDER BY users.username
            """
        ).fetchall()
    if not rows:
        return defaults
    accounts = {}
    for row in rows:
        username = normalize_username(row["username"])
        accounts[username] = {
            "display_name": compose_display_name(row["first_name"], row["last_name"], username, row["display_name"]),
            "role": row["role"] or "member",
        }
    return accounts


def display_name_for_username(username: str | None):
    current_username = normalize_username(username)
    if not current_username:
        return ""
    row = _account_row_for_username(current_username)
    if row:
        return compose_display_name(row["first_name"], row["last_name"], current_username, row["display_name"])
    default = _seed_account_defaults_map().get(current_username)
    if default:
        return compose_display_name(default.get("first_name"), default.get("last_name"), current_username, default.get("display_name"))
    return current_username.title()


def viewer_app_title(username: str | None):
    display_name = display_name_for_username(username)
    if not display_name:
        return APP_TITLE
    return f"{display_name} {APP_TITLE}"


def authenticate_dashboard_user(username: str | None, password: str | None):
    current_username = normalize_username(username)
    if not current_username:
        return None
    row = _account_row_for_username(current_username)
    if not row or not row["password_hash"] or not int(row["is_active"] or 0):
        return None
    supplied_password = str(password or "")
    stored_hash = str(row["password_hash"] or "")
    if stored_hash.startswith(("pbkdf2:", "scrypt:")):
        valid = check_password_hash(stored_hash, supplied_password)
    else:
        valid = hmac.compare_digest(supplied_password, stored_hash)
        if valid:
            with _db_connection() as connection:
                connection.execute(
                    "UPDATE auth_accounts SET password_hash = ?, updated_at = ? WHERE user_id = ?",
                    (generate_password_hash(supplied_password), _now_iso(), row["id"]),
                )
    return current_username if valid else None


def register_dashboard_user(
    username: str,
    password: str,
    first_name: str,
    last_name: str,
    role: str = "member",
) -> str:
    ensure_auth_storage()
    current_username = normalize_username(username)
    if not current_username:
        raise ValueError("Username is required.")
    timestamp = _now_iso()
    display_name = compose_display_name(first_name, last_name, current_username)
    with _db_connection() as connection:
        existing = connection.execute(
            "SELECT id FROM users WHERE username = ? LIMIT 1",
            (current_username,),
        ).fetchone()
        if existing:
            raise ValueError("That username already exists.")
        cursor = connection.execute(
            """
            INSERT INTO users (username, display_name, first_name, last_name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (current_username, display_name, first_name.strip(), last_name.strip(), timestamp, timestamp),
        )
        connection.execute(
            """
            INSERT INTO auth_accounts (user_id, password_hash, role, is_active, created_at, updated_at)
            VALUES (?, ?, ?, 1, ?, ?)
            """,
            (cursor.lastrowid, generate_password_hash(password), role, timestamp, timestamp),
        )
    return current_username


def viewer_username() -> str:
    return normalize_username(session.get("username", ""))


def current_request_host() -> str:
    if not has_request_context():
        return ""
    forwarded = str(request.headers.get("X-Forwarded-Host") or "").strip()
    host_value = forwarded or str(request.host or "").strip()
    return host_value.split(":", 1)[0].lower()


def host_allows_registration() -> bool:
    host_value = current_request_host()
    if not host_value:
        return True
    return host_value not in REGISTRATION_DISABLED_HOSTS


def dashboard_sections():
    return [
        {"id": "diet", "label": "Diet"},
        {"id": "gym", "label": "Gym"},
        {"id": "health", "label": "Health"},
        {"id": "coach", "label": "Coach"},
    ]


def resolve_dashboard_tab(preferred_tab: str | None = None, health_needs_profile_setup: bool = False):
    section_ids = {item["id"] for item in dashboard_sections()}
    requested = (preferred_tab or "").strip().lower()
    if requested in section_ids:
        return requested
    return "health" if health_needs_profile_setup else "diet"


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login"))
        ensure_csrf_token()
        return view(*args, **kwargs)

    return wrapped


def ensure_csrf_token() -> str:
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_hex(24)
        session["csrf_token"] = token
    return token


def verify_csrf() -> bool:
    return hmac.compare_digest(session.get("csrf_token", ""), request.form.get("csrf_token", ""))


def request_wants_json() -> bool:
    requested_with = str(request.headers.get("X-Requested-With", "")).strip().lower()
    accept = str(request.headers.get("Accept", "")).strip().lower()
    return requested_with == "xmlhttprequest" or "application/json" in accept
