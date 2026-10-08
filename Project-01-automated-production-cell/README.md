# Automated Production Cell

A small industrial automation project combining Beckhoff TwinCAT,
PLC programming, Structured Text, Python, SQLite, n8n, and Airtable.

## Project Overview

This project implements an automated production cell that detects,
inspects, sorts, and records manufactured workpieces.

The real-time machine-control logic is implemented in a Beckhoff
TwinCAT PLC using IEC 61131-3 Structured Text.

Python communicates with the PLC through ADS and handles production
event detection, data processing, local persistence, fault monitoring,
and external workflow integration.

## Production Sequence

```text
IDLE
  ↓
STARTING
  ↓
RUNNING
  ↓
WORKPIECE_DETECTED
  ↓
INSPECTING
  ↓
SORTING
  ↓
RECORDING
  ↓
RUNNING

Fault conditions can transition the machine to:
FAULT → RESET → IDLE

## Technology Stack

### Industrial Automation

- Beckhoff TwinCAT 3
- IEC 61131-3 Structured Text
- PLC state-machine programming
- Timers
- Fault handling
- ADS communication

### Python / Data

- Python
- pyads
- SQLite
- Data processing
- Production statistics

### Automation / Integration

- n8n
- Airtable
- Webhooks

## System Architecture
┌──────────────────────────┐
│ Beckhoff TwinCAT PLC     │
│                          │
│ State Machine            │
│ Sensors / Actuators      │
│ Production Counters      │
│ Defect Rate              │
│ Fault Handling           │
└────────────┬─────────────┘
             │
             │ ADS
             ▼
┌──────────────────────────┐
│ Python / pyads           │
│                          │
│ PLC Data Acquisition     │
│ Production Event Logic   │
│ Fault Monitoring         │
│ Statistics               │
└────────────┬─────────────┘
             │
       ┌─────┴─────┐
       ▼           ▼
   SQLite         n8n
                   │
                   ▼
                Airtable

## PLC Responsibilities

- Real-time machine control
- State-machine execution
- Sensor processing
- Actuator control
- Production counters
- Defect-rate calculation
- Fault handling
- Operator reset
- Machine status

## Python Responsibilities

- ADS communication with the PLC
- Production-event detection
- OK/DEFECT event processing
- Local SQLite persistence
- Production statistics
- PLC fault monitoring
- n8n integration

## Production Event Handling

Python monitors the PLC production counters through ADS.

When `TotalParts` increases, Python determines whether the new
production event was an `OK` or `DEFECT` part by comparing the
`OKParts` and `DefectParts` counters with their previous values.

The production event is then:

1. Stored in SQLite
2. Added to the production statistics
3. Sent to the n8n webhook
4. Recorded in Airtable

## Fault Handling

The PLC implements fault handling using `FaultCode` and
`MachineStatus`.

Supported fault codes:

| Code | Meaning |
|---:|---|
| 0 | No fault |
| 1 | Emergency Stop |
| 2 | Machine Fault |

When a fault occurs, the PLC stops the conveyor and sorter outputs
and enters the `FAULT` state.

The operator must clear the fault condition and activate the
`ResetButton` to return the machine through:

FAULT → RESET → IDLE

Python monitors the PLC fault state through ADS and reports new
non-zero fault events.

> **Safety note:** Emergency-stop handling in this project is
> demonstration PLC logic and is not a safety-rated emergency-stop
> architecture. A real machine requires appropriate safety hardware,
> safety PLC/relay systems, and a validated safety design.

## Automation Layer

n8n receives production events from Python through a webhook.

The workflow sends the production data to Airtable, where production
records and KPIs can be stored and monitored.

The verified data pipeline is:
TwinCAT PLC
    ↓
ADS / pyads
    ↓
Python
    ↓
SQLite
    ↓
n8n
    ↓
Airtable

## Current PLC Implementation

The TwinCAT PLC implements:

- Production state machine
- Start/stop control
- Startup timer
- Workpiece detection
- Position detection
- Inspection timing
- OK/DEFECT sorting
- Production counters
- Defect-rate calculation
- Emergency-stop handling
- Machine-fault handling
- Fault codes
- Machine status
- Operator reset

## Verification

The system was tested end-to-end using controlled PLC inputs.

Verified:

- IDLE → STARTING → RUNNING transition
- Workpiece detection
- Position detection
- Inspection sequence
- OK production cycle
- DEFECT production cycle
- Production counter updates
- Defect-rate calculation
- PLC → Python ADS communication
- SQLite production recording
- n8n webhook integration
- Airtable production recording
- PLC fault detection
- Python fault monitoring
- Operator reset

Example verified production event:

Result: OK
SQLite Production ID: 608
Total historical records: 110
OK records: 65
DEFECT records: 45
Defect rate: 40.91%
n8n response: 200

## Project Status

### Completed

- Python production-cell simulation
- SQLite production database
- n8n production webhook
- Airtable production records
- TwinCAT PLC project
- IEC 61131-3 Structured Text implementation
- PLC state machine
- PLC production KPIs
- PLC fault handling
- Python ADS integration
- Python production monitoring
- Python fault monitoring
- PLC/Python architecture documentation
- GitHub repository

## Learning Objective

The project is designed as a practical bridge between:

**Mechanical Engineering → Industrial Automation → PLC Programming → Python → Data Automation**

The goal is to understand how real-time industrial control systems
can connect with modern software and data-processing workflows.

