#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import List

from genicam.genapi import NodeMap
from harvesters.core import Component2DImage, Harvester

from photoneo_genicam.default_gentl_producer import producer_path
from photoneo_genicam.features import enable_hardware_trigger
from photoneo_genicam.user_set import load_default_user_set


def main(device_sn: str):
    with Harvester() as h:
        h.add_file(str(producer_path), check_existence=True, check_validity=True)
        h.update()

        print(f"Connecting to: {device_sn}")
        with h.create({"serial_number": device_sn}) as ia:
            features: NodeMap = ia.remote_device.node_map

            load_default_user_set(features)
            enable_hardware_trigger(features)

            ia.start()
            timeout = 180
            print(f"Wait {timeout}s for hw-trigger signal...")
            with ia.fetch(timeout=timeout) as buffer:
                component_list: List[Component2DImage] = buffer.payload.components
                for component in component_list:
                    print(component)


if __name__ == "__main__":
    try:
        device_id = sys.argv[1]
    except IndexError:
        print("Error: no device given, please run it with the device serial number as argument:")
        print(f"    {Path(__file__).name} <device serial>")
        sys.exit(1)
    main(device_id)
