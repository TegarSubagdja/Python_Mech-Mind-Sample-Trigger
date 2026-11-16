
' ==========================================
' MECH-MIND CONFIGURATION
' ==========================================

Function MM_Connect

    CloseNet #201

    SetNet #201, "192.168.1.2", 50000, CR, NONE, 300, TCP

    OpenNet #201 As Client
    WaitNet #201

    Print "Mech-Mind Connected"

Fend


' ==========================================
' MECH-MIND COMMANDS
' ==========================================

' 201 - Trigger Mech-Viz
Function MM_TriggerViz

    String response$

    Write #201, "201,0,0,0,0,0,0,0" + Chr$(13)
    Line Input #201, response$

    Print "Trigger Viz: ", response$

Fend


' 202 - Stop Mech-Viz
Function MM_StopViz

    String response$

    Write #201, "202" + Chr$(13)
    Line Input #201, response$

    Print "Stop Viz: ", response$

Fend


' 203 - Set Branch
Function MM_SetBranch(Integer step_id, Integer exit_port)

    String response$

    Write #201, "203," + Str$(step_id) + "," + Str$(exit_port) + Chr$(13)
    Line Input #201, response$

    Print "Set Branch: ", response$

Fend


' 204 - Set Index
Function MM_SetIndex(Integer step_id, Integer index)

    String response$

    Write #201, "204," + Str$(step_id) + "," + Str$(index) + Chr$(13)
    Line Input #201, response$

    Print "Set Index: ", response$

Fend


' 205 - Get Planned Path
Function MM_GetPlannedPath

    String response$

    Write #201, "205,2" + Chr$(13)
    Line Input #201, response$

    Print "Planned Path: ", response$

    ' Parse response di sini untuk mengambil koordinat

Fend


' 206 - Get Gripper DO
Function MM_GetGripperDO(Integer sections)

    String response$

    Write #201, "206," + Str$(sections) + Chr$(13)
    Line Input #201, response$

    Print "Gripper DO: ", response$

Fend


' 207 - Read Step Parameter
Function MM_ReadParameter(Integer config_id)

    String response$

    Write #201, "207," + Str$(config_id) + Chr$(13)
    Line Input #201, response$

    Print "Read Parameter: ", response$

Fend


' 208 - Set Step Parameter
Function MM_SetParameter(Integer config_id)

    String response$

    Write #201, "208," + Str$(config_id) + Chr$(13)
    Line Input #201, response$

    Print "Set Parameter: ", response$

Fend


' 210 - Get Vision Move Data
Function MM_GetVizData(Integer data_format)

    String response$

    Write #201, "210," + Str$(data_format) + Chr$(13)
    Line Input #201, response$

    Print "Viz Data: ", response$

Fend


' ==========================================
' CLOSE CONNECTION
' ==========================================

Function MM_Close

    CloseNet #201

    Print "Mech-Mind Disconnected"

Fend
