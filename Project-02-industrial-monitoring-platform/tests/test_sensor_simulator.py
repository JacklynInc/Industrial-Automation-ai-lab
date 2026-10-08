from src.simulator.sensor_simulator import generate_measurement


def test_measurement_values():
    data = generate_measurement()

    assert data["machine_id"] == "MOTOR_01"
    assert 60 <= data["temperature_c"] <= 75
    assert 1.5 <= data["vibration_mms"] <= 3.0
    assert 6.0 <= data["current_a"] <= 8.0