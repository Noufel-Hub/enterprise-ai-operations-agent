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