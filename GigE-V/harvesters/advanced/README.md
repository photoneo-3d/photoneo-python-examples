# Advanced

This folder contains more elaborate examples that show more advanced use or use [OpenCV](https://opencv.org/) and 
[Open3D](https://www.open3d.org/) to visualize received textures and point cloud. 
This example expects the [Balluf ImpactAcquire GenTL producer](http://static.matrix-vision.com/mvIMPACT_Acquire/).

## Example types

- [connect_grab_save.py](connect_grab_save.py):  
  - This file demonstrates how to connect to a device and retrieve component information using software trigger while retrieving only one frame. Additionally, it saves the component as an image.
- [pointcloud.py](pointcloud.py):  
  - Example for visualizing point cloud data.
- [pointcloud_with_marker_space.py](pointcloud_with_marker_space.py):  
  - Example for visualizing point cloud, transformed into marker space.
- [pointcloud_with_projectedC.py](pointcloud_with_projectedC.py):  
  - Example for visualizing point cloud in real time, which is calculated from ProjectedC component locally. Using continuous acquisition mode.
- [pointcloud_with_normals_and_texture.py](pointcloud_with_normals_and_texture.py):  
  - Example for visualizing point cloud data including normal maps and texture information.
- [show_confidence_map.py](show_confidence_map.py):  
  - Python script for displaying confidence map with depth map.
- [show_textures.py](show_textures.py):  
  - Script for displaying all available textures, in different pixel formats.
- [user_sets.py](user_sets.py):  
  - Python script for managing user sets.
- [ycocg_color_convert.py](ycocg_color_convert.py):  
  - Script for YCoCg color conversion.
- [hw_trigger.py](hw_trigger.py):  
  - Script to demonstrate hardware trigger mode.

## Run examples

The examples expect a device's serial number as a single parameter, i.e. to run them:

`python pointcloud.py <device_sn>`
