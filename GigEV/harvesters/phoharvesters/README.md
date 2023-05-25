# Phoharvesters

This folder contains more elaborate examples that show more advanced use or use opencv and 
`open3d` to visualize received textures and pointcloud. 
This example expects the `MATRIX VISION` GenTL Producer.

## Install requirements

Create a virtual environment and install the dependencies:

```
python3.9 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

## Example types

- `fetch_components_example.py` - Using software trigger fetch all available components and print out the data types.
- `show_pointcloud_example.py` - Calculate and render `PointCloud` from `DepthMap` and from `ReprojectionMap`.
- `show_texture_example.py` - Show available textures.
- `hw_trigger_example.py` - Simple example where we wait for hardware trigger signal and export the image.

## Run examples

The examples expect a device's serial number as a single parameter, i.e. to run them:

`python phoharvesters/fetch_components_example.py <device_sn>`