# Photoneo Python examples
![image](https://photoneo.com/files/dw/dw/github/Personal_Linkedin_banner_v4.png)

## Introduction

This repository provides building blocks for developing custom Python applications for [Photoneo](https://www.photoneo.com/) 3D sensors. Two independent integration paths are available depending on which interface you want to use.

## [PhoXi-API](PhoXi-API/README.md)

Python examples using the **`phoxi-api`** package — a high-level Python wrapper for the PhoXi Control application. This is the recommended starting point for most use cases.

**What you will find:**
- Listing available devices
- Freerun and software-triggered frame acquisition
- Interactive point cloud visualisation with Open3D
- Reading and writing device settings via attribute-style and path-based APIs
- Reading offline scan files (`.praw` / `.pmraw`): metadata, matrices, texture normalisation, and two-file comparison
- MaintenanceTool API for laser power calibration and correction patching, including a robot-controlled variant (TCP server/client, with a Universal Robots example client)

**Requirements:** PhoXi Control >= 1.17.0 must be installed and running. Uses `uv` as the package manager.

→ [PhoXi-API examples and quick start](PhoXi-API/README.md)

---

## [GigE-V](GigE-V/README.md)

Python examples using the **GigE Vision / GenICam** protocol directly via the `harvesters` library and a GenTL producer. This path gives low-level access to the device without PhoXi Control.

**Requirements:** Balluf ImpactAcquire GenTL producer and the `GENICAM_GENTL64_PATH` environment variable. Firmware >= 1.13.0.

### [Basic examples](GigE-V/harvesters/basic/README.md)

Straightforward scripts with no visualisation dependencies. Good starting point for understanding the GenICam feature and component model.

**What you will find:**
- Device discovery and status inspection (components, chunks, trigger mode)
- Single-frame grab with software trigger
- Continuous freerun acquisition with FPS measurement
- Reading and writing GenICam features including raw memory registers
- Reading chunk data (temperature, calibration matrix, distortion coefficients)
- User set save/load
- Network diagnostics and Jumbo Frames configuration

→ [Basic examples](GigE-V/harvesters/basic/README.md)

### [Advanced examples](GigE-V/harvesters/advanced/README.md)

More elaborate examples using Open3D and OpenCV. Include a shared `photoneo_genicam` helper package for components, chunks, point cloud assembly, and visualisation.

**What you will find:**
- Point cloud capture, visualisation, and PLY export
- Point cloud with normals and texture colour mapping
- Coordinate space transformation into marker space via chunk data
- Real-time point cloud streaming in ProjectedC mode (client-side XYZ reconstruction from depth maps)
- Coloured point cloud using color camera texture
- Confidence map and depth map display
- All texture sources captured and saved for comparison
- Hardware trigger and hardware-synchronised multi-device PTP timestamps
- Color settings ROI mode
- YCoCg color decoding (Numba JIT)
- User set management
- Marker Dot Correction workflow (feature-accessor and raw-register approaches)
- Feature effect demonstration (ISO, HDR, ProjectionOffset)

→ [Advanced examples](GigE-V/harvesters/advanced/README.md)

### [Network utilities](GigE-V/utils/README.md)

A standalone, dependency-free Python implementation of the GigE Vision **discovery** and **FORCEIP** commands for listing devices on the network and temporarily changing their IP configuration.

→ [Network utilities](GigE-V/utils/README.md)

---

## Support

Visit [www.photoneo.com](https://www.photoneo.com/) for the most up-to-date documentation. For issues with these examples contact the Photoneo Support team at the [Help Center](https://www.photoneo.com/Help-Center).

## License

Photoneo examples are distributed under the [BSD License](https://github.com/photoneo-3d/photoneo-python-examples/blob/main/LICENSE).
