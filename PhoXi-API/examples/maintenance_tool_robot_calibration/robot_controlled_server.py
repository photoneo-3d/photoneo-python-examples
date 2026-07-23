# Robot-controlled server for the Photoneo MaintenanceTool API.
#
# Runs on the PC that has PhoXi Control and the phoxi_api package installed. Listens for a single
# TCP client at a time (typically a robot controller, see ur_client_example.script) that drives a
# maintenance/calibration session by sending line commands: START_CALIBRATION <serial>,
# ADJUST_POWER, TRIGGER, ANALYZE, PATCH, STOP_CALIBRATION. Each command is answered with a single
# "OK[, ...]" or "NOK:<reason>" line.
#
# See README.md in this folder for the full protocol, the calibration flowchart, and
# localhost_client_simulator.py for a manual test client that doesn't require robot hardware.
#
# Prerequisites:
#   - PHOXI_CONTROL_PATH environment variable pointing to PhoXi Control installation directory
#   - PhoXi Control running
#
# Usage:
#   python robot_controlled_server.py

import socket
import sys

from phoxi_api import MaintenanceTool
from phoxi_api.exceptions import PhoXiError

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 2222


def cleanup_device(device):
    # Safely disconnect and release the device if it exists.
    if device is not None:
        try:
            device.disconnect()
        except Exception as e:
            print(f"Error during device disconnect: {e}")
    return None


def handle_client(conn, addr, mt):
    # Handle all commands from a single client connection.
    device = None
    print(f"Connected by {addr}")

    try:
        conn.settimeout(5.0)  # timeout for recv

        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    print("Client disconnected.")
                    break

                command_line = data.decode("utf-8").strip()
                if not command_line:
                    continue
                print(f"Received: {command_line}")

                parts = command_line.split()
                cmd = parts[0].upper()
                response = None

                # ---------- Command handling ----------
                if cmd == "START_CALIBRATION":
                    if len(parts) < 2:
                        response = "NOK:Missing serial number"
                    elif device is not None:
                        active_msg = "NOK:Calibration already active (send STOP_CALIBRATION first)"
                        response = active_msg
                    else:
                        serial = parts[1]
                        try:
                            device = mt.connect(serial)
                            response = "OK"
                            print(f"Device {serial} connected.")
                        except PhoXiError as e:
                            response = f"NOK:{e}"
                            device = None

                elif cmd == "ADJUST_POWER":
                    if device is None:
                        response = "NOK:No active calibration (send START_CALIBRATION first)"
                    else:
                        try:
                            device.adjust_power()
                            response = "OK"
                            print("Power adjustment succeeded.")
                        except PhoXiError as e:
                            response = f"NOK:{e}"

                elif cmd == "TRIGGER":
                    if device is None:
                        response = "NOK:No active calibration"
                    else:
                        try:
                            result = device.trigger()
                            marker_count = result.count_of_recognized_marker_points
                            response = f"OK, markers recognized: {marker_count}"
                            print(
                                f"Trigger OK: frames={result.count_of_acquired_scans}, "
                                f"markers={marker_count}"
                            )
                        except PhoXiError as e:
                            response = f"NOK:{e}"

                elif cmd == "ANALYZE":
                    if device is None:
                        response = "NOK:No active calibration"
                    else:
                        try:
                            score = device.analyze()
                            response = f"OK, area occupancy score: {score:.6f}"
                            print(f"Analysis OK, occupancy score: {score:.6f}")
                        except PhoXiError as e:
                            response = f"NOK:{e}"

                elif cmd == "PATCH":
                    if device is None:
                        response = "NOK:No active calibration"
                    else:
                        try:
                            device.patch()
                            response = "OK"
                            print("Patch applied successfully.")
                            device = None  # patch() disconnects the device
                        except PhoXiError as e:
                            response = f"NOK:{e}"

                elif cmd == "STOP_CALIBRATION":
                    if device is not None:
                        device = cleanup_device(device)
                    response = "OK"
                    print("Calibration stopped.")

                else:
                    response = f"NOK:Unknown command '{cmd}'"

                # Send response
                conn.sendall((response + "\n").encode("utf-8"))
                print(f"Sent: {response}")

            except TimeoutError:
                # No data, but connection still alive - continue
                continue
            except ConnectionResetError:
                print("Client reset the connection.")
                break
            except Exception as e:
                print(f"Unexpected error in client loop: {e}")
                break

    finally:
        # Ensure device is cleaned up when this client disconnects
        cleanup_device(device)
        conn.close()
        print("Connection closed and device released.")


if __name__ == "__main__":
    print("Photoneo MaintenanceTool server (robot-controlled client)")

    mt = MaintenanceTool()
    server_socket = None

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((SERVER_HOST, SERVER_PORT))
        server_socket.listen(5)  # allow backlog
        print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")
        print("Waiting for a robot client (Ctrl+C to stop)...")

        while True:
            conn, addr = server_socket.accept()
            handle_client(conn, addr, mt)

    except KeyboardInterrupt:
        print("\nServer stopped by user.")
    except Exception as e:
        print(f"Fatal server error: {e}")
        sys.exit(1)
    finally:
        if server_socket:
            server_socket.close()
        print("Server shutdown complete.")
