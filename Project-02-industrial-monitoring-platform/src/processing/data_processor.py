TEMPERATURE_WARNING = 70.0
TEMPERATURE_CRITICAL = 80.0

VIBRATION_WARNING = 2.5
VIBRATION_CRITICAL = 3.5

CURRENT_WARNING = 7.5
CURRENT_CRITICAL = 9.0


def process_measurement(measurement):
    warnings = []
    critical = []

    # Temperature
    if measurement["temperature_c"] > TEMPERATURE_CRITICAL:
        critical.append("CRITICAL_TEMPERATURE")
    elif measurement["temperature_c"] > TEMPERATURE_WARNING:
        warnings.append("HIGH_TEMPERATURE")

    # Vibration
    if measurement["vibration_mms"] > VIBRATION_CRITICAL:
        critical.append("CRITICAL_VIBRATION")
    elif measurement["vibration_mms"] > VIBRATION_WARNING:
        warnings.append("HIGH_VIBRATION")

    # Current
    if measurement["current_a"] > CURRENT_CRITICAL:
        critical.append("CRITICAL_CURRENT")
    elif measurement["current_a"] > CURRENT_WARNING:
        warnings.append("HIGH_CURRENT")

    if critical:
        status = "CRITICAL"
        all_warnings = warnings + critical
    elif warnings:
        status = "WARNING"
        all_warnings = warnings
    else:
        status = "NORMAL"
        all_warnings = []

    return {
        **measurement,
        "status": status,
        "warnings": all_warnings
    }