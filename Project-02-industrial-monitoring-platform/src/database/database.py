import sqlite3
from pathlib import Path


DATABASE_PATH = Path("data/sqlite/industrial_monitoring.db")


def initialize_database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            temperature_c REAL NOT NULL,
            vibration_mms REAL NOT NULL,
            current_a REAL NOT NULL,
            status TEXT NOT NULL,
            warnings TEXT
        )
    """)

    connection.commit()
    connection.close()


def save_measurement(measurement):
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    warnings = ",".join(measurement.get("warnings", []))

    cursor.execute("""
        INSERT INTO measurements (
            machine_id,
            timestamp,
            temperature_c,
            vibration_mms,
            current_a,
            status,
            warnings
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        measurement["machine_id"],
        measurement["timestamp"],
        measurement["temperature_c"],
        measurement["vibration_mms"],
        measurement["current_a"],
        measurement["status"],
        warnings
    ))

    connection.commit()
    connection.close()


def get_latest_measurement():
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM measurements
        ORDER BY id DESC
        LIMIT 1
    """)

    measurement = cursor.fetchone()

    connection.close()

    return measurement


if __name__ == "__main__":
    initialize_database()