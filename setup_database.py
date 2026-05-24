"""
Setup database: Neon PostgreSQL (default) atau SQL Server lokal (legacy).
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def setup_neon():
    """Buat tabel dan data awal di Neon via Flask-SQLAlchemy."""
    import init_db  # noqa: F401 — menjalankan create_all + seed user default

    print("Setup selesai via init_db (Neon PostgreSQL).")
    return True


def setup_sql_server():
    """Membuat database SQL Server jika belum ada (legacy)."""
    import pyodbc

    server = os.environ.get("SQL_SERVER", "localhost")
    database_name = os.environ.get("DATABASE_NAME", "AbsensiDB")
    sql_username = os.environ.get("SQL_USERNAME", "sa")
    sql_password = os.environ.get("SQL_PASSWORD", "")
    use_windows_auth = os.environ.get("USE_WINDOWS_AUTH", "true").lower() in (
        "true",
        "1",
        "yes",
    )

    try:
        if use_windows_auth:
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};DATABASE=master;Trusted_Connection=yes;"
            )
        else:
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};DATABASE=master;"
                f"UID={sql_username};PWD={sql_password};"
            )

        print(f"Mencoba koneksi ke SQL Server: {server}...")
        conn = pyodbc.connect(conn_str, timeout=5)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sys.databases WHERE name = ?", (database_name,)
        )
        if cursor.fetchone():
            print(f"Database '{database_name}' sudah ada.")
        else:
            print(f"Membuat database '{database_name}'...")
            cursor.execute(f"CREATE DATABASE [{database_name}]")
            conn.commit()
            print(f"Database '{database_name}' berhasil dibuat.")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error SQL Server: {e}")
        return False


def main():
    print("=" * 60)
    print("Setup Database Sistem Presensi Karyawan")
    print("=" * 60)

    db_url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if db_url and ("postgres" in db_url.lower() or "neon" in db_url.lower()):
        print("Mode: Neon / PostgreSQL")
        if not setup_neon():
            sys.exit(1)
    else:
        print("Mode: SQL Server (legacy)")
        if not setup_sql_server():
            sys.exit(1)
        print("\nJalankan: python init_db.py")

    print("=" * 60)
    print("Selesai. Jalankan: python app.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
