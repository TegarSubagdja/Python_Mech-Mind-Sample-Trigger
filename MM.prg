
' ==========================================
' GLOBAL WAYPOINT DATA
' ==========================================

Integer pointCount
Integer visionIndex

Real waypointX(100)
Real waypointY(100)
Real waypointZ(100)
Real waypointU(100)
Real waypointV(100)
Real waypointW(100)

Integer waypointLabel(100)
Integer waypointTool(100)


' ==========================================
' MECH-MIND CONNECTION
' ==========================================

Function MM_Connect

    CloseNet #201

    SetNet #201, "192.168.1.2", 50000, CR, NONE, 300, TCP
    OpenNet #201 As Client
    WaitNet #201

    Print "Mech-Mind Connected"

Fend


' ==========================================
' TRIGGER VISION
' ==========================================

Function MM_TriggerViz

    String response$

    Write #201, "201,0,0,0,0,0,0,0" + Chr$(13)
    Line Input #201, response$

    Print "Trigger: ", response$

Fend


' ==========================================
' GET WAYPOINT BY BRANCH
' ==========================================

Function MM_GetPath(branchID As Integer)

    Integer cmd
    Integer statusCode
    Integer transmission
    Integer i

    pointCount = 0

    ' Request waypoints from selected branch
    Write #201, "205,2," + Str$(branchID) + Chr$(13)

    ' Read response header
    Input #201, cmd, statusCode, transmission, pointCount, visionIndex

    If statusCode = 2100 Then

        Print "Branch ID: ", branchID
        Print "Waypoint Count: ", pointCount

        For i = 1 To pointCount

            Input #201, waypointX(i), waypointY(i), waypointZ(i), _
                        waypointU(i), waypointV(i), waypointW(i), _
                        waypointLabel(i), waypointTool(i)

        Next i

        Print "Coordinates Received"

    Else

        pointCount = 0
        Print "Mech-Mind Error: ", statusCode

    EndIf

Fend


' ==========================================
' CLOSE CONNECTION
' ==========================================

Function MM_Close

    CloseNet #201

    Print "Mech-Mind Disconnected"

Fend


Function Main

    Integer branchID
    Integer i

    MM_Connect

    MM_TriggerViz

    ' Select branch
    branchID = 1

    MM_GetPath(branchID)

    If pointCount > 0 Then

        For i = 1 To pointCount

            Tool waypointTool(i)

            ' Robot movement handled by main program
            Go XY(waypointX(i), waypointY(i), waypointZ(i), _
                  waypointU(i), waypointV(i), waypointW(i))

        Next i

    EndIf

    MM_Close

Fend
