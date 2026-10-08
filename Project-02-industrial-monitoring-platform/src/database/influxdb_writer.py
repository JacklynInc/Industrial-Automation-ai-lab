from influxdb_client_3 import InfluxDBClient3, Point


INFLUXDB_HOST = "http://localhost:8181"
DATABASE = "industrial_monitoring"


def write_measurement(measurement):
    client = InfluxDBClient3(
        host=INFLUXDB_HOST,
        database=DATABASE,
        token="dev-token"
    )

    point = (
        Point("motor")
        .tag("machine_id", measurement["machine_id"])
        .field("temperature_c", measurement["temperature_c"])
        .field("vibration_mms", measurement["vibration_mms"])
        .field("current_a", measurement["current_a"])
    )

    client.write(point)
    client.close()

    print(f"Written to InfluxDB: {measurement}")