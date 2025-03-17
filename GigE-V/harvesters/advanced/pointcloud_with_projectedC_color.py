#!/usr/bin/env python3
import os
import sys
from pathlib import Path

import numpy as np
import open3d as o3d
from genicam.genapi import NodeMap
from harvesters.core import Component2DImage, Harvester

from photoneo_genicam.components import enable_components
from photoneo_genicam.default_gentl_producer import producer_path
from photoneo_genicam.features import enable_software_trigger
from photoneo_genicam.pointcloud import (calculate_point_cloud_from_projc,
                                         create_3d_vector, map_texture,
                                         pre_fetch_coordinate_maps)
from photoneo_genicam.user_set import load_default_user_set
from photoneo_genicam.utils import data_stream_reset, logger, OSType
from photoneo_genicam.visualizer import pcl_offline_render, render_static

# For Ubuntu24 support with Wayland
os.environ["XDG_SESSION_TYPE"] = "x11"


def main(device_sn: str):
    with Harvester() as h:
        h.add_file(str(producer_path), check_existence=True, check_validity=True)
        h.update()

        logger.info(f"Connecting to: {device_sn}")
        with h.create({"serial_number": device_sn}) as ia:
            features: NodeMap = ia.remote_device.node_map
            logger.info(f"Device Firmware version: {features.DeviceFirmwareVersion.value}")

            if not features.IsMotionCam3D_Val.value:
                logger.error("Example not suppored for current device type.")
                return

            load_default_user_set(features)
            enable_software_trigger(features)
            features.CameraSpace.value = "ColorCamera"

            logger.info("Pre-fetch CoordinateMaps")
            coordinate_map: np.array = pre_fetch_coordinate_maps(ia)

            enable_components(features, ["Intensity", "Range"])
            features.CameraTextureSource.value = "Color"
            features.Scan3dOutputMode.value = "ProjectedC"

            data_stream_reset(ia)
            ia.start()

            features.TriggerSoftware.execute()
            with ia.fetch(timeout=10) as buffer:
                texture: Component2DImage = buffer.payload.components[0]
                depth_map: Component2DImage = buffer.payload.components[1]

                pcl: np.array = calculate_point_cloud_from_projc(
                    depth_map.data.copy(), coordinate_map
                )

                point_cloud: o3d.geometry.PointCloud = o3d.geometry.PointCloud(
                    points=create_3d_vector(pcl)
                )
                point_cloud.colors = map_texture(texture)

                os_type = OSType.detect()
                if os_type == OSType.LINUX:
                    pcl_offline_render(point_cloud, "PointCloudWithColorMapped.png")
                else:
                    render_static([point_cloud])


if __name__ == "__main__":
    try:
        device_id = sys.argv[1]
    except IndexError:
        print("Error: no device given, please run it with the device serial number as argument:")
        print(f"    {Path(__file__).name} <device serial>")
        sys.exit(1)
    main(device_id)
