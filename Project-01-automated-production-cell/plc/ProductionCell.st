TYPE E_State :
(
    IDLE,
    STARTING,
    RUNNING,
    WORKPIECE_DETECTED,
    INSPECTING,
    SORTING,
    RECORDING,
    FAULT,
    RESET
);
END_TYPE


VAR_INPUT
    StartButton       : BOOL;
    StopButton        : BOOL;
    EmergencyStop     : BOOL;
    WorkpieceSensor   : BOOL;
    PositionSensor    : BOOL;
    InspectionOK      : BOOL;
    MachineFault      : BOOL;
END_VAR


VAR_OUTPUT
    ConveyorMotor     : BOOL;
    OKSorter          : BOOL;
    DefectSorter      : BOOL;
    GreenIndicator    : BOOL;
    RedIndicator      : BOOL;
END_VAR


VAR
    State             : E_State := IDLE;
    InspectionResult  : BOOL;

    StartTimer        : TON;
    InspectionTimer   : TON;
    SortingTimer      : TON;

    TotalParts        : UDINT := 0;
    OKParts           : UDINT := 0;
    DefectParts       : UDINT := 0;
    DefectRate        : LREAL := 0.0;

    FaultCode         : UINT := 0;
    MachineStatus     : STRING(30);
END_VAR


(* Reset outputs every PLC scan *)

ConveyorMotor := FALSE;
OKSorter := FALSE;
DefectSorter := FALSE;
GreenIndicator := FALSE;
RedIndicator := FALSE;


(* Timers *)

StartTimer(
    IN := (State = STARTING),
    PT := T#2S
);

InspectionTimer(
    IN := (State = INSPECTING),
    PT := T#1S
);

SortingTimer(
    IN := (State = SORTING),
    PT := T#500MS
);


(* Fault priority *)

IF EmergencyStop THEN
    FaultCode := 1;
    State := FAULT;

ELSIF MachineFault THEN
    FaultCode := 2;
    State := FAULT;
END_IF;


(* State machine *)

CASE State OF

    IDLE:
        IF StartButton THEN
            State := STARTING;
        END_IF;


    STARTING:
        IF StartTimer.Q THEN
            State := RUNNING;
        END_IF;


    RUNNING:
        ConveyorMotor := TRUE;
        GreenIndicator := TRUE;

        IF StopButton THEN
            State := IDLE;

        ELSIF WorkpieceSensor THEN
            State := WORKPIECE_DETECTED;
        END_IF;


    WORKPIECE_DETECTED:
        IF PositionSensor THEN
            State := INSPECTING;
        END_IF;


    INSPECTING:
        IF InspectionTimer.Q THEN
            InspectionResult := InspectionOK;
            State := SORTING;
        END_IF;


    SORTING:
        IF InspectionResult THEN
            OKSorter := TRUE;
        ELSE
            DefectSorter := TRUE;
        END_IF;

        IF SortingTimer.Q THEN
            State := RECORDING;
        END_IF;


    RECORDING:
        TotalParts := TotalParts + 1;

        IF InspectionResult THEN
            OKParts := OKParts + 1;
        ELSE
            DefectParts := DefectParts + 1;
        END_IF;

        IF TotalParts > 0 THEN
            DefectRate := (DefectParts * 100.0) / TotalParts;
        END_IF;

        State := RUNNING;


    FAULT:
        ConveyorMotor := FALSE;
        OKSorter := FALSE;
        DefectSorter := FALSE;
        RedIndicator := TRUE;

        IF NOT EmergencyStop AND NOT MachineFault THEN
            State := RESET;
        END_IF;


    RESET:
        ConveyorMotor := FALSE;
        OKSorter := FALSE;
        DefectSorter := FALSE;
        RedIndicator := FALSE;

        FaultCode := 0;

        State := IDLE;

END_CASE;


(* HMI status *)

CASE State OF

    IDLE:
        MachineStatus := 'IDLE';

    STARTING:
        MachineStatus := 'STARTING';

    RUNNING:
        MachineStatus := 'RUNNING';

    WORKPIECE_DETECTED:
        MachineStatus := 'WORKPIECE DETECTED';

    INSPECTING:
        MachineStatus := 'INSPECTING';

    SORTING:
        MachineStatus := 'SORTING';

    RECORDING:
        MachineStatus := 'RECORDING';

    FAULT:
        MachineStatus := 'FAULT';

    RESET:
        MachineStatus := 'RESET';

END_CASE;