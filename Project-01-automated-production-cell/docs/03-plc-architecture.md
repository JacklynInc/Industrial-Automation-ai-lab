# PLC Architecture

## Controller

The production cell is implemented as a Beckhoff TwinCAT PLC project
using IEC 61131-3 Structured Text.

The PLC contains the real-time machine-control logic, while Python
handles data acquisition, production-event processing, persistence,
and external automation.

## State Machine

The production sequence uses the following states:

IDLE
STARTING
RUNNING
WORKPIECE_DETECTED
INSPECTING
SORTING
RECORDING
FAULT
RESET

## Inputs

| Input | Type | Description |
|---|---|---|
| StartButton | BOOL | Starts production |
| StopButton | BOOL | Stops normal production |
| EmergencyStop | BOOL | Demo emergency-stop input |
| WorkpieceSensor | BOOL | Detects a workpiece |
| PositionSensor | BOOL | Confirms inspection position |
| InspectionOK | BOOL | Simulated inspection result |
| MachineFault | BOOL | Simulated technical machine fault |
| ResetButton | BOOL | Operator reset command |

> **Safety note:** Emergency-stop handling in this project is implemented
> as PLC demonstration logic. It is not a safety-rated emergency-stop
> architecture. A real machine requires appropriate safety hardware,
> safety PLC/relay systems, and a validated safety design.

## Outputs

| Output | Type | Description |
|---|---|---|
| ConveyorMotor | BOOL | Conveyor control |
| OKSorter | BOOL | Sorts accepted workpieces |
| DefectSorter | BOOL | Sorts rejected workpieces |
| GreenIndicator | BOOL | Normal operation indication |
| RedIndicator | BOOL | Fault indication |

## Timers

| Timer | Duration | Purpose |
|---|---:|---|
| StartTimer | 2 s | Startup delay |
| InspectionTimer | 1 s | Inspection duration |
| SortingTimer | 500 ms | Sorting duration |

## Production KPIs

The PLC calculates:

- Total Parts
- OK Parts
- Defect Parts
- Defect Rate

These values are exposed through the `GVL_ADS` interface for Python
monitoring.

## Fault Handling

| Fault Code | Meaning |
|---:|---|
| 0 | No fault |
| 1 | Emergency Stop |
| 2 | Machine Fault |

When a fault occurs, the conveyor and sorters are stopped and the
machine enters the `FAULT` state.

The fault condition must be cleared before an operator can reset the
machine. The explicit reset sequence is:

```text
FAULT → RESET → IDLE

The `ResetButton` provides the operator reset command.

## Machine Status

The PLC exposes:

- `MachineStatus`
- `FaultCode`

These variables provide the current machine state and fault condition
to external monitoring software.

## Communication Architecture
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

ADS (Automation Device Specification) is used for communication between
the TwinCAT PLC and the Python application through `pyads`.

## Responsibilities

### PLC

- Real-time machine control
- State machine execution
- Sensor processing
- Actuator control
- Production counters
- Defect-rate calculation
- Fault handling
- Operator reset
- Machine status

### Python

- ADS communication with the PLC
- Production-event detection
- OK/DEFECT event processing
- Local SQLite persistence
- Production statistics
- PLC fault monitoring
- n8n integration

### n8n / Airtable

- Workflow automation
- Production data integration
- Cloud-based production records
