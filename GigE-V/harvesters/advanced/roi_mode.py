#!/usr/bin/env python3
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
from genicam.genapi import NodeMap
from harvesters.core import Component2DImage, Harvester

from photoneo_genicam.components import enable_components
from photoneo_genicam.default_gentl_producer import producer_path
from photoneo_genicam.features import enable_software_trigger
from photoneo_genicam.user_set import load_default_user_set
from photoneo_genicam.utils import data_stream_reset, logger, version_check
from photoneo_genicam.visualizer import process_for_visualisation


@dataclass
class ColorSettingsROI:
    x1: int
    y1: int
    x2: int
    y2: int

    def is_valid(self):
        return (
            self.x1 > 0
            and self.y1 > 0
            and self.x2 > 0
            and self.y2 > 0
            and self.x1 < self.x2
            and self.y1 < self.y2
        )


roi_1 = ColorSettingsROI(x1=600, y1=600, x2=900, y2=900)


def main(device_sn: str):
    with Harvester() as h:
        h.add_file(str(producer_path), check_existence=True, check_validity=True)
        h.update()

        logger.info(f"Connecting to: {device_sn}")
        with h.create({"serial_number": device_sn}) as ia:
            features: NodeMap = ia.remote_device.node_map
            logger.info(f"Device Firmware version: {features.DeviceFirmwareVersion.value}")

            version_check(features, "1.14.0-a")

            load_default_user_set(features)
            enable_software_trigger(features)

            enable_components(features, ["Intensity"])
            features.CameraSpace.value = "ColorCamera"

            for option in [False, True]:
                if option:
                    features.ColorSettings_ROIMode.value = "Custom"
                    features.ColorSettings_ROI_XMin.value = roi_1.x1
                    features.ColorSettings_ROI_YMin.value = roi_1.y1
                    features.ColorSettings_ROI_XMax.value = roi_1.x2
                    features.ColorSettings_ROI_YMax.value = roi_1.y2
                    logger.info(
                        f"Using ROI xmin={roi_1.x1}, ymin={roi_1.y1}, xmax={roi_1.x2}, ymax={roi_1.y2}"
                    )
                else:
                    logger.info("Using default resolution")

                data_stream_reset(ia)
                ia.start()
                features.TriggerSoftware.execute()
                with ia.fetch(timeout=10) as buffer:
                    image: Component2DImage = buffer.payload.components[0]
                    image_name = "roi_on.png" if option else "roi_off.png"
                    logger.info(f"[{image_name}] Image dimensions: {image.width}x{image.height}")
                    size_in_MB = image.data.size * image.data.itemsize / (1024**2)
                    logger.info(f"[{image_name}] Size of array: {size_in_MB:.2f} MB")
                    cv2.imwrite(image_name, process_for_visualisation(image))
                ia.stop()
                time.sleep(1)


if __name__ == "__main__":
    try:
        device_id = sys.argv[1]
    except IndexError:
        print("Error: no device given, please run it with the device serial number as argument:")
        print(f"    {Path(__file__).name} <device serial>")
        sys.exit(1)
    main(device_id)
