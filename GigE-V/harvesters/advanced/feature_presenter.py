#!/usr/bin/env python3
import sys
import time
from pathlib import Path

from genicam.genapi import NodeMap
from harvesters.core import Component2DImage, Harvester

from photoneo_genicam.camera_features import *
from photoneo_genicam.components import enable_components
from photoneo_genicam.default_gentl_producer import producer_path
from photoneo_genicam.features import Presenter, enable_software_trigger
from photoneo_genicam.user_set import load_default_user_set
from photoneo_genicam.utils import data_stream_reset, logger
from photoneo_genicam.visualizer import TextureImage


FEATURES_TO_PRESENT = [
    Presenter(None, [], [("TextureSource", "LED")]),
    Presenter(ProjectionOffset, [150, 150], []),
    Presenter(ISO, [300], [("TextureSource", "LED")]),
    Presenter(HDR, ["Strong"], [("TextureSource", "LED"), ("ISO", "1600")]),
]


def main(device_sn: str):
    with Harvester() as h:
        h.add_file(str(producer_path), check_existence=True, check_validity=True)
        h.update()

        images = []
        logger.info(f"Connecting to: {device_sn}")
        with h.create({"serial_number": device_sn}) as ia:
            features: NodeMap = ia.remote_device.node_map
            logger.info(
                f"Device Firmware version: {features.DeviceFirmwareVersion.value}"
            )

            for option in FEATURES_TO_PRESENT:
                load_default_user_set(features)
                enable_software_trigger(features)
                enable_components(features, ["Intensity"])

                filename: str = option.apply(features)
                if not filename:
                    continue

                data_stream_reset(ia)
                ia.start()
                features.TriggerSoftware.execute()
                with ia.fetch(timeout=10) as buffer:
                    intensity_texture: Component2DImage = buffer.payload.components[0]
                    images.append(TextureImage(f"{filename}", image=intensity_texture))
                    time.sleep(1)
                ia.stop()

            for image in images:
                image.save()


if __name__ == "__main__":
    try:
        device_id = sys.argv[1]
    except IndexError:
        print(
            "Error: no device given, please run it with the device serial number as argument:"
        )
        print(f"    {Path(__file__).name} <device serial>")
        sys.exit(1)
    main(device_id)
