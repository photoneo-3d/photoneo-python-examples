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

            # Restore default settings.
            features.UserSetSelector.value = "Default"
            features.UserSetLoad.execute()

            for setting in features.UserSetFeatureSelector.symbolics:
                try:
                    setting_value = features.get_node(setting).value
                    print(f"{setting}: {setting_value}")
                except Exception as e:
                    continue


if __name__ == "__main__":
    try:
        device_id = sys.argv[1]
        main(device_id)
    except IndexError:
        print("Error: no device given, please run it with the device serial number as argument:")
        print(f"{Path(__file__).name} <device serial>")
        sys.exit(1)
