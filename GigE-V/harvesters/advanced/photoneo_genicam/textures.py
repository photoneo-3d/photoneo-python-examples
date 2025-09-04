from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import List

from genicam.genapi import NodeMap

from .components import enable_components
from .utils import DeviceType, detect_device_type, logger


class PixelFormat(Enum):
    RGB8 = "RGB8"
    COORD3D_C32F = "Coord3D_C32f"
    CONFIDENCE8 = "Confidence8"
    MONO10 = "Mono10"
    MONO12 = "Mono12"
    MONO16 = "Mono16"
    COORD3D_ABC32F = "Coord3D_ABC32f"

    def __str__(self):
        return self.value


class TextureSource(Enum):
    UNKNOWN = "Unknown"
    LASER = "Laser"
    LASER_ENHANCED = "LaserEnhanced"
    LED = "LED"
    COLOR = "Color"
    COMPUTED = "Computed"
    COMPUTED_ENHANCED = "ComputedEnhanced"
    FOCUS = "Focus"

    def __str__(self):
        return self.value

    @classmethod
    def from_str(cls, value: str) -> "TextureSource":
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"Unknown TextureSource: {value}")


class OperationMode(Enum):
    SCANNER = "Scanner"
    CAMERA = "Camera"

    def __str__(self):
        return self.value

    @classmethod
    def from_str(cls, value: str) -> "OperationMode":
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"Unknown OperationMode: {value}")


class CameraSpace(Enum):
    MARKER_ORTHO_CAMERA = "MarkerOrthoCamera"
    CUSTOM_CAMERA = "CustomCamera"
    COLOR_CAMERA = "ColorCamera"
    PRIMARY_CAMERA = "PrimaryCamera"

    def __str__(self):
        return self.value


@dataclass
class TextureOption:
    texture_source: TextureSource
    pixel_format: PixelFormat
    camera_space: CameraSpace = CameraSpace.PRIMARY_CAMERA
    component: str = "Intensity"
    configuration_name = ""

    def get_ts_modifier(self, features) -> str:
        current_device_type: DeviceType = detect_device_type(features)
        if current_device_type in [
            DeviceType.MOTION_CAM_3D,
            DeviceType.MOTIONCAM_3D_COLOR,
        ]:
            operation_mode: OperationMode = OperationMode.from_str(
                features.OperationMode.value
            )
            if operation_mode == OperationMode.CAMERA:
                return "CameraTextureSource"
        return "TextureSource"

    def get_texture_source_options(
        self, features: NodeMap, ts_modifier: str
    ) -> List[TextureSource]:
        return [
            TextureSource.from_str(ts)
            for ts in features.get_node(ts_modifier).symbolics
        ]

    def set_texture_source(self, features: NodeMap, texture_source: TextureSource):
        ts_modifier: str = self.get_ts_modifier(features)
        if texture_source in self.get_texture_source_options(features, ts_modifier):
            features.get_node(ts_modifier).value = str(texture_source)
        else:
            logger.warning(
                f"TextureSource: {texture_source} is not available. Skipping."
            )
            return

    def apply(self, features: NodeMap):
        current_device_type: DeviceType = detect_device_type(features)
        self.set_texture_source(features, self.texture_source)
        enable_components(features, [self.component])

        features.PixelFormat.value = str(self.pixel_format)

        if current_device_type in [
            DeviceType.MOTIONCAM_3D_COLOR,
            DeviceType.PHOXI_SCANNER_GEN3,
        ]:
            features.CameraSpace.value = str(self.camera_space)

        self.configuration_name = (
            f"TextureSource: {self.texture_source}, "
            f"PixelFormat: {self.pixel_format}, "
            f"Component: {self.component}, "
            f"CameraSpace: {self.camera_space}"
        )


INTENSITY_RGB = TextureOption(
    TextureSource.COLOR, PixelFormat.RGB8, CameraSpace.PRIMARY_CAMERA, "Intensity"
)
INTENSITY_RGB_COLOR_CAMERA = TextureOption(
    TextureSource.COLOR, PixelFormat.RGB8, CameraSpace.COLOR_CAMERA, "Intensity"
)
INTENSITY_MONO10 = TextureOption(
    TextureSource.LED, PixelFormat.MONO10, CameraSpace.PRIMARY_CAMERA, "Intensity"
)
INTENSITY_MONO10_LASER = TextureOption(
    TextureSource.LASER, PixelFormat.MONO10, CameraSpace.PRIMARY_CAMERA, "Intensity"
)
INTENSITY_MONO10_LASER_ENHANCED = TextureOption(
    TextureSource.LASER_ENHANCED,
    PixelFormat.MONO10,
    CameraSpace.PRIMARY_CAMERA,
    "Intensity",
)
INTENSITY_MONO10_COMPUTED = TextureOption(
    TextureSource.COMPUTED, PixelFormat.MONO10, CameraSpace.PRIMARY_CAMERA, "Intensity"
)
INTENSITY_MONO10_COMPUTED_ENHANCED = TextureOption(
    TextureSource.COMPUTED_ENHANCED,
    PixelFormat.MONO10,
    CameraSpace.PRIMARY_CAMERA,
    "Intensity",
)
COLOR_RGB = TextureOption(
    TextureSource.COLOR, PixelFormat.RGB8, CameraSpace.PRIMARY_CAMERA, "ColorCamera"
)
COLOR_MONO16 = TextureOption(
    TextureSource.COLOR, PixelFormat.MONO16, CameraSpace.PRIMARY_CAMERA, "ColorCamera"
)
INTENSITY_MONO12 = TextureOption(TextureSource.LED, PixelFormat.MONO12, CameraSpace.PRIMARY_CAMERA, "Intensity")
PHOXI_3D_SCANNER_ALPHA_DEFAULT = TextureOption(
    TextureSource.LED, PixelFormat.MONO10, CameraSpace.PRIMARY_CAMERA, "Intensity"
)

TEXTURE_MAP_BY_DEVICE_TYPE = defaultdict(list)

TEXTURE_MAP_BY_DEVICE_TYPE[DeviceType.MOTIONCAM_3D_COLOR] = [
    INTENSITY_RGB,
    INTENSITY_RGB_COLOR_CAMERA,
    INTENSITY_MONO10,
    COLOR_MONO16,
    COLOR_RGB,
    INTENSITY_MONO10_LASER,
    INTENSITY_MONO10_LASER_ENHANCED,
]
TEXTURE_MAP_BY_DEVICE_TYPE[DeviceType.MOTION_CAM_3D] = [
    INTENSITY_MONO10,
    INTENSITY_MONO10_LASER,
    INTENSITY_MONO10_LASER_ENHANCED,
]
TEXTURE_MAP_BY_DEVICE_TYPE[DeviceType.PHOXI_SCANNER_GEN3] = [
    INTENSITY_RGB,
    INTENSITY_RGB_COLOR_CAMERA,
    INTENSITY_MONO12,
    COLOR_MONO16,
    COLOR_RGB,
]
TEXTURE_MAP_BY_DEVICE_TYPE[DeviceType.PHOXI_3D_SCANNER] = [
    INTENSITY_MONO12,
]
TEXTURE_MAP_BY_DEVICE_TYPE[DeviceType.ALPHA_SCANNER] = [
    PHOXI_3D_SCANNER_ALPHA_DEFAULT,
]
