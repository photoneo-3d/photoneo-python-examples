#!/usr/bin/env python3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

import cv2
from genicam.genapi import NodeMap
from harvesters.core import Component2DImage, Harvester

from photoneo_genicam.components import enable_components
from photoneo_genicam.default_gentl_producer import producer_path
from photoneo_genicam.features import enable_software_trigger
from photoneo_genicam.user_set import load_default_user_set
from photoneo_genicam.utils import data_stream_reset, logger
from photoneo_genicam.visualizer import TextureImage


@dataclass
class TextureSourceConfig:
    texture_source: str = "Color"
    operation_mode: str = "Camera"
    pixel_format: str = "RGB8"
    component: str = "Intensity"
    camera_space: str = "PrimaryCamera"
    name = ""

    def apply_settings(self, features: NodeMap):
        is_color: bool = features.IsMotionCam3DColor_Val.value
        is_mc: bool = features.IsMotionCam3D_Val.value

        if is_mc:
            features.OperationMode.value = self.operation_mode
            if self.operation_mode == "Camera":
                features.CameraTextureSource.value = self.texture_source
            else:
                features.TextureSource.value = self.texture_source
        else:
            features.TextureSource.value = self.texture_source

        enable_components(features, [self.component])

        if is_color:
            features.CameraSpace.value = self.camera_space

        features.PixelFormat.value = self.pixel_format

        self.name = (
            f"TextureSource: {self.texture_source}, "
            f"PixelFormat: {self.pixel_format}, "
            f"Component: {self.component}, "
            f"CameraSpace: {self.camera_space}"
        )


def device_based_configs(features: NodeMap) -> List[TextureSourceConfig]:
    intensity_rgb = TextureSourceConfig(
        component="Intensity",
        camera_space="PrimaryCamera",
        texture_source="Color",
        pixel_format="RGB8",
    )
    intensity_mono10 = TextureSourceConfig(
        component="Intensity",
        camera_space="PrimaryCamera",
        texture_source="LED",
        pixel_format="Mono10",
    )
    color_rgb = TextureSourceConfig(
        component="ColorCamera",
        camera_space="PrimaryCamera",
        texture_source="Color",
        pixel_format="RGB8",
    )
    color_mono16 = TextureSourceConfig(
        component="ColorCamera",
        camera_space="PrimaryCamera",
        texture_source="Color",
        pixel_format="Mono16",
    )
    intensity_rgb_camera_space = TextureSourceConfig(
        component="Intensity",
        camera_space="ColorCamera",
        texture_source="Color",
        pixel_format="RGB8",
    )
    scanner_default = TextureSourceConfig(
        component="Intensity", texture_source="LED", pixel_format="Mono12"
    )
    alpha_default = TextureSourceConfig(
        component="Intensity", texture_source="LED", pixel_format="Mono10"
    )

    is_color: bool = features.IsMotionCam3DColor_Val.value
    is_mc: bool = features.IsMotionCam3D_Val.value
    is_scanner: bool = features.IsPhoXi3DScanner_Val.value
    is_alpha: bool = features.IsAlphaScanner_Val.value

    if is_color:
        logger.info(f"Device type: MotionCam3DColor")
        return [
            intensity_rgb,
            intensity_mono10,
            color_rgb,
            color_mono16,
            intensity_rgb_camera_space,
        ]
    if is_scanner and not is_alpha:
        logger.info(f"Device type: PhoXi3DScanner")
        return [scanner_default]
    if is_alpha and is_scanner:
        logger.info(f"Device type: AlphaScanner")
        return [alpha_default]
    if is_mc:
        logger.info(f"Device type: MotionCam3D")
        return [intensity_mono10]
    else:
        raise Exception("No config defined for current device type")


def main(device_sn: str):
    with Harvester() as h:
        h.add_file(str(producer_path), check_existence=True, check_validity=True)
        h.update()

        images = []
        logger.info(f"Connecting to: {device_sn}")
        with h.create({"serial_number": device_sn}) as ia:
            features = ia.remote_device.node_map
            logger.info(f"Device Firmware version: {features.DeviceFirmwareVersion.value}")

            example_options: List[TextureSourceConfig] = device_based_configs(features)
            load_default_user_set(features)
            enable_software_trigger(features)

            for setting_combination in example_options:
                setting_combination.apply_settings(features)

                data_stream_reset(ia)
                ia.start()
                features.TriggerSoftware.execute()
                with ia.fetch(timeout=10) as buffer:
                    img: Component2DImage = buffer.payload.components[0]
                    images.append(TextureImage(f"{setting_combination.name}", image=img))
                ia.stop()

        if len(images) == 0:
            logger.error("No images captured")
            return

        for image in images:
            image.show()

        logger.info("Press ESC to close all windows")
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == 27:
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
