
import socket
from dataclasses import dataclass
from typing import Optional


# ============================================================
# CONFIGURATION
# ============================================================

MECH_MIND_IP = "192.168.1.2"
MECH_MIND_PORT = 50000
TIMEOUT = 15

CR = b"\r"

SUCCESS_CODES = {
    201: 2103,
    202: 2104,
    203: 2105,
    204: 2106,
    205: 2100,
    206: 2102,
    207: 2109,
    208: 2108,
    210: 2100,
}


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Waypoint:
    index: int
    pose: list[float]
    label: int
    tool_id: int


@dataclass
class PlannedPath:
    waypoints: list[Waypoint]
    vision_move_index: int
    transmission_complete: bool


# ============================================================
# MECH-MIND STANDARD INTERFACE
# ============================================================

class MechMindClient:

    def __init__(
        self,
        ip: str = MECH_MIND_IP,
        port: int = MECH_MIND_PORT,
        timeout: float = TIMEOUT,
    ):
        self.ip = ip
        self.port = port
        self.timeout = timeout

        self.sock: Optional[socket.socket] = None
        self.buffer = bytearray()

    # ========================================================
    # CONNECTION
    # ========================================================

    def connect(self):

        if self.sock is not None:
            return

        self.sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        self.sock.settimeout(self.timeout)

        try:
            self.sock.connect((self.ip, self.port))
            print(f"CONNECTED: {self.ip}:{self.port}")

        except Exception:
            self.close()
            raise

    def close(self):

        if self.sock is not None:
            self.sock.close()
            self.sock = None

        self.buffer.clear()
        print("CONNECTION CLOSED")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ========================================================
    # TCP COMMUNICATION
    # ========================================================

    def send_command(self, command: str) -> str:

        if self.sock is None:
            raise ConnectionError("TCP not connected")

        if "\r" in command or "\n" in command:
            raise ValueError("Invalid command terminator")

        print(f"\nTX >> {command}")

        self.sock.sendall(
            command.encode("ascii") + CR
        )

        while True:

            delimiter = self.buffer.find(CR)

            if delimiter >= 0:

                response = self.buffer[:delimiter]

                del self.buffer[:delimiter + 1]

                if self.buffer.startswith(b"\n"):
                    del self.buffer[:1]

                result = response.decode("ascii").strip()

                print(f"RX << {result}")

                return result

            chunk = self.sock.recv(4096)

            if not chunk:
                raise ConnectionError(
                    "Mech-Mind disconnected"
                )

            self.buffer.extend(chunk)

    def execute(
        self,
        command: str,
        expected_code: Optional[int] = None,
    ) -> list[str]:

        response = self.send_command(command)

        fields = [
            value.strip()
            for value in response.split(",")
        ]

        if len(fields) < 2:
            raise ValueError(
                f"Invalid response: {response}"
            )

        command_id = int(fields[0])
        status_code = int(fields[1])

        if expected_code is None:
            expected_code = SUCCESS_CODES.get(command_id)

        if (
            expected_code is not None
            and status_code != expected_code
        ):
            raise RuntimeError(
                f"Command {command_id} failed. "
                f"Status: {status_code}. "
                f"Response: {response}"
            )

        return fields

    # ========================================================
    # COMMAND 201 - TRIGGER MECH-VIZ
    # ========================================================

    def trigger_viz(
        self,
        pose_type: int = 0,
        robot_pose: Optional[list[float]] = None,
    ) -> list[str]:

        if pose_type == 0:
            pose = [0] * 6

        elif pose_type == 1:

            if robot_pose is None or len(robot_pose) != 12:
                raise ValueError(
                    "Pose type 1 requires 12 values: "
                    "6 JPs + 6 flange pose values"
                )

            pose = robot_pose

        elif pose_type == 2:

            if robot_pose is None or len(robot_pose) != 6:
                raise ValueError(
                    "Pose type 2 requires 6 joint positions"
                )

            pose = robot_pose

        else:
            raise ValueError("Pose type must be 0, 1 or 2")

        command = "201," + str(pose_type) + "," + ",".join(
            str(value) for value in pose
        )

        return self.execute(command)

    # ========================================================
    # COMMAND 202 - STOP MECH-VIZ
    # ========================================================

    def stop_viz(self) -> list[str]:

        return self.execute("202")

    # ========================================================
    # COMMAND 203 - SET BRANCH
    # ========================================================

    def set_branch(
        self,
        step_id: int,
        exit_port: int,
    ) -> list[str]:

        if step_id <= 0 or exit_port <= 0:
            raise ValueError("Invalid Step ID or Exit Port")

        command = f"203,{step_id},{exit_port}"

        return self.execute(command)

    # ========================================================
    # COMMAND 204 - SET CURRENT INDEX
    # ========================================================

    def set_index(
        self,
        step_id: int,
        current_index: int,
    ) -> list[str]:

        if step_id <= 0 or current_index <= 0:
            raise ValueError("Invalid Step ID or Index")

        command = f"204,{step_id},{current_index}"

        return self.execute(command)

    # ========================================================
    # COMMAND 205 - GET PLANNED PATH
    # ========================================================

    def get_planned_path(
        self,
        pose_type: int = 2,
        max_batches: int = 100,
    ) -> PlannedPath:

        if pose_type not in (1, 2):
            raise ValueError("Pose type must be 1 or 2")

        waypoints = []
        vision_move_index = 0
        transmission_complete = False

        for batch in range(max_batches):

            fields = self.execute(
                f"205,{pose_type}"
            )

            if len(fields) < 5:
                raise ValueError("Invalid path header")

            transmission_status = int(fields[2])
            waypoint_count = int(fields[3])
            vision_position = int(fields[4])

            if transmission_status not in (0, 1):
                raise ValueError("Invalid transmission status")

            # Vision position is relative to the remaining
            # waypoints in each response batch.
            if vision_position > 0 and vision_move_index == 0:
                vision_move_index = (
                    len(waypoints) + vision_position
                )

            expected_length = 5 + waypoint_count * 8

            if len(fields) != expected_length:
                raise ValueError(
                    f"Expected {expected_length} fields, "
                    f"received {len(fields)}"
                )

            offset = 5

            for _ in range(waypoint_count):

                pose = [
                    float(value)
                    for value in fields[offset:offset + 6]
                ]

                label = int(fields[offset + 6])
                tool_id = int(fields[offset + 7])

                waypoints.append(
                    Waypoint(
                        index=len(waypoints) + 1,
                        pose=pose,
                        label=label,
                        tool_id=tool_id,
                    )
                )

                offset += 8

            print(
                f"PATH BATCH {batch + 1}: "
                f"{waypoint_count} waypoints"
            )

            if transmission_status == 1:
                transmission_complete = True
                break

        if not transmission_complete:
            raise TimeoutError(
                "Planned path transmission incomplete"
            )

        return PlannedPath(
            waypoints=waypoints,
            vision_move_index=vision_move_index,
            transmission_complete=True,
        )

    # ========================================================
    # COMMAND 206 - GET GRIPPER DO LIST
    # ========================================================

    def get_gripper_do_list(
        self,
        number_of_sections: int,
    ) -> list[int]:

        if number_of_sections <= 0:
            raise ValueError("Invalid gripper sections")

        fields = self.execute(
            f"206,{number_of_sections}"
        )

        signals = [
            int(value)
            for value in fields[2:]
        ]

        if len(signals) != 64:
            raise ValueError(
                f"Expected 64 DO signals, got {len(signals)}"
            )

        # Preserve -1 placeholders and original positions.
        return signals

    # ========================================================
    # COMMAND 207 - READ STEP PARAMETER
    # ========================================================

    def read_step_parameter(
        self,
        config_id: int,
    ) -> str:

        if config_id <= 0:
            raise ValueError("Invalid Config ID")

        fields = self.execute(
            f"207,{config_id}"
        )

        if len(fields) < 3:
            raise ValueError("Missing parameter value")

        return fields[2]

    # ========================================================
    # COMMAND 208 - SET STEP PARAMETER
    # ========================================================

    def set_step_parameter(
        self,
        config_id: int,
    ) -> list[str]:

        if config_id <= 0:
            raise ValueError("Invalid Config ID")

        return self.execute(
            f"208,{config_id}"
        )

    # ========================================================
    # COMMAND 210 - GET VISION MOVE / CUSTOM DATA
    # ========================================================

    def get_viz_data(
        self,
        returned_data_format: int = 2,
    ) -> list[str]:

        if returned_data_format not in (1, 2, 3, 4):
            raise ValueError(
                "Data format must be 1, 2, 3 or 4"
            )

        # Raw fields are returned because the payload
        # depends on Vision Move and custom data settings.
        return self.execute(
            f"210,{returned_data_format}"
        )


# ============================================================
# DISPLAY FUNCTIONS
# ============================================================

def display_path(path: PlannedPath):

    print("\n" + "=" * 50)
    print("MECH-VIZ PLANNED PATH")
    print("=" * 50)

    print(f"Total Waypoints: {len(path.waypoints)}")
    print(f"Vision Move Index: {path.vision_move_index}")

    for wp in path.waypoints:

        x, y, z, a, b, c = wp.pose

        marker = (
            " <-- VISION MOVE"
            if wp.index == path.vision_move_index
            else ""
        )

        print(f"\nWAYPOINT {wp.index}{marker}")
        print(f"X: {x}")
        print(f"Y: {y}")
        print(f"Z: {z}")
        print(f"A: {a}")
        print(f"B: {b}")
        print(f"C: {c}")
        print(f"Label: {wp.label}")
        print(f"Tool ID: {wp.tool_id}")


def display_do_list(signals: list[int]):

    print("\nGRIPPER DO LIST")

    for index, signal in enumerate(signals, start=1):

        if signal != -1:
            print(f"DO Position {index}: {signal}")


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    # --------------------------------------------------------
    # SELECT COMMANDS
    # --------------------------------------------------------

    USE_TRIGGER = True
    USE_STOP = False
    USE_BRANCH = False
    USE_INDEX = False
    USE_PLANNED_PATH = True
    USE_GRIPPER_DO = False
    USE_READ_PARAMETER = False
    USE_SET_PARAMETER = False
    USE_VIZ_DATA = False

    # --------------------------------------------------------
    # COMMAND PARAMETERS
    # --------------------------------------------------------

    BRANCH_STEP_ID = 5
    BRANCH_EXIT_PORT = 2

    INDEX_STEP_ID = 3
    CURRENT_INDEX = 10

    GRIPPER_SECTIONS = 4

    READ_CONFIG_ID = 10
    WRITE_CONFIG_ID = 11

    POSE_TYPE = 2

    # --------------------------------------------------------
    # EXECUTION
    # --------------------------------------------------------

    try:

        with MechMindClient() as mm:

            # 207 - Read parameter
            if USE_READ_PARAMETER:

                value = mm.read_step_parameter(
                    READ_CONFIG_ID
                )

                print("\nSTEP PARAMETER:", value)

            # 208 - Set parameter
            if USE_SET_PARAMETER:

                mm.set_step_parameter(
                    WRITE_CONFIG_ID
                )

            # 201 - Trigger
            if USE_TRIGGER:

                mm.trigger_viz(
                    pose_type=0
                )

            # 204 - Set index
            if USE_INDEX:

                mm.set_index(
                    INDEX_STEP_ID,
                    CURRENT_INDEX
                )

            # 203 - Set branch
            if USE_BRANCH:

                mm.set_branch(
                    BRANCH_STEP_ID,
                    BRANCH_EXIT_PORT
                )

            # 205 - Get planned path
            if USE_PLANNED_PATH:

                path = mm.get_planned_path(
                    pose_type=POSE_TYPE
                )

                display_path(path)

            # 206 - Get gripper DO
            if USE_GRIPPER_DO:

                signals = mm.get_gripper_do_list(
                    GRIPPER_SECTIONS
                )

                display_do_list(signals)

            # 210 - Get Vision Move / Custom Data
            if USE_VIZ_DATA:

                data = mm.get_viz_data(
                    returned_data_format=4
                )

                print("\nMECH-VIZ DATA:")
                print(data)

            # 202 - Stop
            if USE_STOP:

                mm.stop_viz()

    except Exception as error:

        print(f"\nERROR: {error}")


if __name__ == "__main__":
    main()
