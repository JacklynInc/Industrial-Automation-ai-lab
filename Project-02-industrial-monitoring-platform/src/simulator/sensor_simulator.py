import random
import time
from datetime import datetime

from src.mqtt.mqtt_client import connect_mqtt, publish_measurement


def generate_measurement():
    measurement = {
        "machine_id": "MOTOR_01",
        "timestamp": datetime.now().isoformat(),
        "temperature_c": round(random.uniform(60, 75), 2),
        "vibration_mms": round(random.uniform(1.5, 3.0), 2),
        "current_a": round(random.uniform(6.0, 8.0), 2),
    }

    return measurement


if __name__ == "__main__":
    client = connect_mqtt()

    for _ in range(5):       
        measurement = generate_measurement()
        publish_measurement(client, measurement)
        time.sleep(2)

    client.disconnect()