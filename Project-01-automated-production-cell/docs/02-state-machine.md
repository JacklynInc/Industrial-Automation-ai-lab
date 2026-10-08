# Automated Production Cell — State Machine

## Purpose

The production cell is controlled using a state machine implemented in
Beckhoff TwinCAT Structured Text.

Each state represents a defined operating condition of the machine.

## States

### IDLE

- Machine is stopped.
- Conveyor is OFF.
- Sorter actuators are OFF.
- System waits for START.

### STARTING

- Start sequence is active.
- A 2-second startup timer runs.
- After the timer completes, the machine moves to RUNNING.

### RUNNING

- Conveyor is ON.
- System monitors the workpiece sensor.
- When a workpiece is detected, move to WORKPIECE_DETECTED.

### WORKPIECE_DETECTED

- System waits for the position sensor.
- When the correct position is confirmed, move to INSPECTING.

### INSPECTING

- The workpiece inspection is simulated using `InspectionOK`.
- The result is either:
  - OK
  - DEFECT
- After the inspection timer completes, move to SORTING.

### SORTING

- The appropriate sorter is activated.
- OK workpieces are sent to the OK output.
- Defective workpieces are sent to the DEFECT output.
- After the sorting timer completes, move to RECORDING.

### RECORDING

- Production result is recorded.
- Production counters are updated.
- Defect rate is calculated.
- Return to RUNNING.

### FAULT

- Conveyor is stopped.
- Sorter actuators are stopped.
- Fault information is stored in `FaultCode`.
- System remains in FAULT until the fault condition is cleared and
  the operator activates `ResetButton`.

### RESET

- Fault code is cleared.
- The machine transitions back to IDLE.

## State Flow

```text
IDLE
  |
  v
STARTING
  |
  v
RUNNING
  |
  v
WORKPIECE_DETECTED
  |
  v
INSPECTING
  |
  v
SORTING
  |
  v
RECORDING
  |
  +--------> RUNNING


Emergency Stop / Machine Fault
              |
              v
            FAULT
              |
              | ResetButton
              v
            RESET
              |
              v
            IDLE

## Inputs

| Variable          | Description                  |
| ----------------- | ---------------------------- |
| `StartButton`     | Starts production            |
| `StopButton`      | Stops normal production      |
| `EmergencyStop`   | Demo emergency-stop input    |
| `WorkpieceSensor` | Detects a workpiece          |
| `PositionSensor`  | Confirms inspection position |
| `InspectionOK`    | Simulated inspection result  |
| `MachineFault`    | Simulated machine fault      |
| `ResetButton`     | Operator reset command       |

## Outputs

| Variable         | Description                 |
| ---------------- | --------------------------- |
| `ConveyorMotor`  | Conveyor control            |
| `OKSorter`       | OK sorting actuator         |
| `DefectSorter`   | Defect sorting actuator     |
| `GreenIndicator` | Normal operation indication |
| `RedIndicator`   | Fault indication            |

> **Safety note:** Emergency-stop handling in this project is
> demonstration PLC logic and is not a safety-rated emergency-stop
> architecture.
