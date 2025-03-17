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
from photoneo_genicam.pointcloud import (calculate_point_cloud_from_projc,
                                         create_3d_vector,
                                         pre_fetch_coordinate_maps)
from photoneo_genicam.user_set import load_default_user_set
from photoneo_genicam.utils import data_stream_reset, logger
from photoneo_genicam.visualizer import RealTimePCLRenderer

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

            load_default_user_set(features)

            logger.info("Pre-fetch CoordinateMaps")
            coordinate_map: np.array = pre_fetch_coordinate_maps(ia)

            enable_components(features, ["Range"])

            features.Scan3dOutputMode.value = "ProjectedC"
            if features.IsMotionCam3D_Val.value:
                features.CameraTextureSource.value = "Laser"
            else:
                features.TextureSource.value = "Laser"

            data_stream_reset(ia)
            ia.start()
            frame_counter = 0
            total_fps = 0.0
            pcl_renderer = RealTimePCLRenderer()
            while not pcl_renderer.should_close:
                with ia.fetch(timeout=10) as buffer:
                    depth_map: Component2DImage = buffer.payload.components[0]
                    pcl: np.array = calculate_point_cloud_from_projc(
                        depth_map.data.copy(), coordinate_map
                    )

                    points: o3d.utility.Vector3dVector = create_3d_vector(pcl)
                    if frame_counter == 0:
                        point_cloud: o3d.geometry.PointCloud = o3d.geometry.PointCloud(
                            points=points
                        )
                        pcl_renderer.vis.add_geometry(point_cloud)
                    else:
                        point_cloud.points.clear()
                        point_cloud.points.extend(points)
                        pcl_renderer.vis.update_geometry(point_cloud)
                    frame_counter += 1
                    total_fps += ia.statistics.fps

                    pcl_renderer.vis.poll_events()
                    pcl_renderer.vis.update_renderer()
                    print(f"Avg FPS: {round(total_fps / frame_counter, 2)}", end="\r")

            pcl_renderer.vis.destroy_window()


if __name__ == "__main__":
    try:
        device_id = sys.argv[1]
    except IndexError:
        print("Error: no device given, please run it with the device serial number as argument:")
        print(f"    {Path(__file__).name} <device serial>")
        sys.exit(1)
    main(device_id)
