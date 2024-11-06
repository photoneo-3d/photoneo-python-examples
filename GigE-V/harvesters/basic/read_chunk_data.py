#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import List

from genicam.genapi import NodeMap
from harvesters.core import Harvester

from gentl_producer_loader import producer_path


def print_chunk_options(features: NodeMap, chunk_feature_name: str):
    selector_alias: str = f"Chunk{chunk_feature_name}Selector"
    value_alias: str = f"Chunk{chunk_feature_name}Value"

    print(f"{chunk_feature_name}")
    # List all selector options
    selector_options: List[str] = features.get_node(selector_alias).symbolics
    for selector in selector_options:
        # Change selector value
        features.get_node(selector_alias).value = selector
        # Fetch selector option
        selector_value = features.get_node(value_alias).value
        print(f"  {selector}: {selector_value}")


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

            features.ChunkModeActive.value = True
            print("Available chunks to read:")
            print("\n".join(f"  {chunk}" for chunk in features.ChunkSelector.symbolics))

            # Enable Temperature chunk
            features.ChunkSelector.value = "Temperature"
            features.ChunkEnable.value = True

            # Enable MainCameraCalibrationData chunk
            features.ChunkSelector.value = "MainCameraCalibrationData"
            features.ChunkEnable.value = True

            ia.start()
            features.TriggerSoftware.execute()
            with ia.fetch(timeout=10) as buffer:
                temperature: float = features.ChunkTemperature.value
                print(f"Temperature chunk value: {temperature}")

                print_chunk_options(features, "MainCameraCameraMatrix")
                print_chunk_options(features, "MainCameraDistortionCoefficients")
                print_chunk_options(features, "MainCameraSensorAxis")
                print_chunk_options(features, "MainCameraSensorPosition")


if __name__ == "__main__":
    try:
        device_id = sys.argv[1]
        main(device_id)
    except IndexError:
        print("Error: no device given, please run it with the device serial number as argument:")
        print(f"{Path(__file__).name} <device serial>")
        sys.exit(1)
