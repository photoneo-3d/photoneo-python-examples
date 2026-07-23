# Demonstrates the MaintenanceTool API workflow: connect to a device, adjust its
# laser power and LED intensity, repeatedly trigger scans, analyze the results,
# and optionally apply a correction patch.
#
# Prerequisites:
#   - PHOXI_CONTROL_PATH environment variable pointing to PhoXi Control installation directory
#   - PhoXi Control running
#
# Usage:
#   python maintenance_tool_api_example.py                   # show expected connection failures
#   python maintenance_tool_api_example.py <SerialNumber>    # full workflow

import sys

from phoxi_api import MaintenanceTool
from phoxi_api.exceptions import PhoXiError

if __name__ == "__main__":
    mt = MaintenanceTool()

    major, minor, patch = mt.get_maintenance_tool_api_version()
    print(f"MaintenanceTool_API version: {major}.{minor}.{patch}")

    if not mt.check_phoxi_control_compatibility():
        print(
            "WARNING: Running PhoXiControl is not compatible with"
            " MaintenanceTool_API used by this example!"
        )
        sys.exit(2)

    if len(sys.argv) == 1:
        # No serial number provided — demonstrate expected-failure connection attempts.
        for serial in ["", "NonExistentSerialNumber"]:
            try:
                mt.connect(serial)
            except PhoXiError as e:
                print(f"Connection request with serial number '{serial}': {e}")
        sys.exit(0)

    serial_number = sys.argv[1]
    try:
        with mt.connect(serial_number) as device:
            print(f"Connection request with serial number '{serial_number}': succeeded")

            device.adjust_power()
            print("Adjust power: OK")

            while True:
                print("Ready for trigger? Or (q)uit?")
                user_input = input("Response: ")
                if user_input == "q":
                    break

                result = device.trigger()
                print(
                    f"Trigger request:"
                    f" frame count = {result.count_of_acquired_scans},"
                    f" marker point count = {result.count_of_recognized_marker_points}"
                )

            try:
                area_occupancy_score = device.analyze()
                print(
                    f"Analyze request:"
                    f" correction patch is ready to be applied,"
                    f" occupancy score = {area_occupancy_score}"
                )

                print("Do you want to apply the correction (p)atch?")
                user_input = input("Response: ")
                if user_input == "p":
                    device.patch()
                    print("Patch request: device patched")
            except PhoXiError as e:
                print(f"Analyze request: {e}")

    except PhoXiError as e:
        print(f"Connection request with serial number '{serial_number}': {e}")
        sys.exit(1)
