from packaging import version

from .features import CameraFeature
from .utils import DeviceType

ISO = CameraFeature(
    name="ISO",
    settings=["ISO"],
    min_firmware_version=version.parse("1.15.0"),
    supported_device_types=DeviceType.all(),
)

ProjectionOffset = CameraFeature(
    name="ProjectionOffset",
    settings=["ProjectionOffsetLeft", "ProjectionOffsetRight"],
    min_firmware_version=version.parse("1.15.0"),
    supported_device_types=DeviceType.all(),
)

HDR = CameraFeature(
    name="HDR",
    settings=["HDR"],
    min_firmware_version=version.parse("1.16.0"),
    supported_device_types=[DeviceType.PHOXI_SCANNER_GEN3],
)
