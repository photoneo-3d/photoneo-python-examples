import struct
import sys
from pathlib import Path

from genicam.genapi import NodeMap
from harvesters.core import Harvester

from common import cti_file_path


def main(device_sn: str):
    with Harvester() as h:
        print("Load .cti file...")
        h.add_file(str(cti_file_path), check_existence=True, check_validity=True)
        h.update()

        print(f"Connecting to: {device_sn}")
        with h.create({"serial_number": device_sn}) as ia:
            features: NodeMap = ia.remote_device.node_map

            print("Setting software trigger mode")
            # accessing features directly
            features.TriggerSelector.value = "FrameStart"
            features.TriggerMode.value = "On"
            features.TriggerSource.value = "Software"

            if features.IsMotionCam3D_Val.value:
                print("Setting 2D mode")
                # accessing features through string names
                old_mode = features.get_node("OperationMode").value
                features.get_node("OperationMode").value = "Mode_2D"

            # accessing features directly
            print(f"Width: {features.Width.value}")
            print(f"Height: {features.Height.value}")
            print(f"TriggerSelector: {features.TriggerSelector.value}")
            print(f"TriggerMode: {features.TriggerMode.value}")
            print(f"TriggerSource: {features.TriggerSource.value}")

            if features.IsMotionCam3D_Val.value:
                print(f"OperationMode: {features.OperationMode.value}")

            print("Reverting...")
            features.TriggerSelector.value = "FrameStart"
            features.TriggerMode.value = "Off"
            if features.IsMotionCam3D_Val.value:
                features.OperationMode.value = old_mode

            # This is a "raw" memory register, that contains a number of little endian doubles
            # (containing the opencv camera calibration parameters.)
            buffer_length = features.get_node("CameraMatrix").length
            buffer = features.get_node("CameraMatrix").get(buffer_length)
            value_count = int(buffer_length / 8)
            camera_matrix: tuple = struct.unpack(f"<{value_count}d", buffer)
            print(f"CameraMatrix: {camera_matrix}")

            # accessing features through string names
            features_to_print = [
                "TriggerSelector",
                "TriggerMode",
                "TriggerSource"
            ]
            for feature in features_to_print:
                print(f"{feature}: {features.get_node(feature).value}")

    print("Finished")


if __name__ == "__main__":
    try:
        device_id = sys.argv[1]
        main(device_id)
    except IndexError:
        print(
            f"Error: no device given, please run it with the device serial number as argument:"
        )
        print(f"{Path(__file__).name} <device serial>")
        sys.exit(1)
