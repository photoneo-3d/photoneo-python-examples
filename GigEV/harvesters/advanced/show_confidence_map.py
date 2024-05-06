#!/usr/bin/env python3
import sys
from pathlib import Path

import cv2
from genicam.genapi import NodeMap
from harvesters.core import Component2DImage, Harvester

from photoneo_genicam.components import enable_components
from photoneo_genicam.default_gentl_producer import producer_path
from photoneo_genicam.features import enable_software_trigger
from photoneo_genicam.user_set import load_default_user_set
from photoneo_genicam.visualizer import process_for_visualisation


def main(device_sn: str):
    with Harvester() as h:
        h.add_file(str(producer_path), check_existence=True, check_validity=True)
        h.update()

        with h.create({"serial_number": device_sn}) as ia:
            features: NodeMap = ia.remote_device.node_map

            load_default_user_set(features)
            enable_software_trigger(features)

            enable_components(features, ["Range", "Confidence"])
            features.Scan3dOutputMode.value = "ProjectedC"

            ia.start()
            features.TriggerSoftware.execute()
            with ia.fetch(timeout=10) as buffer:
                depth: Component2DImage = buffer.payload.components[0]
                confidence: Component2DImage = buffer.payload.components[1]

                dept_img = process_for_visualisation(depth)
                cnf_img = process_for_visualisation(confidence)
                cv2.imshow("DepthMap", dept_img)
                cv2.imshow("ConfidenceMap", cnf_img)

            while True:
                key = cv2.waitKey(1) & 0xFF
                if key == 27:
                    break

                # Add a check for window closing event
                if cv2.getWindowProperty('DepthMap', cv2.WND_PROP_VISIBLE) < 1:
                    break
                if cv2.getWindowProperty('ConfidenceMap', cv2.WND_PROP_VISIBLE) < 1:
                    break

            cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        device_id = sys.argv[1]
    except IndexError:
        print("Error: no device given, please run it with the device serial number as argument:")
        print(f"    {Path(__file__).name} <device serial>")
        sys.exit(1)
    main(device_id)
