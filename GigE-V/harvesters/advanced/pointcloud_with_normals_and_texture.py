#!/usr/bin/env python3
import os
import sys
from pathlib import Path

import open3d as o3d
from genicam.genapi import NodeMap
from harvesters.core import Component2DImage, Harvester

from photoneo_genicam.components import enable_components, enabled_components
from photoneo_genicam.default_gentl_producer import producer_path
from photoneo_genicam.features import enable_software_trigger
from photoneo_genicam.pointcloud import create_3d_vector, map_texture
from photoneo_genicam.user_set import load_default_user_set
from photoneo_genicam.utils import data_stream_reset, logger
from photoneo_genicam.visualizer import render_static

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
            enable_software_trigger(features)

            features.Scan3dOutputMode.value = "CalibratedABC_Grid"
            enable_components(features, ["Intensity", "Range", "Normal"])

            data_stream_reset(ia)
            ia.start()
            features.TriggerSoftware.execute()
            with ia.fetch(timeout=10) as buffer:
                components = dict(zip(enabled_components(features), buffer.payload.components))
                intensity_component: Component2DImage = components["Intensity"]
                point_cloud_raw: Component2DImage = components["Range"]
                normal_component: Component2DImage = components["Normal"]

                point_cloud = o3d.geometry.PointCloud()
                point_cloud.points = create_3d_vector(point_cloud_raw.data)
                point_cloud.normals = create_3d_vector(normal_component.data)
                point_cloud.colors = map_texture(intensity_component)
                render_static([point_cloud])


if __name__ == "__main__":
    try:
        device_id = sys.argv[1]
    except IndexError:
        print("Error: no device given, please run it with the device serial number as argument:")
        print(f"    {Path(__file__).name} <device serial>")
        sys.exit(1)
    main(device_id)
