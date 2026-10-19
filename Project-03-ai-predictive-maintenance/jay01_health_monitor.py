"""Jay01 health monitor v2.
Separates the latest recorded machine condition from historical fault records.
Reads jay01_history.sqlite3 without modifying it.

Run from the project folder:
    python jay01_health_monitor.py
Optional:
    python jay01_health_monitor.py --limit 50
    python jay01_health_monitor.py --db path/to/jay01_history.sqlite3

All thresholds are fictional simulation values, not real-machine specifications.
"""
import argparse
import sqlite3
from pathlib import Path

THRESHOLDS = {
    "temperature_warning_c": 70.0,
    "temperature_critical_c": 85.0,
    "vibration_warning_mm_s_rms": 4.5,
    "vibration_critical_mm_s_rms": 7.1,
    "current_warning_a": 4.0,
    "current_critical_a": 5.0,
}

def assess_reading(row):
    reasons = []
    critical = False
    warning = False

    if not row["sensor_valid"]:
        critical = True
        reasons.append("Sensor data is invalid")

    checks = [
        ("temperature_c", "Temperature", "°C", 70.0, 85.0, False),
        ("vibration_mm_s_rms", "Vibration", "mm/s RMS", 4.5, 7.1, False),
        ("current_a", "Current", "A", 4.0, 5.0, True),
    ]
    for column, label, unit, warning_limit, critical_limit, strict in checks:
        value = row[column]
        if value is None:
            critical = True
            reasons.append(f"{label} reading is missing")
        elif (value > critical_limit if strict else value >= critical_limit):
            critical = True
            reasons.append(f"Critical {label.lower()}: {value:.2f} {unit}")
        elif (value > warning_limit if strict else value >= warning_limit):
            warning = True
            reasons.append(f"High {label.lower()}: {value:.2f} {unit}")

    if row["state"] == "FAULT":
        critical = True
        reasons.append("Recorded machine state is FAULT")
    elif row["state"] in ("RECOVERY", "MAINTENANCE"):
        warning = True
        reasons.append(f"Recorded machine state is {row['state']}")

    if critical:
        return "CRITICAL", reasons
    if warning:
        return "WARNING", reasons
    return "NORMAL", ["No configured threshold violations detected"]

def print_reading(row, heading):
    health, reasons = assess_reading(row)
    print(f"\n{heading}")
    print(f"Record #{row['id']} | {row['timestamp']} | Machine: {row['machine_id']}")
    print(f"State: {row['state']} | Assessment: {health}")
    print(
        f"Temperature: {row['temperature_c']} °C | "
        f"Vibration: {row['vibration_mm_s_rms']} mm/s RMS | "
        f"Current: {row['current_a']} A | Speed: {row['speed_rpm']} rpm"
    )
    print(f"Sensor valid: {bool(row['sensor_valid'])}")
    print(f"Recorded active alarms: {row['active_alarms'] or 'None'}")
    print("Reasons: " + "; ".join(reasons))
    return health

def main():
    parser = argparse.ArgumentParser(description="Assess Jay01 current condition and recent history.")
    parser.add_argument("--db", default="jay01_history.sqlite3",
                        help="Path to the Jay01 SQLite database")
    parser.add_argument("--limit", type=int, default=20,
                        help="Number of recent historical measurements to inspect")
    args = parser.parse_args()
    db_path = Path(args.db)

    if not db_path.exists():
        raise SystemExit(
            f"Database not found: {db_path.resolve()}\n"
            "Run this script from the folder containing jay01_history.sqlite3 or pass --db."
        )

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    required = {
        "id", "timestamp", "machine_id", "state", "temperature_c",
        "vibration_mm_s_rms", "current_a", "speed_rpm", "sensor_valid",
        "active_alarms",
    }
    columns = {r["name"] for r in con.execute("PRAGMA table_info(measurements)")}
    missing = sorted(required - columns)
    if missing:
        con.close()
        raise SystemExit("Unexpected database schema; missing: " + ", ".join(missing))

    latest = con.execute("""
        SELECT id, timestamp, machine_id, state, temperature_c,
               vibration_mm_s_rms, current_a, speed_rpm, sensor_valid,
               active_alarms
        FROM measurements ORDER BY id DESC LIMIT 1
    """).fetchone()

    history = con.execute("""
        SELECT id, timestamp, machine_id, state, temperature_c,
               vibration_mm_s_rms, current_a, speed_rpm, sensor_valid,
               active_alarms
        FROM measurements ORDER BY id DESC LIMIT ?
    """, (max(1, args.limit),)).fetchall()

    event_count = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    con.close()

    if latest is None:
        print("No measurements found in the database.")
        return

    print("=" * 64)
    print("JAY01 HEALTH MONITOR — V2")
    print(f"Database: {db_path.resolve()}")
    print("Mode: rule-based condition monitoring; not a trained prediction model")
    print("Thresholds are fictional simulation values.")
    print_reading(latest, "LATEST RECORDED CONDITION")
    print(f"\nHISTORICAL REVIEW — latest {len(history)} measurements")
    print(f"Total event records in database: {event_count}")

    counts = {"CRITICAL": 0, "WARNING": 0, "NORMAL": 0}
    historical_faults = []
    for row in history:
        health, reasons = assess_reading(row)
        counts[health] += 1
        if health == "CRITICAL":
            historical_faults.append((row, reasons))

    print("Historical assessments: " + ", ".join(
        f"{key}={counts[key]}" for key in ("CRITICAL", "WARNING", "NORMAL")
    ))
    print("\nRecent critical records (historical; not automatically current faults):")
    if not historical_faults:
        print("None in the inspected window.")
    else:
        for row, reasons in historical_faults:
            print(
                f"- #{row['id']} | {row['timestamp']} | state={row['state']} | "
                f"alarms={row['active_alarms'] or 'None'}"
            )
            print("  " + "; ".join(reasons))

    print("\nInterpretation: the latest record is the latest data stored in SQLite, "
          "not proof of the machine's live condition. The simulator must be running "
          "and recording fresh readings to establish a current condition.")

if __name__ == "__main__":
    main()
