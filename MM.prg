
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
