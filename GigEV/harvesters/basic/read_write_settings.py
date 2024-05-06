#!/usr/bin/env python3
import struct
import sys
from pathlib import Path

from genicam.genapi import NodeMap
from harvesters.core import Harvester

from gentl_producer_loader import producer_path


def main(device_sn: str):
    with Harvester() as h:
        h.add_file(str(producer_path), check_existence=True, check_validity=True)
        h.update()

        print(f"Connecting to: {device_sn}")
        with h.create({"serial_number": device_sn}) as ia:
            features: NodeMap = ia.remote_device.node_map

            # Restore default settings.
            features.UserSetSelector.value = "Default"
            features.UserSetLoad.execute()

            # Enable software trigger.
            features.TriggerSelector.value = "FrameStart"
            features.TriggerMode.value = "On"
            features.TriggerSource.value = "Software"

            if features.IsMotionCam3D_Val.value:
                # Accessing features through string values
                features.get_node("OperationMode").value = "Mode_2D"
                print(f"Operation mode: {features.OperationMode.value}")

            # Accessing features directly by their name
            print(f"Width: {features.Width.value}")
            print(f"Height: {features.Height.value}")
            print(f"CalibrationVolumeOnly: {features.CalibrationVolumeOnly.value}")
            print(f"ExposureTime: {features.ExposureTime.value}")
            print(f"ShutterMultiplier: {features.ShutterMultiplier.value}")
            print(f"NormalsEstimationRadius: {features.NormalsEstimationRadius.value}")
            print(f"LEDPower: {features.LEDPower.value}")
            print(f"LaserPower: {features.LaserPower.value}")

            # This is a "raw" memory register, that contains a number of little endian doubles
            # (containing the opencv camera calibration parameters.)
            buffer_length = features.get_node("CameraMatrix").length
            buffer = features.get_node("CameraMatrix").get(buffer_length)
            value_count = int(buffer_length / 8)
            camera_matrix: tuple = struct.unpack(f"<{value_count}d", buffer)
            print(f"CameraMatrix: {camera_matrix}")

            # accessing features through string names
            features_to_print = ["TriggerSelector", "TriggerMode", "TriggerSource"]
            for feature in features_to_print:
                print(f"{feature}: {features.get_node(feature).value}")

            # Loading default user set to restore changes
            features.UserSetSelector.value = "Default"
            features.UserSetLoad.execute()

    print("Finished")


if __name__ == "__main__":
    try:
        device_id = sys.argv[1]
        main(device_id)
    except IndexError:
        print("Error: no device given, please run it with the device serial number as argument:")
        print(f"{Path(__file__).name} <device serial>")
        sys.exit(1)
