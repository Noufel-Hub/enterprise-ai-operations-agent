import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "operations.db"


def get_connection(db_path=None):
    if db_path is None:
        db_path = DB_PATH

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(db_path=None):
    connection = get_connection(db_path)

    try:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS equipment (
                equipment_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                location TEXT NOT NULL,
                status TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS measurements (
                measurement_id INTEGER PRIMARY KEY,
                equipment_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                temperature REAL NOT NULL,
                pressure REAL NOT NULL CHECK (pressure >= 0),
                FOREIGN KEY (equipment_id)
                    REFERENCES equipment(equipment_id)
            );
        """)

        connection.commit()

    finally:
        connection.close()
