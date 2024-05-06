#!/usr/bin/env python3
import sys
from pathlib import Path

import numpy as np
import open3d as o3d
from genicam.genapi import NodeMap
from harvesters.core import Component2DImage, Harvester

from photoneo_genicam.chunks import get_transformation_matrix_from_chunk, parse_chunk_selector
from photoneo_genicam.components import enable_components, enabled_components
from photoneo_genicam.default_gentl_producer import producer_path
from photoneo_genicam.features import enable_software_trigger
from photoneo_genicam.pointcloud import create_3d_vector, map_texture
from photoneo_genicam.user_set import load_default_user_set
from photoneo_genicam.visualizer import render_static


def main(device_sn: str):
    with Harvester() as h:
        np.set_printoptions(suppress=True)
        h.add_file(str(producer_path), check_existence=True, check_validity=True)
        h.update()

        with h.create({"serial_number": device_sn}) as ia:
            features: NodeMap = ia.remote_device.node_map

            load_default_user_set(features)
            enable_software_trigger(features)
            enable_components(features, ["Intensity", "Range"])

            features.Scan3dOutputMode.value = "CalibratedABC_Grid"
            features.RecognizeMarkers.value = True
            features.CoordinateSpace.value = "MarkerSpace"

            features.ChunkModeActive.value = True
            features.ChunkSelector.value = "CurrentCameraToCoordinateSpaceTransformation"
            features.ChunkEnable.value = True

            ia.start()
            features.TriggerSoftware.execute()

            # If no marker is recognized, the fetch will time out.
            with ia.fetch(timeout=10) as buffer:
                components = dict(zip(enabled_components(features), buffer.payload.components))
                intensity_component: Component2DImage = components["Intensity"]
                point_cloud_raw: Component2DImage = components["Range"]

                chunk_name: str = "CurrentCameraToCoordinateSpaceTransformation"
                parsed_chunk_data: dict = parse_chunk_selector(
                    features, chunk_feature_name=chunk_name
                )
                transformation_matrix: np.ndarray = get_transformation_matrix_from_chunk(
                    parsed_chunk_data
                )
                print(transformation_matrix)

                point_cloud = o3d.geometry.PointCloud()
                point_cloud.points = create_3d_vector(point_cloud_raw.data)
                point_cloud.colors = map_texture(intensity_component)
                point_cloud.transform(transformation_matrix)
                render_static([point_cloud])


if __name__ == "__main__":
    try:
        device_id = sys.argv[1]
    except IndexError:
        print("Error: no device given, please run it with the device serial number as argument:")
        print(f"    {Path(__file__).name} <device serial>")
        sys.exit(1)
    main(device_id)
