from src.database import init_db, get_connection


def seed_database():
    init_db()

    connection = get_connection()

    try:
        equipment = [
            ("GAS-101", "Gas Analyzer 1", "Process Line A", "online"),
            ("GAS-102", "Gas Analyzer 2", "Process Line B", "warning"),
            ("GAS-103", "Gas Analyzer 3", "Process Line C", "offline"),
        ]

        connection.executemany("""
            INSERT OR IGNORE INTO equipment
                (equipment_id, name, location, status)
            VALUES (?, ?, ?, ?)
        """, equipment)

        measurements = [
            ("GAS-101", "2026-11-07T10:00:00Z", 24.5, 101.3),
            ("GAS-101", "2026-11-07T10:05:00Z", 25.2, 101.4),
            ("GAS-102", "2026-11-07T10:00:00Z", 31.8, 102.1),
            ("GAS-103", "2026-11-07T10:00:00Z", 22.4, 100.9),
        ]

        connection.executemany("""
            INSERT INTO measurements
                (equipment_id, timestamp, temperature, pressure)
            SELECT ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1
                FROM measurements
                WHERE equipment_id = ?
                  AND timestamp = ?
            )
        """, [
            (
                equipment_id,
                timestamp,
                temperature,
                pressure,
                equipment_id,
                timestamp
            )
            for equipment_id, timestamp, temperature, pressure
            in measurements
        ])

        connection.commit()

        print("Database seeded successfully.")

    finally:
        connection.close()


if __name__ == "__main__":
    seed_database()
