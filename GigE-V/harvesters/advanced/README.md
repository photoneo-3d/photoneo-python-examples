# GigE Vision advanced examples

More elaborate examples that use Open3D and OpenCV for 3D visualisation and image display. All examples use the `photoneo_genicam` helper package located in this directory.

## Prerequisites

- Firmware >= 1.13.0 (some examples require >= 1.14.0, noted per example)
- [Balluf ImpactAcquire GenTL producer](http://static.matrix-vision.com/mvIMPACT_Acquire/) installed
- `GENICAM_GENTL64_PATH` environment variable set to the GenTL producer directory
- Python packages: `harvesters`, `genicam-python`, `open3d`, `opencv-python`, `numpy`
- `ycocg_color_convert.py` additionally requires `numba`

## Running Examples

```bash
python <script>.py <device_serial_number>
```

## `photoneo_genicam` Package

Shared helpers used by all advanced examples:

| Module | Purpose |
|---|---|
| `components.py` | Enable/disable components, query enabled state and pixel formats |
| `chunks.py` | Parse chunk selector data, extract 4×4 transformation matrices |
| `pointcloud.py` | Build `Vector3dVector` from raw data, map texture as colours, pre-fetch coordinate maps, reconstruct PCL from ProjectedC depth map |
| `textures.py` | Per-device texture configuration presets |
| `features.py` | Enable software/hardware trigger, `Presenter` helper for feature demonstrations |
| `user_set.py` | Load Default user set |
| `visualizer.py` | Static Open3D render, real-time PCL renderer, texture image save, `process_for_visualisation` |
| `utils.py` | Logger, `data_stream_reset`, `version_check`, `detect_device_type`, `measure_time` |
| `camera_features.py` | Feature parameter classes (ISO, HDR, ProjectionOffset) for `feature_presenter.py` |

## Examples

### `connect_grab_save.py`

Connects, enables one or more requested components, triggers one software-triggered frame, and saves each component to disk. Intensity and ColorCamera are saved as PNG (handling Mono10, Mono12, Mono16, and RGB8 pixel formats); all other components are saved as raw `.dat` files.

```bash
python connect_grab_save.py <serial> Range
python connect_grab_save.py <serial> Intensity Range Confidence
```

---

### `pointcloud.py`

Captures a single `CalibratedABC_Grid` point cloud (Range component), creates an Open3D `PointCloud`, saves it as `pointcloud.ply`, and renders it in a static 3D viewer.

```bash
python pointcloud.py <serial>
```

---

### `pointcloud_with_normals_and_texture.py`

Enables Intensity, Range, and Normal components. Builds a textured point cloud with per-point normals and renders it statically with Open3D.

```bash
python pointcloud_with_normals_and_texture.py <serial>
```

---

### `pointcloud_with_marker_space.py`

Enables marker recognition and sets `CoordinateSpace = MarkerSpace`. Reads the `CurrentCameraToCoordinateSpaceTransformation` chunk from the frame buffer to obtain the 4×4 transformation matrix, applies it to the point cloud, and renders the result in marker space with texture colour mapping.

> If no marker is detected in the scene the fetch times out.

```bash
python pointcloud_with_marker_space.py <serial>
```

---

### `pointcloud_with_projectedC.py`

Demonstrates client-side point cloud reconstruction from depth data. Pre-fetches the static `CoordinateMapA` / `CoordinateMapB` grids once (these only change when settings change). Then runs a **real-time acquisition loop** in `ProjectedC` output mode, reconstructing full XYZ point clouds from each depth frame on the client, and updating the Open3D viewer live with FPS display.

```bash
python pointcloud_with_projectedC.py <serial>
```

---

### `pointcloud_with_projectedC_color.py`

Like `pointcloud_with_projectedC.py` but adds colour texture from the color camera (`CameraSpace = ColorCamera`, `TextureSource = Color`). Reconstructs XYZ from `ProjectedC` depth, maps colour texture, and renders the coloured point cloud. On Linux the result is saved as `PointCloudWithColorMapped.png` instead of an interactive window.

Requires MotionCam-3D or PhoXi 3D Scanner Gen3.

```bash
python pointcloud_with_projectedC_color.py <serial>
```

---

### `show_confidence_map.py`

Enables the Range (ProjectedC) and Confidence components, triggers one frame, and displays both the depth map and confidence map side-by-side in OpenCV windows. Press **ESC** or close either window to exit.

```bash
python show_confidence_map.py <serial>
```

---

### `show_textures.py`

Iterates all texture configurations relevant to the detected device type (defined in `photoneo_genicam/textures.py`). For each configuration, applies the settings, captures one frame, and saves the Intensity component as a PNG. Useful for comparing texture sources (Laser, LED, Color, etc.) and pixel formats side by side.

```bash
python show_textures.py <serial>
```

---

### `user_sets.py`

Demonstrates the full **user set** save/load lifecycle:

1. Changes several settings (TextureSource, ExposureTime, LEDPower, ShutterMultiplier, NormalsEstimationRadius, CalibrationVolumeOnly)
2. Saves them to `UserSet1`
3. Loads the Default profile (restoring factory values)
4. Reloads `UserSet1` to verify persistence

Prints setting values at each step.

```bash
python user_sets.py <serial>
```

---

### `hw_trigger.py`

Configures hardware trigger (`TriggerSource = Line1`) and waits up to 180 seconds for an external electrical signal on the trigger input. Logs each received component when a frame arrives.

```bash
python hw_trigger.py <serial>
```

---

### `roi_mode.py`

Demonstrates **Color Settings ROI** mode (requires firmware >= 1.14.0). Captures two frames of the Intensity component using `CameraSpace = ColorCamera`:

1. Full resolution (`roi_off.png`)
2. A predefined 300×300 pixel ROI (`roi_on.png`)

Logs image dimensions and transfer size for each capture.

```bash
python roi_mode.py <serial>
```

---

### `ptp_timestamp.py`

Connects to **two devices** sequentially, enables PTP on each, and acquires 5 software-triggered frames from each device. For every frame, prints the acquisition timestamp (converted from nanoseconds to UTC datetime), the PTP port state, and the grandmaster clock identity.

```bash
python ptp_timestamp.py <serial1> <serial2>
```

Both devices must be on the same network and running the same PTP grandmaster.

---

### `feature_presenter.py`

Applies a series of pre-defined feature combinations (baseline, ProjectionOffset, ISO, HDR) to the Intensity component, captures one texture frame for each, and saves all results as PNG files for visual comparison.

```bash
python feature_presenter.py <serial>
```

Modify the `FEATURES_TO_PRESENT` list in the script to explore other feature combinations.

---

### `ycocg_color_convert.py`

Captures the ColorCamera component in `Mono16` pixel format (YCoCg-encoded color) and decodes it to 10-bit RGB using a Numba-JIT compiled converter. Displays both the raw YCoCg image and the decoded RGB image in OpenCV windows side by side. Press **ESC** to exit.

Requires MotionCam-3D or PhoXi 3D Scanner Gen3. Requires `numba`.

```bash
python ycocg_color_convert.py <serial>
```

---

### `marker_dot_correction.py`

Full **Marker Dot Correction** workflow using GenICam feature-based chunk access:

1. Sets `MarkerDotCorrection_Mode = ReferenceRecording`, triggers a reference frame, and reads 2D reference dot positions via `ChunkMarkerDotCorrection_ReferenceMarkers2dIndex`
2. Sets mode to `Active`, triggers a corrected frame, reads observed dot positions
3. Computes per-dot displacement (in pixels) between observed and reference positions
4. Prints the original and corrected `CurrentCameraToCoordinateSpaceTransformation` matrices

```bash
python marker_dot_correction.py <serial>
```

---

### `marker_dot_correction_registers.py`

Same Marker Dot Correction workflow as above, but reads marker dot coordinates and transformation matrices directly from **raw memory registers** using `numpy.frombuffer` rather than the per-index feature accessor pattern. Demonstrates an alternative, lower-level approach to parsing chunk data.

```bash
python marker_dot_correction_registers.py <serial>
```
