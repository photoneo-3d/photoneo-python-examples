#!/usr/bin/env python3
import sys
from pathlib import Path

import open3d as o3d
from genicam.genapi import NodeMap
from harvesters.core import Component2DImage, Harvester

from photoneo_genicam.components import enable_components
from photoneo_genicam.default_gentl_producer import producer_path
from photoneo_genicam.features import enable_software_trigger
from photoneo_genicam.pointcloud import create_3d_vector
from photoneo_genicam.user_set import load_default_user_set
from photoneo_genicam.visualizer import render_static


def main(device_sn: str):
    with Harvester() as h:
        h.add_file(str(producer_path), check_existence=True, check_validity=True)
        h.update()

        with h.create({"serial_number": device_sn}) as ia:
            features: NodeMap = ia.remote_device.node_map

            load_default_user_set(features)
            enable_software_trigger(features)
            enable_components(features, ["Range"])

            # This is the default value.
            features.Scan3dOutputMode.value = "CalibratedABC_Grid"

            ia.start()
            features.TriggerSoftware.execute()
            with ia.fetch() as buffer:
                point_cloud_raw: Component2DImage = buffer.payload.components[0]
                point_cloud = o3d.geometry.PointCloud()
                point_cloud.points = create_3d_vector(point_cloud_raw.data.copy())
                o3d.io.write_point_cloud("pointcloud.ply", point_cloud)
                render_static([point_cloud])


if __name__ == "__main__":
    try:
        device_id = sys.argv[1]
    except IndexError:
        print("Error: no device given, please run it with the device serial number as argument:")
        print(f"    {Path(__file__).name} <device serial>")
        sys.exit(1)
    main(device_id)
