from src.database import get_connection
from langchain_core.tools import tool


@tool
def get_latest_measurement(equipment_id: str) -> dict:
    """Retrieve the latest measurement for a given equipment ID."""

    connection = get_connection()

    try:
        cursor = connection.execute("""
            SELECT
                equipment_id,
                timestamp,
                temperature,
                pressure
            FROM measurements
            WHERE equipment_id = ?
            ORDER BY timestamp DESC, measurement_id DESC
            LIMIT 1
        """, (equipment_id,))

        row = cursor.fetchone()

        if row is None:
            return {"error": "No measurements found"}

        return dict(row)

    finally:
        connection.close()