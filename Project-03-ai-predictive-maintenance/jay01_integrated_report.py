
import sqlite3
from pathlib import Path
from collections import Counter


BASE_DIR = Path(__file__).resolve().parent

DATABASES = {
    "Project 01": (
        BASE_DIR.parent
        / "Project-01-automated-production-cell"
        / "data"
        / "production.db"
    ),
    "Project 02": (
        BASE_DIR.parent
        / "Project-02-industrial-monitoring-platform"
        / "data"
        / "sqlite"
        / "industrial_monitoring.db"
    ),
    "Project 03": BASE_DIR / "jay01_history.sqlite3",
}


def connect_read_only(path):
    if not path.exists():
        raise FileNotFoundError(f"Database not found: {path}")

    return sqlite3.connect(
        f"file:{path.resolve().as_posix()}?mode=ro",
        uri=True,
        timeout=5,
    )


def report_production():
    print("\n--- PROJECT 01: PRODUCTION ---")

    with connect_read_only(DATABASES["Project 01"]) as db:
        total, ok, defects = db.execute(
            """
            SELECT COUNT(*),
                   SUM(CASE WHEN UPPER(result) = 'OK' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN UPPER(result) = 'DEFECT'
                       THEN 1 ELSE 0 END)
            FROM production
            """
        ).fetchone()

        ok = ok or 0
        defects = defects or 0
        defect_rate = defects / total * 100 if total else 0.0

        print(f"Total records: {total}")
        print(f"OK: {ok}")
        print(f"Defects: {defects}")
        print(f"Defect rate: {defect_rate:.2f}%")

        if total:
            print(
                "Note: Rate uses all stored production records, "
                "not only recent production."
            )


def report_monitoring():
    print("\n--- PROJECT 02: INDUSTRIAL MONITORING ---")

    with connect_read_only(DATABASES["Project 02"]) as db:
        total = db.execute(
            "SELECT COUNT(*) FROM measurements"
        ).fetchone()[0]

        print(f"Total stored measurements: {total}")

        statuses = db.execute(
            """
            SELECT UPPER(COALESCE(status, 'UNKNOWN')) AS status,
                   COUNT(*)
            FROM measurements
            GROUP BY UPPER(COALESCE(status, 'UNKNOWN'))
            ORDER BY COUNT(*) DESC
            """
        ).fetchall()

        print("Measurements by status:")
        for status, count in statuses:
            print(f"  {status}: {count}")

        warning_rows = db.execute(
            """
            SELECT warnings
            FROM measurements
            WHERE warnings IS NOT NULL AND TRIM(warnings) != ''
            """
        ).fetchall()

        warning_counts = Counter()
        for (warnings,) in warning_rows:
            for warning in warnings.split(","):
                warning = warning.strip()
                if warning:
                    warning_counts[warning] += 1

        print("Warning labels across stored records:")
        if warning_counts:
            for warning, count in warning_counts.most_common():
                print(f"  {warning}: {count}")
        else:
            print("  No warning labels recorded.")


def report_maintenance():
    print("\n--- PROJECT 03: PREDICTIVE MAINTENANCE ---")

    with connect_read_only(DATABASES["Project 03"]) as db:
        latest = db.execute(
            """
            SELECT id, timestamp, machine_id, state,
                   temperature_c, vibration_mm_s_rms,
                   current_a, sensor_valid, active_alarms
            FROM measurements
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

        if latest:
            (
                record_id, timestamp, machine_id, state,
                temperature, vibration, current,
                sensor_valid, alarms
            ) = latest

            print(f"Latest record: #{record_id}")
            print(f"Timestamp: {timestamp}")
            print(f"Machine: {machine_id}")
            print(f"State: {state}")
            print(f"Sensor valid: {sensor_valid}")
            print(f"Temperature: {temperature} °C")
            print(f"Vibration: {vibration} mm/s RMS")
            print(f"Current: {current} A")
            print(f"Active alarms: {alarms or 'None'}")
        else:
            print("No maintenance measurements found.")

        total_events = db.execute(
            "SELECT COUNT(*) FROM events"
        ).fetchone()[0]
        print(f"\nTotal recorded machine events: {total_events}")

        event_counts = db.execute(
            """
            SELECT event_type, COUNT(*)
            FROM events
            GROUP BY event_type
            ORDER BY COUNT(*) DESC
            """
        ).fetchall()

        print("Events by type:")
        if event_counts:
            for event_type, count in event_counts:
                print(f"  {event_type}: {count}")
        else:
            print("  No events recorded.")

        recent = db.execute(
            """
            SELECT id, timestamp, event_type, details
            FROM events
            ORDER BY id DESC
            LIMIT 5
            """
        ).fetchall()

        print("Recent events:")
        for event_id, timestamp, event_type, details in recent:
            print(
                f"  #{event_id} | {timestamp} | "
                f"{event_type} | {details}"
            )


def main():
    print("=" * 60)
    print("INDUSTRIAL AUTOMATION - INTEGRATED DATA REPORT")
    print("All source databases are opened read-only.")
    print("=" * 60)

    reports = [
        ("Project 01", report_production),
        ("Project 02", report_monitoring),
        ("Project 03", report_maintenance),
    ]

    for name, report in reports:
        try:
            report()
        except (sqlite3.Error, FileNotFoundError, ValueError) as exc:
            print(f"\n{name} report failed: {exc}")

    print("\n" + "=" * 60)
    print("Report complete.")
    print("Project records remain separate; machine links are unverified.")
    print("=" * 60)


if __name__ == "__main__":
    main()
