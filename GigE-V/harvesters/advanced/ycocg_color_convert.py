#!/usr/bin/env python3
import sys
from pathlib import Path

import cv2
import numpy as np
from genicam.genapi import NodeMap
from harvesters.core import Component2DImage, Harvester
from numba import jit

from photoneo_genicam.components import enable_components
from photoneo_genicam.default_gentl_producer import producer_path
from photoneo_genicam.features import enable_software_trigger
from photoneo_genicam.user_set import load_default_user_set
from photoneo_genicam.utils import (data_stream_reset, logger, logging,
                                    measure_time)

numba_logger = logging.getLogger("numba")
numba_logger.setLevel(logging.WARNING)


@jit(nopython=True)
def pixel_rgb(y: int, co: int, cg: int) -> np.ndarray:
    pixel_depth = 10

    if y == 0:
        return np.array((0, 0, 0)).reshape((1, 1, 3))

    delta: int = 1 << (pixel_depth - 1)
    max_value: int = 2 * delta - 1

    r1: int = 2 * y + co
    r: int = (r1 - cg) // 2 if r1 > cg else 0

    g1: int = y + cg // 2
    g: int = g1 - delta if g1 > delta else 0

    b1: int = y + 2 * delta
    b2: int = (co + cg) // 2
    b: int = b1 - b2 if b1 > b2 else 0

    return np.array((min(r, max_value), min(g, max_value), min(b, max_value))).reshape((1, 1, 3))


@measure_time
@jit(nopython=True)
def convert_to_rgb(ycocg_img) -> np.ndarray:
    pixel_depth: int = 10
    y_shift: int = np.iinfo(ycocg_img.dtype).bits - pixel_depth
    mask: int = (1 << y_shift) - 1

    rgb_img = np.empty((ycocg_img.shape[0], ycocg_img.shape[1], 3), dtype=np.uint16)

    for row in range(0, ycocg_img.shape[0], 2):
        for col in range(0, ycocg_img.shape[1], 2):
            y00 = ycocg_img[row, col] >> y_shift
            y01 = ycocg_img[row, col + 1] >> y_shift
            y10 = ycocg_img[row + 1, col] >> y_shift
            y11 = ycocg_img[row + 1, col + 1] >> y_shift

            co = ((ycocg_img[row, col] & mask) << y_shift) + (ycocg_img[row, col + 1] & mask)
            cg = ((ycocg_img[row + 1, col] & mask) << y_shift) + (
                ycocg_img[row + 1, col + 1] & mask
            )

            rgb_img[row, col] = pixel_rgb(y00, co, cg)
            rgb_img[row, col + 1] = pixel_rgb(y01, co, cg)
            rgb_img[row + 1, col] = pixel_rgb(y10, co, cg)
            rgb_img[row + 1, col + 1] = pixel_rgb(y11, co, cg)

    return rgb_img


def main(device_sn: str):
    with Harvester() as h:
        h.add_file(str(producer_path), check_existence=True, check_validity=True)
        h.update()

        logger.info(f"Connecting to: {device_sn}")
        with h.create({"serial_number": device_sn}) as ia:
            features: NodeMap = ia.remote_device.node_map
            logger.info(f"Device Firmware version: {features.DeviceFirmwareVersion.value}")

            if not features.IsMotionCam3DColor_Val.value:
                logger.warning("WARNING: This example is not supported on the current device type.")
                return

            load_default_user_set(features)
            enable_software_trigger(features)

            enable_components(features, ["ColorCamera"])

            features.PixelFormat.value = "Mono16"
            features.Scan3dOutputMode.value = "ProjectedC"

            data_stream_reset(ia)
            ia.start()
            features.TriggerSoftware.execute()
            with ia.fetch(timeout=10) as buffer:
                image_ycocg: Component2DImage = buffer.payload.components[0]
                reshaped_ycocg = image_ycocg.data.reshape(
                    image_ycocg.height, image_ycocg.width
                ).copy()
                cv2.imshow("YCoCg", reshaped_ycocg)
                logger.debug("Converting YCoCg to RGB...")
                img = convert_to_rgb(reshaped_ycocg)
                image_uint8 = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                cv2.imshow("YCoCg Converted", cv2.cvtColor(image_uint8, cv2.COLOR_RGB2BGR))

            # logger.info("Press ESC to close all windows")
            while True:
                key = cv2.waitKey(1) & 0xFF
                if key == 27:
                    break


if __name__ == "__main__":
    try:
        device_id = sys.argv[1]
    except IndexError:
        print("Error: no device given, please run it with the device serial number as argument:")
        print(f"    {Path(__file__).name} <device serial>")
        sys.exit(1)
    main(device_id)
