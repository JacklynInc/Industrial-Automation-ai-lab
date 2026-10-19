"""
Jay01 - Simulated Conveyor Drive System
Version: 0.1

Educational software simulation only. Not for controlling real machinery.

Commands:
  start
  stop
  tick [seconds]
  status
  inject temp
  inject vibration
  inject overload
  inject sensor
  clearfault
  reset
  help
  exit

The simulation advances only when you run `tick`, so tests are repeatable.
"""

from __future__ import annotations

import argparse
import random
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


MACHINE_ID = "Jay01"
DB_PATH = Path("jay01_history.sqlite3")

MOTOR_RATED_POWER_KW = 1.5
MOTOR_NOMINAL_SPEED_RPM = 1450.0
SENSOR_SAMPLE_INTERVAL_SECONDS = 1
SENSOR_STALE_TIMEOUT_SECONDS = 5
SPEED_DEVIATION_TOLERANCE_PERCENT = 10.0
SPEED_DEVIATION_DURATION_SECONDS = 5

TEMP_WARNING_C = 70.0
TEMP_CRITICAL_C = 85.0
VIBRATION_WARNING_MM_S_RMS = 4.5
VIBRATION_CRITICAL_MM_S_RMS = 7.1
CURRENT_WARNING_A = 4.0
CURRENT_CRITICAL_A = 5.0

STATES = {
    "STOPPED", "STARTING", "RUNNING", "WARNING",
    "FAULT", "MAINTENANCE", "RECOVERY"
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class HistoryStore:
    """Small SQLite history store for measurements and machine events."""

    def __init__(self, path: Path = DB_PATH) -> None:
        self.connection = sqlite3.connect(path)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                machine_id TEXT NOT NULL,
                state TEXT NOT NULL,
                temperature_c REAL,
                vibration_mm_s_rms REAL,
                current_a REAL,
                speed_rpm REAL,
                sensor_valid INTEGER NOT NULL,
                active_alarms TEXT NOT NULL
            )
        """)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                machine_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                details TEXT NOT NULL
            )
        """)
        self.connection.commit()

    def event(self, event_type: str, details: str) -> None:
        self.connection.execute(
            "INSERT INTO events (timestamp, machine_id, event_type, details) VALUES (?, ?, ?, ?)",
            (utc_now(), MACHINE_ID, event_type, details),
        )
        self.connection.commit()

    def measurement(self, machine: "Jay01Machine") -> None:
        self.connection.execute(
            """INSERT INTO measurements
            (timestamp, machine_id, state, temperature_c, vibration_mm_s_rms,
             current_a, speed_rpm, sensor_valid, active_alarms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                utc_now(), MACHINE_ID, machine.state,
                round(machine.temperature_c, 2),
                round(machine.vibration_mm_s_rms, 2),
                round(machine.current_a, 2),
                round(machine.speed_rpm, 2),
                int(machine.sensor_valid),
                ",".join(sorted(machine.active_alarms)),
            ),
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()


@dataclass
class Jay01Machine:
    store: HistoryStore
    state: str = "STOPPED"
    temperature_c: float = 25.0
    vibration_mm_s_rms: float = 1.2
    current_a: float = 0.0
    speed_rpm: float = 0.0
    sensor_valid: bool = True
    runtime_seconds: int = 0
    active_alarms: set[str] = field(default_factory=set)
    injected_fault: str | None = None
    speed_deviation_seconds: int = 0
    sensor_missing_seconds: int = 0

    def log_state(self, reason: str) -> None:
        self.store.event("STATE_CHANGE", f"{self.state}: {reason}")

    def set_state(self, new_state: str, reason: str) -> None:
        if new_state not in STATES:
            raise ValueError(f"Unknown state: {new_state}")
        if self.state != new_state:
            previous = self.state
            self.state = new_state
            self.store.event("STATE_CHANGE", f"{previous} -> {new_state}: {reason}")

    def add_alarm(self, alarm_id: str, severity: str, details: str) -> None:
        if alarm_id not in self.active_alarms:
            self.active_alarms.add(alarm_id)
            self.store.event("ALARM_ACTIVATED", f"{alarm_id} [{severity}]: {details}")

    def clear_alarm(self, alarm_id: str) -> None:
        if alarm_id in self.active_alarms:
            self.active_alarms.remove(alarm_id)
            self.store.event("ALARM_CLEARED", alarm_id)

    def start(self) -> str:
        if self.state in {"FAULT", "MAINTENANCE", "RECOVERY"}:
            return f"Start rejected: machine is in {self.state}."
        if any(a in self.active_alarms for a in {
            "TEMP_CRITICAL", "VIB_CRITICAL", "MOTOR_OVERLOAD", "SENSOR_FAILURE"
        }):
            return "Start rejected: a blocking alarm is active."
        if self.state in {"STOPPED", "WARNING"}:
            self.set_state("STARTING", "start command accepted")
            self.store.event("COMMAND", "START")
            return "Starting Jay01. Run `tick 3` to advance the start sequence."
        return f"Start ignored: machine is already {self.state}."

    def stop(self) -> str:
        self.store.event("COMMAND", "STOP")
        self.speed_rpm = 0.0
        self.current_a = 0.0
        if self.state != "FAULT":
            self.set_state("STOPPED", "stop command")
        return "Jay01 stop command processed."

    def inject(self, fault: str) -> str:
        allowed = {"temp", "vibration", "overload", "sensor"}
        if fault not in allowed:
            return "Unknown fault. Use: temp, vibration, overload, sensor."
        self.injected_fault = fault
        self.store.event("FAULT_INJECTION", fault)
        if fault == "temp":
            self.temperature_c = 86.0
        elif fault == "vibration":
            self.vibration_mm_s_rms = 7.2
        elif fault == "overload":
            self.current_a = 5.2
        elif fault == "sensor":
            self.sensor_valid = False
            self.sensor_missing_seconds = SENSOR_STALE_TIMEOUT_SECONDS
        return f"Injected simulated {fault} fault."

    def clear_injected_fault(self) -> str:
        fault = self.injected_fault
        if fault is None:
            return "No injected fault is active."
        if fault == "temp":
            self.temperature_c = 55.0
        elif fault == "vibration":
            self.vibration_mm_s_rms = 2.0
        elif fault == "overload":
            self.current_a = 3.0 if self.state in {"RUNNING", "WARNING"} else 0.0
        elif fault == "sensor":
            self.sensor_valid = True
            self.sensor_missing_seconds = 0
        self.store.event("FAULT_INJECTION_CLEARED", fault)
        self.injected_fault = None
        return f"Cleared injected {fault} condition. Use `reset` if a fault remains latched."

    def reset(self) -> str:
        critical = {"TEMP_CRITICAL", "VIB_CRITICAL", "MOTOR_OVERLOAD", "SENSOR_FAILURE"}
        if critical.intersection(self.active_alarms):
            return "Reset rejected: clear the cause of the critical alarm first."
        self.store.event("COMMAND", "RESET/ACKNOWLEDGE")
        if self.state == "RECOVERY":
            self.set_state("STOPPED", "recovery checks completed; manual restart required")
            return "Recovery complete. Jay01 is STOPPED; use `start` when ready."
        self.set_state("RECOVERY", "fault acknowledged; recovery checks required")
        return "Fault acknowledged. Run `tick 1`, then `reset` again to complete recovery."

    def evaluate(self) -> None:
        # Temperature alarms
        if self.temperature_c >= TEMP_CRITICAL_C:
            self.add_alarm("TEMP_CRITICAL", "CRITICAL", f"temperature={self.temperature_c:.1f} C")
        elif self.temperature_c >= TEMP_WARNING_C:
            self.add_alarm("TEMP_HIGH", "WARNING", f"temperature={self.temperature_c:.1f} C")
        else:
            self.clear_alarm("TEMP_HIGH")
            self.clear_alarm("TEMP_CRITICAL")

        # Vibration alarms
        if self.vibration_mm_s_rms >= VIBRATION_CRITICAL_MM_S_RMS:
            self.add_alarm("VIB_CRITICAL", "CRITICAL", f"vibration={self.vibration_mm_s_rms:.1f} mm/s RMS")
        elif self.vibration_mm_s_rms >= VIBRATION_WARNING_MM_S_RMS:
            self.add_alarm("VIB_HIGH", "WARNING", f"vibration={self.vibration_mm_s_rms:.1f} mm/s RMS")
        else:
            self.clear_alarm("VIB_HIGH")
            self.clear_alarm("VIB_CRITICAL")

        # Current alarms
        if self.current_a > CURRENT_CRITICAL_A:
            self.add_alarm("MOTOR_OVERLOAD", "CRITICAL", f"current={self.current_a:.1f} A")
        elif self.current_a > CURRENT_WARNING_A:
            self.add_alarm("CURRENT_HIGH", "WARNING", f"current={self.current_a:.1f} A")
        else:
            self.clear_alarm("CURRENT_HIGH")
            self.clear_alarm("MOTOR_OVERLOAD")

        # Simulated sensor freshness
        if not self.sensor_valid:
            self.sensor_missing_seconds += 1
        else:
            self.sensor_missing_seconds = 0
        if self.sensor_missing_seconds >= SENSOR_STALE_TIMEOUT_SECONDS:
            self.add_alarm("SENSOR_FAILURE", "CRITICAL", "required sensor data is invalid/stale")
        elif not self.sensor_valid:
            self.add_alarm("SENSOR_FAILURE", "WARNING", "sensor signal is invalid")
        else:
            self.clear_alarm("SENSOR_FAILURE")

        # Speed deviation only while running.
        if self.state == "RUNNING" and self.speed_rpm > 0:
            low = MOTOR_NOMINAL_SPEED_RPM * (1 - SPEED_DEVIATION_TOLERANCE_PERCENT / 100)
            high = MOTOR_NOMINAL_SPEED_RPM * (1 + SPEED_DEVIATION_TOLERANCE_PERCENT / 100)
            if not (low <= self.speed_rpm <= high):
                self.speed_deviation_seconds += 1
            else:
                self.speed_deviation_seconds = 0
            if self.speed_deviation_seconds >= SPEED_DEVIATION_DURATION_SECONDS:
                self.add_alarm("SPEED_DEVIATION", "WARNING", f"speed={self.speed_rpm:.1f} rpm")
            else:
                self.clear_alarm("SPEED_DEVIATION")
        else:
            self.speed_deviation_seconds = 0
            self.clear_alarm("SPEED_DEVIATION")

        critical_ids = {"TEMP_CRITICAL", "VIB_CRITICAL", "MOTOR_OVERLOAD", "SENSOR_FAILURE"}
        if critical_ids.intersection(self.active_alarms):
            self.speed_rpm = 0.0
            self.current_a = 0.0
            self.set_state("FAULT", "critical alarm active")
        elif self.state == "RUNNING" and self.active_alarms:
            self.set_state("WARNING", "non-critical alarm active")
        elif self.state == "WARNING" and not self.active_alarms:
            self.set_state("RUNNING", "warning conditions cleared")

    def tick(self, seconds: int = 1) -> str:
        if seconds < 1 or seconds > 3600:
            return "Tick duration must be between 1 and 3600 seconds."
        for _ in range(seconds):
            if self.state == "STARTING":
                self.speed_rpm = min(MOTOR_NOMINAL_SPEED_RPM, self.speed_rpm + 500)
                self.current_a = 3.0
                if self.speed_rpm >= MOTOR_NOMINAL_SPEED_RPM:
                    self.speed_rpm = MOTOR_NOMINAL_SPEED_RPM
                    self.set_state("RUNNING", "nominal speed reached")
            elif self.state in {"RUNNING", "WARNING"}:
                if self.injected_fault is None:
                    self.temperature_c = min(68.0, self.temperature_c + 0.08)
                    self.vibration_mm_s_rms = max(
                        0.8, min(3.0, self.vibration_mm_s_rms + random.uniform(-0.08, 0.08))
                    )
                    self.current_a = max(2.5, min(3.8, 3.2 + random.uniform(-0.15, 0.15)))
                self.speed_rpm = MOTOR_NOMINAL_SPEED_RPM + random.uniform(-12, 12)
                self.runtime_seconds += 1
            elif self.state in {"STOPPED", "FAULT", "MAINTENANCE", "RECOVERY"}:
                if self.state != "FAULT":
                    self.speed_rpm = 0.0
                    self.current_a = 0.0
            self.evaluate()
            self.store.measurement(self)
        return f"Advanced simulation by {seconds} second(s)."

    def status(self) -> str:
        alarms = ", ".join(sorted(self.active_alarms)) or "None"
        sensor = "VALID" if self.sensor_valid else "INVALID"
        return (
            f"\n{MACHINE_ID} STATUS\n"
            f"State: {self.state}\n"
            f"Temperature: {self.temperature_c:.1f} °C\n"
            f"Vibration: {self.vibration_mm_s_rms:.2f} mm/s RMS\n"
            f"Current: {self.current_a:.2f} A\n"
            f"Speed: {self.speed_rpm:.1f} rpm\n"
            f"Sensor status: {sensor}\n"
            f"Runtime: {self.runtime_seconds} simulated seconds\n"
            f"Active alarms: {alarms}\n"
        )


def print_help() -> None:
    print("""
Commands:
  start              Start the simulated machine
  stop               Stop the simulated machine
  tick [seconds]     Advance simulated time (default 1 second)
  status             Show current state and sensor values
  inject temp        Inject critical overheating
  inject vibration   Inject critical vibration
  inject overload    Inject motor overload
  inject sensor      Simulate a failed sensor
  clearfault         Remove the currently injected condition
  reset              Acknowledge fault / enter recovery
  help               Show commands
  exit               Exit and close the database
""")


def main() -> None:
    parser = argparse.ArgumentParser(description="Jay01 conveyor drive simulator")
    parser.add_argument("--db", default=str(DB_PATH), help="SQLite database path")
    args = parser.parse_args()

    store = HistoryStore(Path(args.db))
    machine = Jay01Machine(store=store)
    print(f"{MACHINE_ID} simulator v0.1 — software simulation only")
    print(f"History database: {args.db}")
    print_help()

    try:
        while True:
            try:
                raw = input("Jay01> ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not raw:
                continue
            parts = raw.split()
            command = parts[0]
            if command == "exit":
                break
            elif command == "help":
                print_help()
            elif command == "status":
                print(machine.status())
            elif command == "start":
                print(machine.start())
            elif command == "stop":
                print(machine.stop())
            elif command == "tick":
                try:
                    seconds = int(parts[1]) if len(parts) > 1 else 1
                except ValueError:
                    print("Use a whole number of seconds, e.g. `tick 5`.")
                    continue
                print(machine.tick(seconds))
            elif command == "inject" and len(parts) == 2:
                print(machine.inject(parts[1]))
            elif command == "clearfault":
                print(machine.clear_injected_fault())
            elif command == "reset":
                print(machine.reset())
            else:
                print("Unknown command. Type `help`.")
    finally:
        store.close()
        print("Jay01 simulator closed. Measurement and event history saved.")


if __name__ == "__main__":
    main()
