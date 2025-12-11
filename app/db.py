from pathlib import Path
import sqlite3

# Ruta base: carpeta del proyecto (proyecto_redes)
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "red.db"


def get_conn():
    # Asegurar que la carpeta data exista
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # Usuarios (login)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    );
    """)

    # Dispositivos (info general)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostname TEXT,
        ip TEXT,
        modelo TEXT,
        ios_version TEXT,
        serial TEXT
    );
    """)

    # Interfaces (VLAN / MAC)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS interfaces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER,
        interface TEXT,
        vlan INTEGER,
        mac TEXT,
        FOREIGN KEY (device_id) REFERENCES devices(id)
    );
    """)

    # Log de inventarios
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_at TEXT,
        notes TEXT
    );
    """)

    conn.commit()
    conn.close()


def crear_usuario_inicial():
    """Crea el usuario admin/admin si no existe."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
        ("admin", "admin")
    )
    conn.commit()
    conn.close()
