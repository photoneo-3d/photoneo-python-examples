# Basic examples

This folder contains simple examples that use the harvester api directly and don't use any dependencies for visualization.
This example expects the [Balluf ImpactAcquire GenTL producer](http://static.matrix-vision.com/mvIMPACT_Acquire/).

## Example types

- [list_devices.py](list_devices.py):
  - This script provides an example of how to retrieve a list of connected compatible devices.
- [device_status.py](device_status.py):
  - Retrieves useful information from device. 
- [connect_and_grab.py](connect_and_grab.py):
  - This file demonstrates how to connect to a device and retrieve component information using software trigger while retrieving only one frame.
- [freerun.py](freerun.py):
  - This script demonstrates how to retrieve data continuously with an FPS counter.
- [read_user_set_settings.py](read_user_set_settings.py):
  - Fetches settings available in user sets.
- [read_chunk_data.py](read_chunk_data.py):
  - This script demonstrates how to read data in chunks.
- [read_write_settings.py](read_write_settings.py):
  - This script provides an example of reading and writing settings for a device. It demonstrates different approaches to interact with the device.
- [jumbo_frames_compatibility](jumbo_frames_compatibility.py):
  - Example for printing information about network interfaces with MTU values and attempting to connect to a device to detect potential MTU misconfiguration issues.
- [toggle_jumbo_frames](toggle_jumbo_frames.py):
  - Toggle JumboFrames (MTU 9000).

## Run examples

The examples expect a device's serial number as a single parameter, i.e. to run them:

`python connect_and_grab.py <device_sn>`
