# PLC ↔ Python Interface

## Purpose

Define the production data exchanged between the Beckhoff TwinCAT PLC
and the Python application through ADS.

## PLC → Python

| Variable | PLC Type | Description |
|---|---|---|
| `GVL_ADS.TotalParts` | UDINT | Total number of produced parts |
| `GVL_ADS.OKParts` | UDINT | Number of accepted parts |
| `GVL_ADS.DefectParts` | UDINT | Number of defective parts |
| `GVL_ADS.DefectRate` | LREAL | Percentage of defective parts |
| `GVL_ADS.FaultCode` | UINT | Current machine fault code |
| `GVL_ADS.MachineStatus` | STRING(30) | Current machine state |
| `GVL_ADS.InspectionOK` | BOOL | Result of the latest inspection |

## Python → PLC

Python writes control and simulation inputs through the ADS interface:

| Variable | PLC Type | Description |
|---|---|---|
| `GVL_ADS.StartButton` | BOOL | Start production |
| `GVL_ADS.StopButton` | BOOL | Stop production |
| `GVL_ADS.EmergencyStop` | BOOL | Demo emergency-stop input |
| `GVL_ADS.WorkpieceSensor` | BOOL | Workpiece detection |
| `GVL_ADS.PositionSensor` | BOOL | Inspection position |
| `GVL_ADS.InspectionOK` | BOOL | Inspection result |
| `GVL_ADS.MachineFault` | BOOL | Simulated machine fault |
| `GVL_ADS.ResetButton` | BOOL | Operator reset command |

## Fault Codes

| Code | Meaning |
|---:|---|
| 0 | No fault |
| 1 | Emergency Stop |
| 2 | Machine Fault |

## ADS Communication

ADS (Automation Device Specification) provides the communication
layer between TwinCAT and Python.

The Python application uses the `pyads` library to access PLC
variables through the TwinCAT ADS interface.

Example:

```python
total_parts = plc.read_by_name(
    "GVL_ADS.TotalParts",
    pyads.PLCTYPE_UDINT
)

machine_status = plc.read_by_name(
    "GVL_ADS.MachineStatus",
    pyads.PLCTYPE_STRING
)

defect_rate = plc.read_by_name(
    "GVL_ADS.DefectRate",
    pyads.PLCTYPE_LREAL
)

fault_code = plc.read_by_name(
    "GVL_ADS.FaultCode",
    pyads.PLCTYPE_UINT
)
## Data Architecture
Beckhoff TwinCAT PLC
        |
        | ADS
        v
Python / pyads
        |
        +---- SQLite
        |
        +---- n8n
                |
                v
             Airtable

## Responsibilities

### PLC

- Real-time machine control
- State machine execution
- Production counters
- Fault handling
- Machine status
- Operator reset

### Python

- ADS data acquisition
- Production-event detection
- Data processing
- Local persistence
- Production statistics
- Fault monitoring
- External automation integration
