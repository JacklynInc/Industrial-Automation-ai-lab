"""
Beckhoff TwinCAT ADS Client

Handles communication between the Python application
and the Beckhoff PLC via ADS.
"""

import pyads


PLC_AMS_NET_ID = "127.0.0.1.1.1"
PLC_PORT = 851


def connect_to_plc():
    """Open an ADS connection to the TwinCAT PLC."""
    plc = pyads.Connection(PLC_AMS_NET_ID, PLC_PORT)
    plc.open()
    return plc


def read_production_data(plc):
    """Read production data from the PLC."""

    data = {
        "total_parts": plc.read_by_name(
            "GVL_ADS.TotalParts",
            pyads.PLCTYPE_UDINT
        ),

        "ok_parts": plc.read_by_name(
            "GVL_ADS.OKParts",
            pyads.PLCTYPE_UDINT
        ),

        "defect_parts": plc.read_by_name(
            "GVL_ADS.DefectParts",
            pyads.PLCTYPE_UDINT
        ),

        "defect_rate": plc.read_by_name(
            "GVL_ADS.DefectRate",
            pyads.PLCTYPE_LREAL
        ),

        "fault_code": plc.read_by_name(
            "GVL_ADS.FaultCode",
            pyads.PLCTYPE_UINT
        ),

        "machine_status": plc.read_by_name(
            "GVL_ADS.MachineStatus",
            pyads.PLCTYPE_STRING
        ),

        "inspection_ok": plc.read_by_name(
            "GVL_ADS.InspectionOK",
            pyads.PLCTYPE_BOOL
        ),
    }

    return data


def disconnect_from_plc(plc):
    """Close the ADS connection."""
    plc.close()