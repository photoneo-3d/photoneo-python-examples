#!/usr/bin/env python3
import sys
from pathlib import Path

from genicam.genapi import NodeMap
from harvesters.core import Harvester

from gentl_producer_loader import producer_path
from utils import data_stream_reset, logger

FRAME_COUNT = 50


def main(device_sn: str):
    with Harvester() as h:
        h.add_file(str(producer_path), check_existence=True, check_validity=True)
        h.update()

        logger.info(f"Connecting to: {device_sn}")
        with h.create({"serial_number": device_sn}) as ia:
            features: NodeMap = ia.remote_device.node_map
            logger.info(f"Device Firmware version: {features.DeviceFirmwareVersion.value}")

            # Load the Default user set to restore default settings
            # (which include continuous acquisition mode).
            features.UserSetSelector.value = "Default"
            features.UserSetLoad.execute()

            data_stream_reset(ia)
            ia.start()
            logger.info(f"Acquiring {FRAME_COUNT} frames.")
            frame_counter = 0
            fps_accumulated = 0.0
            while frame_counter != FRAME_COUNT:
                with ia.fetch(timeout=15):
                    print(
                        f"Frame ID: {frame_counter}  FPS:{round(ia.statistics.fps,2)}  ", end="\r"
                    )
                    frame_counter += 1
                    fps_accumulated += ia.statistics.fps

            print("\n")
            print(f"Avg FPS: {round(fps_accumulated / frame_counter, 2)}")
            print(f"Max FPS: {round(ia.statistics.fps_max,2)}")


if __name__ == "__main__":
    try:
        device_id = sys.argv[1]
    except IndexError:
        print("Error: no device given, please run it with the device serial number as argument:")
        print(f"    {Path(__file__).name} <device serial>")
        sys.exit(1)
    main(device_id)
