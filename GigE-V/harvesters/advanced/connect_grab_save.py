#!/usr/bin/env python3
import sys
from pathlib import Path

import cv2
import numpy as np
from genicam.genapi import NodeMap
from harvesters.core import Component2DImage, Harvester

from photoneo_genicam.components import (enable_components, enabled_components,
                                         get_component_statuses)
from photoneo_genicam.default_gentl_producer import producer_path
from photoneo_genicam.features import enable_software_trigger
from photoneo_genicam.user_set import load_default_user_set
from photoneo_genicam.utils import write_raw_array


def process_component(component_name: str, component: Component2DImage):
    pixel_format = component.data_format
    if component_name in ("Intensity", "ColorCamera"):
        component_data = component.data.copy()
        if pixel_format == "Mono10":
            data = ((component_data.astype(np.uint16) << 6).reshape(component.height, component.width, 1))
        elif pixel_format == "Mono12":
            data = ((component_data.astype(np.uint16) << 4).reshape(component.height, component.width, 1))
        elif pixel_format == "Mono16":
            data = component.data.reshape(component.height, component.width, 1)
        elif pixel_format == "RGB8":
            data = cv2.cvtColor(component.data.reshape((component.height, component.width, 3)), cv2.COLOR_RGB2BGR)
        else:
            raise Exception(f"Unknown pixel format option for component: {component_name}")
        cv2.imwrite(f"{component_name}_{pixel_format}.png", data)
    elif component_name == "Confidence":
        data = component.data.reshape(component.height, component.width, 1)
        cv2.imwrite(f"{component_name}_{pixel_format}.png", data)
    else:
        write_raw_array(f"{component_name}_{pixel_format}.dat", component.data)


def main(device_sn: str, *components: str):

    if len(components) == 0:
        print("Warning: No component specified, using default: Range.")
        components = ["Range"]

    with Harvester() as h:
        h.add_file(str(producer_path), check_existence=True, check_validity=True)
        h.update()

        print(f"Connecting to: {device_sn}")
        with h.create({"serial_number": device_sn}) as ia:
            features: NodeMap = ia.remote_device.node_map

            load_default_user_set(features)
            enable_software_trigger(features)

            print(f"Requested component(s): {components}")
            enable_components(features, list(components))
            print(get_component_statuses(features, include_pixel_format=True))

            ia.start()
            features.TriggerSoftware.execute()
            enabled_comps: list = enabled_components(features)
            with ia.fetch(timeout=10) as buff:
                # match the components based on their order
                for component_name, part in zip(enabled_comps, buff.payload.components):
                    print(f"Saving component {component_name}")
                    print(f"  Data: {part}\n")
                    process_component(component_name, part)


if __name__ == "__main__":
    try:
        device_id = sys.argv[1]
        component_names = sys.argv[2:]
    except IndexError:
        print(
            "Error: no device or component given, please run it with the device serial number as argument:"
        )
        print(f"    {Path(__file__).name} <device serial> <component_name1> <component_name2> ...")
        sys.exit(1)
    main(device_id, *component_names)
