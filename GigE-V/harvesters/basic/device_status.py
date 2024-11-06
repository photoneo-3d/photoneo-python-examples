#!/usr/bin/env python3
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

            def mark_enabled(pixel_format):
                return ("*" if features.PixelFormat.value == pixel_format else "") + pixel_format

            print(f"DeviceFirmwareVersion: {features.DeviceFirmwareVersion.value}")
            print(f"DeviceModelName: {features.DeviceModelName.value}")
            print(f"DeviceUserID: {features.DeviceUserID.value}")
            print()

            print("Components:")
            for component in features.ComponentSelector.symbolics:
                features.ComponentSelector.value = component
                print(
                    f"  {component:<15}"
                    f"{'Enabled' if features.ComponentEnable.value else 'Disabled':<10}"
                    f"({', '.join(mark_enabled(pf) for pf in features.PixelFormat.symbolics):>})"
                )
            print()
            print("Chunks")
            print(f"  ChunkModeActive: {features.ChunkModeActive.value}")
            for chunk in features.ChunkSelector.symbolics:
                features.ChunkSelector.value = chunk
                print(
                    f"  Chunk {chunk}: {'Enabled' if features.ComponentEnable.value else 'Disabled'}"
                )
            print()

            features.TriggerSelector.value = "FrameStart"
            print(f"TriggerMode: {features.TriggerMode.value}")
            if features.TriggerMode.value == "On":
                print(f"TriggerSource: {features.TriggerSource.value}")
            print(f"Scan3dOutputMode: {features.Scan3dOutputMode.value}")
            print(f"CalibrationVolumeOnly: {features.CalibrationVolumeOnly.value}")

            if features.IsMotionCam3D_Val.value:
                operation_mode: str = features.OperationMode.value
                print(f"OperationMode")

                print(f"{'  Camera*' if operation_mode == 'Camera' else '  Camera'}")
                print(f"    CameraTextureSource: {features.CameraTextureSource.value}")
                print(f"    CameraCodingStrategy: {features.CameraCodingStrategy.value}")

                print(f"{'  Scanner*' if operation_mode == 'Scanner' else '  Scanner'}")
                print(f"    TextureSource: {features.TextureSource.value}")
                print(f"    CodingStrategy: {features.CodingStrategy.value}")

                print(f"CodingQuality: {features.CodingQuality.value}")
                print(f"OutputTopology: {features.OutputTopology.value}")
            else:
                print(f"CodingQuality: {features.CodingQuality.value}")
                print(f"TextureSource: {features.TextureSource.value}")


if __name__ == "__main__":
    try:
        device_id = sys.argv[1]
        main(device_id)
    except IndexError:
        print("Error: no device given, please run it with the device serial number as argument:")
        print(f"{Path(__file__).name} <device serial>")
        sys.exit(1)
