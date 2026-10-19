
"""Jay01 Predictive Maintenance — Trend Analysis V4.

Reads historical measurements from SQLite in read-only mode.
Assesses current stored machine condition separately from historical trends.

This is rule-based monitoring, not a trained machine-learning model.
"""

import sqlite3
from pathlib import Path
from statistics import mean, pstdev


DB_PATH = Path(__file__).with_name("jay01_history.sqlite3")
HISTORY_LIMIT = 100
RECENT_LIMIT = 20

# (display label, unit, warning threshold, critical threshold)
METRICS = {
    "temperature_c": ("Temperature", "°C", 70.0, 85.0),
    "vibration_mm_s_rms": (
        "Vibration",
        "mm/s RMS",
        4.5,
        7.1,
    ),
    "current_a": ("Current", "A", 4.0, 5.0),
    "speed_rpm": ("Speed", "rpm", None, None),
}

CRITICAL_ALARMS = {
    "TEMP_CRITICAL",
    "VIB_CRITICAL",
    "MOTOR_OVERLOAD",
    "SENSOR_FAILURE",
}


def connect_database():
    """Open the existing database without allowing writes."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    return sqlite3.connect(
        f"{DB_PATH.resolve().as_uri()}?mode=ro",
        uri=True,
        timeout=10,
    )


def parse_alarms(value):
    """Convert a comma-separated alarm field into a set."""
    if not value:
        return set()

    return {
        alarm.strip()
        for alarm in str(value).split(",")
        if alarm.strip()
    }


def assess_current_health(latest):
    """Assess the latest stored record, not the historical maximum."""
    print("\n--- CURRENT MACHINE HEALTH ---")

    state = str(latest["state"] or "UNKNOWN").upper()
    sensor_valid = bool(latest["sensor_valid"])
    alarms = str(latest["active_alarms"] or "").strip()

    print(f"Latest record: #{latest['id']} | {latest['timestamp']}")
    print(f"Machine state: {state}")
    print(f"Sensor valid: {sensor_valid}")
    print(f"Recorded active alarms: {alarms or 'None'}")

    issues = []
    critical = False
    warning = False

    if not sensor_valid:
        issues.append("Sensor data is invalid.")
        critical = True

    # Evaluate the latest sensor readings.
    for column, details in METRICS.items():
        label, unit, warning_limit, critical_limit = details
        raw_value = latest[column]

        if raw_value is None:
            if column != "speed_rpm" or state == "RUNNING":
                issues.append(f"{label} reading is missing.")
                warning = True
            continue

        value = float(raw_value)

        if critical_limit is not None and value >= critical_limit:
            issues.append(
                f"{label} is critical: {value:.2f} {unit} "
                f"(limit {critical_limit} {unit})."
            )
            critical = True
        elif warning_limit is not None and value >= warning_limit:
            issues.append(
                f"{label} warning: {value:.2f} {unit} "
                f"(limit {warning_limit} {unit})."
            )
            warning = True

    # Machine state is important even when the alarm field is empty.
    if state == "FAULT":
        issues.append(
            "The latest stored machine state is FAULT. "
            "Review the event history before restarting."
        )
        critical = True
    elif state in {"RECOVERY", "STARTING"}:
        issues.append(
            f"The machine is in {state}; normal operation is not confirmed."
        )
        warning = True
    elif state not in {"RUNNING", "STOPPED"}:
        issues.append(f"Unrecognised machine state: {state}.")
        warning = True

    recorded_alarms = parse_alarms(alarms)

    if recorded_alarms:
        issues.append(f"Alarm field is populated: {alarms}")

        if recorded_alarms & CRITICAL_ALARMS:
            critical = True
        else:
            warning = True

    if critical:
        print("HEALTH RESULT: CRITICAL")
    elif warning:
        print("HEALTH RESULT: WARNING / CHECK REQUIRED")
    elif state == "RUNNING":
        print("HEALTH RESULT: NORMAL — no configured limits exceeded.")
    elif state == "STOPPED":
        print(
            "HEALTH RESULT: STOPPED — operational health "
            "is not being demonstrated."
        )
    else:
        print("HEALTH RESULT: NOT FULLY ASSESSED")

    if issues:
        print("Findings:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Findings: No configured issues detected in the latest record.")

    print(
        "Scope: this assessment describes the latest database record, "
        "not necessarily the machine's live condition."
    )


def assess_record(row):
    """Classify a historical record using the configured rules."""
    state = str(row["state"] or "UNKNOWN").upper()
    alarms = parse_alarms(row["active_alarms"])

    if not bool(row["sensor_valid"]):
        return "CRITICAL", ["Sensor data is invalid"]

    if state == "FAULT":
        return "CRITICAL", ["Machine state is FAULT"]

    if alarms & CRITICAL_ALARMS:
        return "CRITICAL", [f"Critical alarm: {', '.join(sorted(alarms & CRITICAL_ALARMS))}"]

    findings = []

    if alarms:
        findings.append(f"Active alarms: {', '.join(sorted(alarms))}")

    if state in {"RECOVERY", "STARTING"}:
        findings.append(f"Machine state is {state}")

    for column, details in METRICS.items():
        label, unit, warning_limit, critical_limit = details
        raw_value = row[column]

        if raw_value is None:
            continue

        value = float(raw_value)

        if critical_limit is not None and value >= critical_limit:
            findings.append(f"{label} critical: {value:.2f} {unit}")
        elif warning_limit is not None and value >= warning_limit:
            findings.append(f"{label} warning: {value:.2f} {unit}")

    if any("critical:" in item.lower() for item in findings):
        return "CRITICAL", findings

    if findings:
        return "WARNING", findings

    if state != "RUNNING":
        return "OTHER", [f"Machine state is {state}"]

    return "NORMAL", ["No configured limits exceeded"]


def print_historical_review(rows):
    """Summarise historical records without treating them as current faults."""
    print(f"\n--- HISTORICAL REVIEW — latest {len(rows)} measurements ---")

    counts = {"CRITICAL": 0, "WARNING": 0, "NORMAL": 0, "OTHER": 0}

    for row in rows:
        category, _ = assess_record(row)
        counts[category] += 1

    print(f"Historical assessments: {counts}")

    critical_rows = [
        (row, assess_record(row))
        for row in rows
        if assess_record(row)[0] == "CRITICAL"
    ]

    if critical_rows:
        print("\nRecent critical records (historical, not automatically current):")

        # Display newest first.
        for row, (category, findings) in critical_rows[-5:][::-1]:
            print(
                f"- #{row['id']} | {row['timestamp']} | "
                f"state={row['state']} | "
                f"alarms={row['active_alarms'] or 'None'}"
            )
            for finding in findings:
                print(f"    {finding}")
    else:
        print("No critical records found in this review window.")


def print_running_trends(rows):
    """Calculate descriptive statistics from valid RUNNING records only."""
    running_rows = [
        row for row in rows
        if str(row["state"] or "").upper() == "RUNNING"
        and bool(row["sensor_valid"])
    ]

    print("\n--- RUNNING-STATE TREND ANALYSIS ---")
    print(f"Valid RUNNING records: {len(running_rows)}")

    if len(running_rows) < 2:
        print("Not enough valid RUNNING records to calculate trends.")
        return

    for column, details in METRICS.items():
        label, unit, warning_limit, critical_limit = details

        values = [
            float(row[column])
            for row in running_rows
            if row[column] is not None
        ]

        if not values:
            print(f"{label}: no valid values available.")
            continue

        average = mean(values)
        spread = pstdev(values)
        minimum = min(values)
        maximum = max(values)

        print(
            f"{label}: mean={average:.2f} {unit}, "
            f"std_dev={spread:.2f}, min={minimum:.2f}, "
            f"max={maximum:.2f}"
        )

        if critical_limit is not None and maximum >= critical_limit:
            print(
                f"  Trend flag: at least one RUNNING record reached "
                f"the critical threshold ({critical_limit} {unit})."
            )
        elif warning_limit is not None and maximum >= warning_limit:
            print(
                f"  Trend flag: at least one RUNNING record reached "
                f"the warning threshold ({warning_limit} {unit})."
            )

    print(
        "Interpretation: these are descriptive statistics, "
        "not a forecast of future failure."
    )


def main():
    print("=" * 64)
    print("JAY01 TREND ANALYSIS — V4")
    print(f"Database: {DB_PATH}")
    print("Mode: read-only, rule-based condition monitoring")
    print("Thresholds are illustrative simulation values.")
    print("=" * 64)

    with connect_database() as connection:
        connection.row_factory = sqlite3.Row

        # Fetch enough records for the current condition and trend review.
        rows = connection.execute(
            """
            SELECT
                id,
                timestamp,
                machine_id,
                state,
                temperature_c,
                vibration_mm_s_rms,
                current_a,
                speed_rpm,
                sensor_valid,
                active_alarms
            FROM measurements
            ORDER BY id DESC
            LIMIT ?
            """,
            (HISTORY_LIMIT,),
        ).fetchall()

        event_count = connection.execute(
            "SELECT COUNT(*) FROM events"
        ).fetchone()[0]

    if not rows:
        print("\nNo measurements found. Run the Jay01 simulator first.")
        return

    # Query returned newest-first; retain the true latest record separately.
    latest = rows[0]
    chronological_rows = list(reversed(rows))

    print(f"Measurement records inspected: {len(rows)}")
    print(f"Total event records in database: {event_count}")

    assess_current_health(latest)

    print_historical_review(rows[:RECENT_LIMIT])
    print_running_trends(chronological_rows)

    print("\n--- INTERPRETATION ---")
    print(
        "The current assessment uses the latest stored measurement. "
        "Historical alarms and faults remain historical; they do not "
        "automatically mean the machine is currently faulted."
    )
    print(
        "For a live assessment, ensure the simulator is recording fresh "
        "measurements and check the timestamp."
    )


if __name__ == "__main__":
    try:
        main()
    except (sqlite3.Error, OSError, KeyError, ValueError) as exc:
        raise SystemExit(f"Trend analysis failed: {exc}")
