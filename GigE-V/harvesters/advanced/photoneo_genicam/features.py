from dataclasses import dataclass
from typing import Any, List, Tuple

from genicam.genapi import NodeMap
from packaging import version

from .utils import DeviceType, detect_device_type, setup_logger

logger = setup_logger()


def enable_trigger(features: NodeMap, source: str):
    features.TriggerSelector.value = "FrameStart"
    features.TriggerMode.value = "On"
    features.TriggerSource.value = source


def enable_software_trigger(features: NodeMap):
    enable_trigger(features, "Software")


def enable_hardware_trigger(features: NodeMap):
    enable_trigger(features, "Line1")


@dataclass
class CameraFeature:
    name: str
    settings: List[str]
    min_firmware_version: version.Version
    supported_device_types: List[DeviceType]


class Presenter:
    def __init__(
        self,
        cam_feature: CameraFeature,
        f_settings: List[Any],
        a_settings: List[Tuple[str, str]],
    ):
        self.camera_feature = cam_feature
        self.feature_settings = f_settings
        self.additional_settings = a_settings

        if self.feature_settings and (
            len(self.feature_settings) < len(cam_feature.settings)
        ):
            raise Exception("This feature needs more values to set.")

    def is_device_type_supported(self, features) -> bool:
        if self.camera_feature:
            return detect_device_type(features) in self.camera_feature.supported_device_types
        return True

    def is_fw_supported(self, features) -> bool:
        if self.camera_feature:
            return version.Version(version.parse(str(features.DeviceFirmwareVersion.value)).base_version) >= \
                   version.Version(self.camera_feature.min_firmware_version.base_version)
        return True

    def construct_name(self) -> str:
        name: str = self.camera_feature.name if self.camera_feature else "DEFAULT"
        suffix = (
            "_" + "_".join(str(x) for x in self.feature_settings)
            if self.feature_settings
            else ""
        )
        return f"{name}{suffix}"

    def handle_texture_source_change(self, features, value):
        if detect_device_type(features) in [
            DeviceType.MOTION_CAM_3D,
            DeviceType.MOTIONCAM_3D_COLOR,
        ]:
            features.get_node("CameraTextureSource").value = value
        else:
            features.get_node("TextureSource").value = value

    def apply(self, features) -> str:
        if not self.is_device_type_supported(features):
            logger.warning(f"Feature {self.camera_feature.name} is not supported for current device type. Skipping...")
            return ""
        if not self.is_fw_supported(features):
            logger.warning(f"Feature {self.camera_feature.name} is not supported for current firmware version. Skipping...")
            return ""

        for a_setting, setting_value in self.additional_settings:
            if "TextureSource" in a_setting:
                self.handle_texture_source_change(features, setting_value)
            else:
                features.get_node(a_setting).value = setting_value

        if self.camera_feature:
            for f_name, f_value in zip(
                self.camera_feature.settings, self.feature_settings
            ):
                features.get_node(f_name).value = f_value

            logger.info(f"Presenting feature: {self.camera_feature.name}.")
        else:
            logger.info(f"Creating a DEFAULT image.")
        return self.construct_name()
