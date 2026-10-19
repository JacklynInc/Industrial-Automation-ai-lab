
"""Publish Jay01 simulator measurements to the existing MQTT broker."""

import json
import sqlite3
import time
from pathlib import Path

import paho.mqtt.client as mqtt


BROKER = "localhost"
PORT = 1883
TOPIC = "factory/jay01/sensors"
MACHINE_ID = "Jay01"

DB_PATH = Path(__file__).with_name("jay01_history.sqlite3")


def get_latest_measurement():
    """Read the latest measurement from Jay01's SQLite database."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row

        row = connection.execute(
            """
            SELECT timestamp, machine_id, state, temperature_c,
                   vibration_mm_s_rms, current_a, speed_rpm,
                   sensor_valid, active_alarms
            FROM measurements
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    if row is None:
        raise RuntimeError("No Jay01 measurements found.")

    measurement = dict(row)
    measurement["machine_id"] = MACHINE_ID
    measurement["sensor_valid"] = bool(measurement["sensor_valid"])

    return measurement


def main():
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="jay01_publisher",
    )

    try:
        client.connect(BROKER, PORT, keepalive=60)
        client.loop_start()
        print(f"Connected to MQTT broker at {BROKER}:{PORT}")
        print(f"Publishing to: {TOPIC}")
        print("Press Ctrl+C to stop.")

        last_timestamp = None

        while True:
            measurement = get_latest_measurement()

            # Publish only when the simulator records a new measurement.
            if measurement["timestamp"] != last_timestamp:
                payload = json.dumps(measurement)
                result = client.publish(TOPIC, payload, qos=1)
                result.wait_for_publish()

                print(f"Published: {payload}")
                last_timestamp = measurement["timestamp"]

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nJay01 MQTT publisher stopped.")

    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
