import sys
from pathlib import Path

import numpy as np
import open3d as o3d
from genicam.genapi import NodeMap
from harvesters.core import Harvester
from open3d.visualization import Visualizer

from common import (CONNECTION_SETTINGS, console, cti_file_path,
                    enable_components, RANGE, REPROJECTION)

FRAME_COUNT = 500


def calculate_point_cloud(
    depth_map: np.ndarray, reprojection_map: np.ndarray
) -> np.array:
    return depth_map.reshape(-1, 1) * reprojection_map


def get_reprojection_map(features: NodeMap, ia) -> np.ndarray:
    # Enable reprojection only
    enable_components(features, [REPROJECTION])

    # Enable software trigger
    features.TriggerSelector.value = "FrameStart"
    features.TriggerMode.value = "On"
    features.TriggerSource.value = "Software"

    ia.start()
    features.TriggerSoftware.execute()
    with ia.fetch() as buffer:
        repr_map = buffer.payload.components[0].data.copy()
        console.print("[green]Reprojection map acquired")

    ia.stop()
    return np.concatenate([repr_map.reshape(-1, 2), np.ones((repr_map.size // 2, 1))], axis=1,)


def main(device_sn: str):
    vis = Visualizer()
    vis.create_window()

    opt = vis.get_render_option()
    opt.point_size = 1.0
    opt.background_color = np.asarray([0.5, 0.5, 0.5])

    with Harvester() as h:
        h.add_file(str(cti_file_path), check_existence=True, check_validity=True)
        h.update()

        console.print(f"[bold]Connecting to: {device_sn}")
        with h.create({"serial_number": device_sn}, config=CONNECTION_SETTINGS) as ia:
            features: NodeMap = ia.remote_device.node_map

            reprojection_map: np.ndarray = get_reprojection_map(features, ia)

            features.TriggerSelector.value = "FrameStart"
            features.TriggerMode.value = "Off"

            width = features.Width.value
            height = features.Height.value

            # Enable Depth map only
            enable_components(features, [RANGE])

            console.print("[green]Start Freerun")
            ia.start()
            point_cloud = o3d.geometry.PointCloud()

            for frame_counter in range(FRAME_COUNT):
                with ia.fetch(timeout=10) as buff:
                    depth_map_buffer: np.ndarray = buff.payload.components[0].data
                    pcl_raw_nmp: np.ndarray = calculate_point_cloud(
                        depth_map_buffer, reprojection_map
                    )
                    point_cloud.points = o3d.utility.Vector3dVector(
                        pcl_raw_nmp.reshape(width * height, 3)
                    )
                if frame_counter == 0:
                    vis.add_geometry(point_cloud)
                else:
                    print(f"FPS: {round(ia.statistics.fps, 2)}", end="\r")
                    vis.update_geometry(point_cloud)
                    if not vis.poll_events():
                        break
                    vis.update_renderer()

    vis.destroy_window()


if __name__ == "__main__":
    try:
        device_id = sys.argv[1]
    except IndexError:
        print(
            f"Error: no device given, please run it with the device serial number as argument:"
        )
        print(f"    {Path(__file__).name} <device serial>")
        sys.exit(1)
    main(device_id)
