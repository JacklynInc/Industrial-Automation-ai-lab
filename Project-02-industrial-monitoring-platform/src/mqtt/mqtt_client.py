import json
import paho.mqtt.client as mqtt
from src.database.database import save_measurement
from src.processing.data_processor import process_measurement
from src.database.influxdb_writer import write_measurement
from src.monitoring.n8n_alert import send_alert


BROKER = "localhost"
PORT = 1883
TOPIC = "factory/motor01/sensors"


def connect_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    client.connect(BROKER, PORT)

    return client


def publish_measurement(client, measurement):
    payload = json.dumps(measurement)
    result = client.publish(TOPIC, payload)
    result.wait_for_publish()

    print(f"Published: {payload}")

def on_message(client, userdata, message):
    payload = message.payload.decode()
    measurement = json.loads(payload)
    processed_measurement = process_measurement(measurement)
    send_alert(processed_measurement)
    save_measurement(processed_measurement)
    write_measurement(processed_measurement)
    print(f"Processed: {processed_measurement}")


def subscribe_to_measurements():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    client.on_message = on_message

    client.connect(BROKER, PORT)
    client.subscribe(TOPIC)

    print(f"Listening on: {TOPIC}")

    client.loop_forever()

