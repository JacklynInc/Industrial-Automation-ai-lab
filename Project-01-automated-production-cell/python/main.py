import sqlite3
import time
from datetime import datetime

import requests

from ads_client import (
    connect_to_plc,
    read_production_data,
    disconnect_from_plc,
)
from statistics import get_production_statistics


# ============================================================
# Configuration
# ============================================================

N8N_WEBHOOK_URL = (
    "https://j01.app.n8n.cloud/webhook/Production-result"
)


# ============================================================
# Database
# ============================================================

connection = sqlite3.connect("data/production.db")
cursor = connection.cursor()


# ============================================================
# Beckhoff PLC
# ============================================================

plc = connect_to_plc()

print("Connected to TwinCAT PLC via ADS")


# ============================================================
# Production event handling
# ============================================================
def monitor_plc_fault(plc, last_fault_code):
    """Detect and report new PLC fault events."""

    production_data = read_production_data(plc)

    fault_code = production_data["fault_code"]
    machine_status = production_data["machine_status"]

    if fault_code != 0 and fault_code != last_fault_code:
        print(
            f"PLC FAULT detected: "
            f"Code={fault_code} | "
            f"Status={machine_status}"
        )

    return fault_code

def record_plc_production(
    plc,
    last_total_parts,
    last_ok_parts,
    last_defect_parts,
):
    """
    Detect a newly completed PLC production event,
    determine whether it was OK or DEFECT,
    store it in SQLite, and send the result to n8n.
    """

    production_data = read_production_data(plc)

    current_total_parts = production_data["total_parts"]
    current_ok_parts = production_data["ok_parts"]
    current_defect_parts = production_data["defect_parts"]

    # --------------------------------------------------------
    # No new production event
    # --------------------------------------------------------

    if current_total_parts <= last_total_parts:
        return (
            last_total_parts,
            last_ok_parts,
            last_defect_parts,
        )

    # --------------------------------------------------------
    # Determine production result from PLC counters
    # --------------------------------------------------------

    if current_ok_parts > last_ok_parts:
        result = "OK"

    elif current_defect_parts > last_defect_parts:
        result = "DEFECT"

    else:
        print(
            "Warning: TotalParts increased, "
            "but no result counter increased."
        )

        return (
            current_total_parts,
            current_ok_parts,
            current_defect_parts,
        )

    # --------------------------------------------------------
    # Timestamp
    # --------------------------------------------------------

    timestamp = datetime.now().isoformat()

    # --------------------------------------------------------
    # Store production result in SQLite
    # --------------------------------------------------------

    cursor.execute(
        """
        INSERT INTO production (result, timestamp)
        VALUES (?, ?)
        """,
        (result, timestamp),
    )

    connection.commit()

    # --------------------------------------------------------
    # Calculate production statistics
    # --------------------------------------------------------

    total, ok, defect, defect_rate = get_production_statistics(
        connection
    )

    production_id = cursor.lastrowid

    # --------------------------------------------------------
    # Send production data to n8n
    # --------------------------------------------------------

    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json={
                "production_id": production_id,
                "result": result,
                "timestamp": timestamp,
                "total_parts": total,
                "ok_parts": ok,
                "defect_parts": defect,
                "defect_rate": defect_rate,
            },
            timeout=10,
        )

        print(f"n8n response: {response.status_code}")

    except requests.RequestException as error:
        print(f"n8n connection failed: {error}")

    # --------------------------------------------------------
    # Display production event
    # --------------------------------------------------------

    print(
        f"PLC production recorded: "
        f"ID={production_id} | "
        f"Result={result} | "
        f"Total={total} | "
        f"OK={ok} | "
        f"DEFECT={defect} | "
        f"Defect rate={defect_rate:.2f}%"
    )

    # --------------------------------------------------------
    # Update previous PLC counters
    # --------------------------------------------------------

    return (
        current_total_parts,
        current_ok_parts,
        current_defect_parts,
    )


# ============================================================
# Initial PLC counter snapshot
# ============================================================

initial_data = read_production_data(plc)

last_total_parts = initial_data["total_parts"]
last_ok_parts = initial_data["ok_parts"]
last_defect_parts = initial_data["defect_parts"]
last_fault_code = initial_data["fault_code"]

print(
    f"Starting PLC monitor. "
    f"Current total parts: {last_total_parts}"
)


# ============================================================
# PLC monitoring loop
# ============================================================

try:

    while True:

        (
            last_total_parts,
            last_ok_parts,
            last_defect_parts,
        ) = record_plc_production(
            plc,
            last_total_parts,
            last_ok_parts,
            last_defect_parts,
        )
        last_fault_code = monitor_plc_fault(
            plc,last_fault_code,
)
        time.sleep(1)


except KeyboardInterrupt:

    print("\nPLC monitoring stopped.")


finally:

    disconnect_from_plc(plc)
    connection.close()

    print("Connections closed.")