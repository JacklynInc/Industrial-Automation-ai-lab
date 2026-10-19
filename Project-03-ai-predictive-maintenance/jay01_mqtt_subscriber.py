
"""Jay01 MQTT subscriber.

Receives Jay01 telemetry from Mosquitto and stores it in
jay01_history.sqlite3.

Run from the Project-03-ai-predictive-maintenance folder.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


BROKER = "localhost"
PORT = 1883
TOPIC = "factory/jay01/sensors"
DB_PATH = Path(__file__).with_name("jay01_history.sqlite3")


def save_measurement(data):
    """Validate and report MQTT telemetry without duplicating SQLite records."""

    required_fields = [
        "timestamp",
        "machine_id",
        "state",
        "temperature_c",
        "vibration_mm_s_rms",
        "current_a",
        "speed_rpm",
        "sensor_valid",
        "active_alarms",
    ]

    missing = [field for field in required_fields if field not in data]
    if missing:
        print(f"Rejected message: missing fields {missing}")
        return

    print(
        f"MQTT received: machine={data['machine_id']}, "
        f"time={data['timestamp']}, "
        f"state={data['state']}, "
        f"temperature={data['temperature_c']}°C, "
        f"vibration={data['vibration_mm_s_rms']} mm/s RMS, "
        f"current={data['current_a']} A, "
        f"speed={data['speed_rpm']} rpm, "
        f"alarms={data['active_alarms'] or 'None'}"
    )


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"Connected to MQTT broker at {BROKER}:{PORT}")
        client.subscribe(TOPIC)
        print(f"Subscribed to topic: {TOPIC}")
    else:
        print(f"MQTT connection failed: {reason_code}")


def on_message(client, userdata, message):
    try:
        payload = message.payload.decode("utf-8")
        data = json.loads(payload)

        if not isinstance(data, dict):
            print("Skipped message: JSON payload must be an object")
            return

        save_measurement(data)

    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"Invalid MQTT message: {exc}")
    except (sqlite3.Error, KeyError, TypeError, ValueError) as exc:
        print(f"Could not save MQTT measurement: {exc}")


def main():
    if not DB_PATH.exists():
        raise SystemExit(
            f"Database not found: {DB_PATH}\n"
            "Run the Jay01 simulator first to create the database."
        )

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="jay01-sqlite-subscriber",
    )
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"Database: {DB_PATH}")
    print(f"Waiting for messages on {TOPIC} ...")

    try:
        client.connect(BROKER, PORT, keepalive=60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nSubscriber stopped.")
    except OSError as exc:
        print(f"Could not connect to MQTT broker: {exc}")
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
