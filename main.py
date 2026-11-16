
import socket


# ==========================================
# CONFIGURATION
# ==========================================

IP = "192.168.1.2"
PORT = 50000
TIMEOUT = 15

sock = None


# ==========================================
# TCP CONNECTION
# ==========================================

def connect():

    global sock

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT)
    sock.connect((IP, PORT))

    print("TCP CONNECTED")


def close():

    global sock

    if sock:
        sock.close()
        sock = None

    print("CONNECTION CLOSED")


def send(command):

    sock.sendall((command + "\r").encode())

    response = b""

    while b"\r" not in response:

        data = sock.recv(4096)

        if not data:
            raise ConnectionError("Connection closed")

        response += data

    result = response.split(b"\r", 1)[0].decode().strip()

    print(f"RX: {result}")

    return result.split(",")


# ==========================================
# MECH-MIND COMMANDS
# ==========================================

# 201 - Trigger Mech-Viz
def trigger_viz():

    return send("201,0,0,0,0,0,0,0")


# 202 - Stop Mech-Viz
def stop_viz():

    return send("202")


# 203 - Set Branch
def set_branch(step_id, exit_port):

    return send(f"203,{step_id},{exit_port}")


# 204 - Set Index
def set_index(step_id, index):

    return send(f"204,{step_id},{index}")


# 205 - Get Planned Path
def get_planned_path(pose_type=2):

    response = send(f"205,{pose_type}")

    count = int(response[3])

    waypoints = []

    for i in range(count):

        start = 5 + (i * 8)

        waypoint = {
            "x": float(response[start]),
            "y": float(response[start + 1]),
            "z": float(response[start + 2]),
            "a": float(response[start + 3]),
            "b": float(response[start + 4]),
            "c": float(response[start + 5]),
            "label": int(response[start + 6]),
            "tool_id": int(response[start + 7]),
        }

        waypoints.append(waypoint)

    return waypoints


# 206 - Get Gripper DO
def get_gripper_do(sections):

    return send(f"206,{sections}")


# 207 - Read Step Parameter
def read_parameter(config_id):

    return send(f"207,{config_id}")


# 208 - Set Step Parameter
def set_parameter(config_id):

    return send(f"208,{config_id}")


# 210 - Get Vision Move / Custom Data
def get_viz_data(data_format=2):

    return send(f"210,{data_format}")


# ==========================================
# MAIN
# ==========================================

def main():

    try:

        connect()

        # Trigger Mech-Viz
        trigger_viz()

        # Set Branch (optional)
        set_branch(8, 5)

        set_branch(12, 2)

        # Set Index (optional)
        # set_index(3, 10)

        # Get Planned Path
        waypoints = get_planned_path()

        print("\nPLANNED PATH")

        for i, wp in enumerate(waypoints, start=1):

            print(f"\nWaypoint {i}")

            for key, value in wp.items():
                print(f"{key}: {value}")

        # Other commands (optional)
        # stop_viz()
        # get_gripper_do(4)
        # read_parameter(10)
        # set_parameter(11)
        # get_viz_data(4)

    except Exception as e:

        print("ERROR:", e)

    finally:

        close()


if __name__ == "__main__":
    main()
