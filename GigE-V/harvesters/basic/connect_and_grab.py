#!/usr/bin/env python3
import struct
import sys
from pathlib import Path
from typing import List

from genicam.genapi import NodeMap
from harvesters.core import Component2DImage, Harvester

from gentl_producer_loader import producer_path


def write_raw_array(filename: str, array):
    with open(filename, "wb") as file:
        for element in array:
            file.write(element.tobytes())


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

            # Switch to software trigger to trigger only one frame.
            #
            # "FrameStart" is the only supported trigger currently, so the following line could
            # be skipped, but it's safer to set it in case more triggers are added in the future.
            features.TriggerSelector.value = "FrameStart"
            features.TriggerMode.value = "On"
            features.TriggerSource.value = "Software"

            ia.start()
            features.TriggerSoftware.execute()
            with ia.fetch(timeout=10) as buffer:
                # The harvesters  package doesn't currently allow to identify the components based on
                # ComponentIDValue but Photoneo devices always send the components in the order
                # of increasing ComponentIDValue. See advanced/connect_grab_save.py for
                # an example on how to do that.
                component_list: List[Component2DImage] = buffer.payload.components
                for i, component in enumerate(component_list):
                    print(
                        f"Component index: {i}\n"
                        f"DataFormat: {component.data_format}\n"
                        f"Element count per pixel: {component.num_components_per_pixel}\n"
                        f"Width x Height: {component.width} x {component.height}\n"
                        f"Length: {len(component.data)}\n"
                        f"Raw data: {component.data}\n"
                    )
                    raw_data_name = f"{i}.dat"
                    print(f"Saving raw data to: {raw_data_name}")
                    write_raw_array(raw_data_name, component.data.copy())


if __name__ == "__main__":
    try:
        device_id = sys.argv[1]
    except IndexError:
        print("Error: no device given, please run it with the device serial number as argument:")
        print(f"    {Path(__file__).name} <device serial>")
        sys.exit(1)
    main(device_id)
