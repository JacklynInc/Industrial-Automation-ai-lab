
"""Jay01 Maintenance Alerts
Rule-based maintenance alerts using the existing SQLite history.
This is a simulation feature, not a trained predictive model.
"""

import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).with_name("jay01_history.sqlite3")

# Illustrative thresholds for this simulation.
THRESHOLDS = {
    "temperature_c": {
        "label": "Temperature",
        "unit": "°C",
        "warning": 70.0,
        "critical": 85.0,
    },
    "vibration_mm_s_rms": {
        "label": "Vibration",
        "unit": "mm/s RMS",
        "warning": 4.5,
        "critical": 7.1,
    },
    "current_a": {
        "label": "Motor current",
        "unit": "A",
        "warning": 4.0,
        "critical": 5.0,
    },
}

CRITICAL_ALARMS = {
    "TEMP_CRITICAL",
    "VIB_CRITICAL",
    "MOTOR_OVERLOAD",
    "SENSOR_FAILURE",
}


def get_latest_measurement():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    connection = sqlite3.connect(
        f"file:{DB_PATH.as_posix()}?mode=ro",
        uri=True,
    )
    connection.row_factory = sqlite3.Row

    try:
        return connection.execute(
            """
            SELECT *
            FROM measurements
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
    finally:
        connection.close()


def evaluate_measurement(record):
    findings = []
    status = "NORMAL"

    state = str(record["state"] or "UNKNOWN").upper()
    sensor_valid = bool(record["sensor_valid"])

    if not sensor_valid:
        status = "CRITICAL"
        findings.append("Sensor data is invalid. Inspect the sensor.")

    if state == "FAULT":
        status = "CRITICAL"
        findings.append("Machine is in FAULT state. Investigate before restarting.")
    elif state == "RECOVERY":
        if status != "CRITICAL":
            status = "WARNING"
        findings.append("Machine is recovering. Complete the required checks.")
    elif state == "STARTING":
        if status != "CRITICAL":
            status = "WARNING"
        findings.append("Machine is starting. Confirm normal operation.")
    elif state == "STOPPED":
        if status != "CRITICAL":
            status = "INFO"
        findings.append("Machine is stopped; running condition cannot be assessed.")
    elif state != "RUNNING":
        if status != "CRITICAL":
            status = "WARNING"
        findings.append(f"Machine state is not recognised: {state}.")

    for column, config in THRESHOLDS.items():
        value = record[column]

        if value is None:
            if status != "CRITICAL":
                status = "WARNING"
            findings.append(f"{config['label']} reading is missing.")
            continue

        value = float(value)

        if value >= config["critical"]:
            status = "CRITICAL"
            findings.append(
                f"{config['label']} CRITICAL: {value:.2f} "
                f"{config['unit']} (limit {config['critical']})."
            )
        elif value >= config["warning"]:
            if status not in {"CRITICAL"}:
                status = "WARNING"
            findings.append(
                f"{config['label']} WARNING: {value:.2f} "
                f"{config['unit']} (limit {config['warning']})."
            )

    alarms = {
        item.strip()
        for item in str(record["active_alarms"] or "").split(",")
        if item.strip()
    }

    if alarms:
        findings.append("Active alarm(s): " + ", ".join(sorted(alarms)))

        if alarms & CRITICAL_ALARMS:
            status = "CRITICAL"
        elif status not in {"CRITICAL"}:
            status = "WARNING"

    if not findings:
        findings.append("No configured threshold violations detected.")

    return status, findings



def analyse_rising_trend():
    """Assess recent temperature, vibration, and current trends."""

    metrics = {
        "temperature_c": {
            "name": "Temperature",
            "unit": "°C",
            "warning": 70.0,
            "critical": 85.0,
            "minimum_rise": 5.0,
        },
        "vibration_mm_s_rms": {
            "name": "Vibration",
            "unit": "mm/s RMS",
            "warning": 4.5,
            "critical": 7.1,
            "minimum_rise": 0.5,
        },
        "current_a": {
            "name": "Current",
            "unit": "A",
            "warning": 4.0,
            "critical": 5.0,
            "minimum_rise": 0.3,
        },
    }

    connection = sqlite3.connect(
        f"file:{DB_PATH.as_posix()}?mode=ro",
        uri=True,
    )
    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute(
            """
            SELECT id, timestamp, state, sensor_valid,
                   temperature_c, vibration_mm_s_rms, current_a
            FROM measurements
            WHERE UPPER(state) = 'RUNNING'
              AND sensor_valid = 1
            ORDER BY id DESC
            LIMIT 20
            """
        ).fetchall()
    finally:
        connection.close()

    rows = list(reversed(rows))

    print("\n--- EARLY-WARNING TREND ANALYSIS ---")

    if len(rows) < 10:
        print(
            f"Not enough valid RUNNING readings ({len(rows)}). "
            "At least 10 are required."
        )
        return

    midpoint = len(rows) // 2
    earlier = rows[:midpoint]
    recent = rows[midpoint:]

    for column, config in metrics.items():
        old_values = [
            float(row[column])
            for row in earlier
            if row[column] is not None
        ]
        new_values = [
            float(row[column])
            for row in recent
            if row[column] is not None
        ]

        name = config["name"]
        unit = config["unit"]

        if not old_values or not new_values:
            print(f"{name}: insufficient data for trend analysis.")
            continue

        old_mean = sum(old_values) / len(old_values)
        new_mean = sum(new_values) / len(new_values)
        change = new_mean - old_mean

        print(f"\n{name}")
        print(f"Earlier average: {old_mean:.2f} {unit}")
        print(f"Recent average:  {new_mean:.2f} {unit}")
        print(f"Change:          {change:+.2f} {unit}")

        if new_mean >= config["critical"]:
            print("TREND STATUS: CRITICAL LEVEL")
        elif new_mean >= config["warning"]:
            print("TREND STATUS: WARNING THRESHOLD REACHED")
        elif (
            change >= config["minimum_rise"]
            and new_mean >= config["warning"] * 0.70
        ):
            print("TREND STATUS: EARLY WARNING - rising trend")
        else:
            print("TREND STATUS: No rising-trend warning")




def main():
    record = get_latest_measurement()

    if record is None:
        print("No measurements found. Run the Jay01 simulator first.")
        return

    status, findings = evaluate_measurement(record)

    print("=" * 55)
    print("JAY01 MAINTENANCE ALERT")
    print("=" * 55)
    print(f"Record: #{record['id']}")
    print(f"Timestamp: {record['timestamp']}")
    print(f"Machine state: {record['state']}")
    print(f"Temperature: {record['temperature_c']} °C")
    print(f"Vibration: {record['vibration_mm_s_rms']} mm/s RMS")
    print(f"Current: {record['current_a']} A")
    print(f"Status: {status}")

    print("\nFindings:")
    for finding in findings:
        print(f"- {finding}")

    print("\nNote: This checks the latest stored reading.")
    print("Thresholds are illustrative simulation values.")

    print("\nRunning trend analysis...")
    analyse_rising_trend()


if __name__ == "__main__":
    try:
        main()
    except (sqlite3.Error, FileNotFoundError, KeyError) as exc:
        raise SystemExit(
            f"Could not evaluate maintenance status: {exc}"
        )
