"""
Konfigurasi aplikasi
"""
import os
import re
from datetime import timedelta


def normalize_database_url(url: str) -> str:
    """
    Ubah URL Neon/Vercel (postgresql://) menjadi URI SQLAlchemy + psycopg2.
    Hapus channel_binding yang sering bermasalah dengan psycopg2.
    """
    if not url:
        return url

    if url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url[len("postgres://") :]
    elif url.startswith("postgresql://") and "+psycopg" not in url.split("://", 1)[0]:
        url = "postgresql+psycopg2://" + url[len("postgresql://") :]

    url = re.sub(r"[&?]channel_binding=[^&]*", "", url)
    url = re.sub(r"\?&", "?", url).rstrip("?")
    return url


def resolve_database_url() -> str:
    """Ambil DATABASE_URL dari env (Neon/Vercel) atau fallback SQL Server lokal."""
    for key in ("DATABASE_URL", "POSTGRES_URL"):
        url = os.environ.get(key)
        if url:
            return normalize_database_url(url)

    sql_server = os.environ.get("SQL_SERVER", "localhost")
    database_name = os.environ.get("DATABASE_NAME", "AbsensiDB")
    sql_username = os.environ.get("SQL_USERNAME", "sa")
    sql_password = os.environ.get("SQL_PASSWORD", "")
    use_windows_auth = os.environ.get("USE_WINDOWS_AUTH", "true").lower() in (
        "true",
        "1",
        "yes",
    )

    if use_windows_auth:
        return (
            f"mssql+pyodbc://{sql_server}/{database_name}"
            "?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
        )
    return (
        f"mssql+pyodbc://{sql_username}:{sql_password}@{sql_server}/{database_name}"
        "?driver=ODBC+Driver+17+for+SQL+Server"
    )


class Config:
    """Konfigurasi dasar aplikasi"""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"

    DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() in ["true", "1", "yes"]

    DATABASE_URL = resolve_database_url()
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Koneksi stabil ke Neon (pooler / serverless)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    CHECK_IN_START = os.environ.get("CHECK_IN_START", "07:00")
    CHECK_IN_END = os.environ.get("CHECK_IN_END", "09:00")
    CHECK_OUT_START = os.environ.get("CHECK_OUT_START", "16:00")
    CHECK_OUT_END = os.environ.get("CHECK_OUT_END", "18:00")

    OFFICE_LATITUDE = float(os.environ.get("OFFICE_LATITUDE", -6.2088))
    OFFICE_LONGITUDE = float(os.environ.get("OFFICE_LONGITUDE", 106.8456))
    GEO_RADIUS_METERS = int(os.environ.get("GEO_RADIUS_METERS", 100))

    UPLOAD_FOLDER = "uploads"
    MAX_UPLOAD_SIZE = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "doc", "docx"}

    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 587)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ["true", "on", "1"]
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
