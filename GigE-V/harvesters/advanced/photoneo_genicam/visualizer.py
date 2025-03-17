from dataclasses import dataclass
from typing import List

import cv2
import glfw
import numpy as np
import open3d as o3d
from harvesters.core import Component2DImage
from open3d.visualization import VisualizerWithKeyCallback

from .utils import logger


def render_static(objects: List, axes_size=70, width=1000, height=800, top=300, left=300):
    """
    Render a static Open3D geometry with axes.
    """
    axes = o3d.geometry.TriangleMesh.create_coordinate_frame(
        size=axes_size, origin=np.array([0, 0, 0])
    )
    o3d.visualization.draw_geometries(
        geometry_list=[axes] + objects, width=width, height=height, top=top, left=left
    )


def process_for_visualisation(image: Component2DImage):
    isRGB: bool = image.data_format == "RGB8"
    isDepth: bool = image.data_format == "Coord3D_C32f"
    isConfidence: bool = image.data_format == "Confidence8"
    isMono10: bool = image.data_format == "Mono10"
    isMono12: bool = image.data_format == "Mono12"
    isMono16: bool = image.data_format == "Mono16"
    isNormal: bool = image.data_format == "Coord3D_ABC32f"

    if isMono10:
        upscaled_to_16bit = image.data.astype(np.uint16) << 6
        return upscaled_to_16bit.reshape(image.height, image.width, 1).copy()
    if isMono12:
        upscaled_to_16bit = image.data.astype(np.uint16) << 4
        return upscaled_to_16bit.reshape(image.height, image.width, 1).copy()
    if isConfidence or isMono16:
        return image.data.reshape(image.height, image.width, 1).copy()
    if isDepth:
        image_array = image.data.reshape((image.height, image.width, 1))
        normalized_image = cv2.normalize(image_array, None, 0, 65535, cv2.NORM_MINMAX)
        return normalized_image.astype(np.uint16)
    if isRGB:
        return cv2.cvtColor(image.data.reshape((image.height, image.width, 3)), cv2.COLOR_RGB2BGR)
    if isNormal:
        image_array = image.data.reshape((image.height, image.width, 3))
        normalized_image = cv2.normalize(image_array, None, 0, 255, cv2.NORM_MINMAX)
        return normalized_image.astype(np.uint8)
    else:
        raise Exception("Unexpected pixel format")


class TextureImage:
    def __init__(self, name: str, image: Component2DImage):
        self.name = name
        self.image: Component2DImage = image
        self.processed_image = process_for_visualisation(self.image)

    def show(self):
        cv2.namedWindow(self.name, cv2.WINDOW_GUI_NORMAL)
        cv2.imshow(self.name, self.processed_image)

    def print_info(self):
        logger.info(f"Resolution:{self.image.width}x{self.image.height}")
        logger.info(f"ImagePixelFormat:{self.image.data_format}")
        logger.info(f"Components per pixel:{self.image.num_components_per_pixel}")
        logger.info(f"Min:{self.image.data.min()}")
        logger.info(f"Max:{self.image.data.max()}")


class RealTimePCLRenderer:
    def __init__(self):
        self.vis = VisualizerWithKeyCallback()
        self.vis.create_window(width=1000, height=800, top=300, left=100)
        self.render_opts = self.vis.get_render_option()
        self.render_opts.point_size = 2.0
        self.render_opts.background_color = np.asarray([0.9, 0.9, 0.9])
        self.vis.register_key_action_callback(glfw.KEY_ESCAPE, self.key_action_callback)
        self.should_close = False

    def key_action_callback(self, vis, key, action):
        self.should_close = True


@dataclass
class OfflineRenderParams:
    background_color: tuple = (1, 1, 1, 1)
    shader: str = "defaultUnlit"
    point_size: float = 2.0
    up_vector: tuple = (0, -1, 0)
    fov: float = 50
    distance_from_camera: float = 0.60
    width: int = 1920
    height: int = 1080


def pcl_offline_render(pcl, filename: str, params=OfflineRenderParams()):
    """
    Renders a point cloud offline and saves it as an image.

    Args:
        pcl (o3d.geometry.PointCloud): The input point cloud.
        filename (str): The output image filename.
        params (OfflineRenderParams, optional): Rendering parameters. Defaults to OfflineRenderParams().
    """
    renderer = o3d.visualization.rendering.OffscreenRenderer(params.width, params.height)
    renderer.scene.set_background(params.background_color)

    mat = o3d.visualization.rendering.MaterialRecord()
    mat.shader, mat.point_size = params.shader, params.point_size

    renderer.scene.add_geometry("pcl", pcl, mat)

    bounds = pcl.get_axis_aligned_bounding_box()
    center, extent = bounds.get_center(), np.linalg.norm(bounds.get_extent())
    eye = center + [0, 0, -params.distance_from_camera * extent]

    renderer.setup_camera(params.fov, center, eye, params.up_vector)
    o3d.io.write_image(filename, renderer.render_to_image())
    logger.debug(f"Saved image as {filename}")
