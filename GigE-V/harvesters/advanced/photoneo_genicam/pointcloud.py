import numpy as np
import open3d as o3d
from genicam.genapi import NodeMap
from harvesters.core import Component2DImage, ImageAcquirer

from .components import enable_components
from .features import enable_software_trigger
from .user_set import load_default_user_set
from .utils import measure_time


def calculate_point_cloud_from_projc(depth_map: np.ndarray, coordinate_map: np.ndarray) -> np.array:
    return depth_map[:, np.newaxis] * coordinate_map


def construct_coordinate_map(
    coordinate_a: np.ndarray,
    coordinate_b: np.ndarray,
    focal_length: float,
    aspect_ratio: float,
    principal_point_u: float,
    principal_point_v: float,
) -> np.array:
    x = (coordinate_a - principal_point_u) / focal_length
    y = (coordinate_b - principal_point_v) / (focal_length * aspect_ratio)
    z = np.ones_like(x)
    return np.stack([x, y, z], axis=-1)


# The astype(np.float64) operation is required to make this operation fast
def create_3d_vector(input_array_as_np: np.ndarray):
    return o3d.utility.Vector3dVector(input_array_as_np.reshape(-1, 3).astype(np.float64))


def map_texture(texture: Component2DImage) -> o3d.utility.Vector3dVector:
    # o3d point colors property expect (num_points, 3), range [0, 1] format
    if texture.data_format == "RGB8":
        return o3d.utility.Vector3dVector(texture.data.reshape(-1, 3).astype(np.float64) / 255.0)
    if texture.data_format == "Mono10":
        normalized = texture.data.reshape(-1, 1).astype(np.float64) / 1024.0
        return o3d.utility.Vector3dVector(np.repeat(normalized, 3, axis=-1))
    if texture.data_format == "Mono12":
        normalized = texture.data.reshape(-1, 1).astype(np.float64) / 4096.0
        return o3d.utility.Vector3dVector(np.repeat(normalized, 3, axis=-1))
    if texture.data_format == "Mono16":
        normalized = texture.data.reshape(-1, 1).astype(np.float64) / 65536.0
        return o3d.utility.Vector3dVector(np.repeat(normalized, 3, axis=-1))


@measure_time
def pre_fetch_coordinate_maps(ia: ImageAcquirer) -> np.ndarray:
    assert not ia.is_acquiring(), "Acquisition is not stopped"

    features: NodeMap = ia.remote_device.node_map

    trigger_mode_before_pre_fetch = features.TriggerMode.value
    trigger_source_before_pre_fetch = features.TriggerSource.value

    enable_software_trigger(features)
    enable_components(features, ["CoordinateMapA", "CoordinateMapB"])

    focal_length: float = features.Scan3dFocalLength.value
    aspect_ratio: float = features.Scan3dAspectRatio.value
    ppu: float = features.Scan3dPrincipalPointU.value
    ppv: float = features.Scan3dPrincipalPointV.value

    ia.start()
    features.TriggerSoftware.execute()

    coord_map: np.ndarray = None
    with ia.fetch(timeout=3) as buffer:
        coordinate_map_a: Component2DImage = buffer.payload.components[0]
        coordinate_map_b: Component2DImage = buffer.payload.components[1]
        coord_map = construct_coordinate_map(
            coordinate_map_a.data, coordinate_map_b.data, focal_length, aspect_ratio, ppu, ppv
        )
    ia.stop()

    features.TriggerMode.value = trigger_mode_before_pre_fetch
    features.TriggerSource.value = trigger_source_before_pre_fetch
    return coord_map
