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

        return {
            **dict(row),
            "temperature_unit": "°C",
            "pressure_unit": "kPa",
        }

    finally:
        connection.close()


@tool
def get_equipment_status(equipment_id: str) -> dict:
    """Retrieve the current status and details of a specific equipment item.

    Use this tool when the user asks about the status, name,
    or location of equipment identified by its equipment ID.
    """
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT equipment_id, name, location, status
            FROM equipment
            WHERE equipment_id = ?
            """,
            (equipment_id,)
        ).fetchone()

        if row is None:
            return {
                "error": f"Equipment {equipment_id} not found"
            }

        return dict(row)

    finally:
        connection.close()


@tool
def list_equipment_by_status(status: str) -> list[dict]:
    """Retrieve all equipment with a specified status.

    Use this tool when the user asks which equipment is
    online, offline, or in a warning state.

    Args:
        status: Equipment status (online, offline, or warning).
    """
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT equipment_id, name, location, status
            FROM equipment
            WHERE status = ?
            ORDER BY equipment_id
            """,
            (status,)
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


@tool
def get_measurement_statistics(equipment_id: str) -> dict:
    """Calculate temperature and pressure statistics for equipment.

    Use this tool when the user asks about average, minimum,
    maximum, or number of measurements for specific equipment.

    Statistics are calculated over all available measurements.
    """
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS measurement_count,
                AVG(temperature) AS avg_temperature,
                MIN(temperature) AS min_temperature,
                MAX(temperature) AS max_temperature,
                AVG(pressure) AS avg_pressure,
                MIN(pressure) AS min_pressure,
                MAX(pressure) AS max_pressure
            FROM measurements
            WHERE equipment_id = ?
            """,
            (equipment_id,)
        ).fetchone()

        if row["measurement_count"] == 0:
            return {
                "error": f"No measurements found for {equipment_id}"
            }

        return {
            "equipment_id": equipment_id,
            **dict(row),
            "temperature_unit": "°C",
            "pressure_unit": "kPa",
        }

    finally:
        connection.close()