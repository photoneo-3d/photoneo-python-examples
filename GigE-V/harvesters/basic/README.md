# GigE Vision basic examples

Simple examples that use the `harvesters` library directly with no visualisation dependencies. Each script is self-contained and can be run with plain Python.

## Prerequisites

- Firmware >= 1.13.0
- [Balluf ImpactAcquire GenTL producer](http://static.matrix-vision.com/mvIMPACT_Acquire/) installed
- `GENICAM_GENTL64_PATH` environment variable set to the GenTL producer directory
- Python packages: `harvesters`, `genicam-python`

## Running Examples

```bash
python <script>.py <device_serial_number>
```

## Examples

### `list_devices.py`

An example of how to retrieve a list of connected compatible devices: lists all GenTL-discoverable devices without connecting to any of them, printing a formatted table with serial number, model, vendor, display name, and user-defined name.

```bash
python list_devices.py
```

No device serial number required.

---

### `device_status.py`

Retrieves useful information from the device: connects and prints a snapshot of its current configuration:

- Firmware version, model name, and user ID
- All available **components** with their enabled/disabled state and supported pixel formats (active format marked with `*`)
- **Chunk** mode status and enabled state of each chunk
- Current trigger mode and trigger source
- `Scan3dOutputMode` and `CalibrationVolumeOnly`
- For MotionCam-3D: active `OperationMode` with per-mode texture source and coding strategy settings

```bash
python device_status.py <serial>
```

---

### `connect_and_grab.py`

Demonstrates how to connect to a device and retrieve component information using software trigger while retrieving only one frame: restores default settings, configures software trigger, fires one frame, and prints each received component's pixel format, element count, dimensions, and data length. Optionally saves the raw binary data to disk.

```bash
python connect_and_grab.py <serial>
```

---

### `freerun.py`

Demonstrates how to retrieve data continuously with an FPS counter: runs continuous (freerun) acquisition using the Default user set, acquiring 50 frames without explicit triggering, printing a live FPS counter per frame, then reporting the average and peak FPS.

```bash
python freerun.py <serial>
```

---

### `read_user_set_settings.py`

Fetches settings available in user sets: loads the Default user set and iterates every feature listed in `UserSetFeatureSelector`, printing the name and current value of each readable feature.

```bash
python read_user_set_settings.py <serial>
```

Useful for discovering which settings are accessible through user sets on a given device.

---

### `read_chunk_data.py`

This script demonstrates how to read data in chunks: enables `ChunkModeActive`, then enables the `Temperature` and `MainCameraCalibrationData` chunks. After triggering one software-triggered frame, reads:

- `ChunkTemperature` — device temperature (float)
- Camera matrix, distortion coefficients, sensor axis, and sensor position via the `Chunk<Feature>Selector` / `Chunk<Feature>Value` pattern

```bash
python read_chunk_data.py <serial>
```

---

### `read_write_settings.py`

An example of reading and writing settings for a device, demonstrating different approaches to interact with it:

- Direct attribute access: `features.ExposureTime.value`, `features.LaserPower.value`, etc.
- String-based access: `features.get_node("OperationMode").value`
- Iterating a list of feature names to print their values
- Reading a **raw memory register** (`CameraMatrix`) using `struct.unpack` on a little-endian `double[]` buffer
- MotionCam-3D `OperationMode` switching
- Restoring the Default user set after making changes

```bash
python read_write_settings.py <serial>
```

---

### `jumbo_frames_compatibility.py`

Example for printing information about network interfaces with MTU values and attempting to connect to a device to detect potential MTU misconfiguration issues: enumerates all connected network interfaces and their MTU values (Windows via `netsh`, Linux via `ip link`), then attempts to connect to the device with a 3-second retry loop. If the connection fails, reports a hint to check the interface MTU for Jumbo Frames compatibility (MTU 9000 recommended).

```bash
python jumbo_frames_compatibility.py <serial>
```

---

### `toggle_jumbo_frames.py`

Toggle JumboFrames (MTU 9000): sets the `EnableJumboFrames` GenICam feature to enable (MTU 9000) or disable (MTU 1500) Jumbo Frames on the device's network interface.

```bash
python toggle_jumbo_frames.py <serial> --enable
python toggle_jumbo_frames.py <serial> --disable
```

> **Note:** After toggling, the device resets its network interface and becomes temporarily unreachable. Reconnect after a few seconds.
