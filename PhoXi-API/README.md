# Photoneo PhoXi API Python examples

## Introduction

Examples for working with Photoneo 3D sensors through the **PhoXi API** Python wrapper (`phoxi-api`), which communicates with the locally running PhoXi Control application.

## Prerequisites

- **PhoXi Control >= 1.17.0** installed and running (download from [Photoneo Downloads](https://www.photoneo.com/downloads/phoxi-control))
- `PHOXI_CONTROL_PATH` environment variable pointing to the PhoXi Control installation directory
- Python >= 3.10
- `uv` package manager (`pip install uv`)

## Quick Start

```bash
cd PhoXi-API
uv sync
uv run examples/get_device_list.py
uv run examples/get_frame_sw_trigger.py --device_id=<YOUR_DEVICE_ID>
```

## Examples

### `get_device_list.py`

Lists all devices currently known to PhoXi Control (both connected and file cameras).

```bash
uv run examples/get_device_list.py
```

By default uses the cached device list. The `refresh=True` flag triggers a new network discovery scan, which takes a few seconds.

---

### `get_frame_freerun.py`

Demonstrates continuous (freerun) acquisition. Configures the device to enable PointCloud, DepthMap and Texture frame matrices, switches to `FREERUN` trigger mode, then acquires and prints 5 consecutive frames without explicit triggering.

```bash
uv run examples/get_frame_freerun.py --device_id=<YOUR_DEVICE_ID>
```

Shows how to inspect `frame.Info`, `frame.PointCloud`, `frame.DepthMap`, and `frame.Texture`.

---

### `get_frame_sw_trigger.py`

Demonstrates software-triggered acquisition. Enables PointCloud, DepthMap, and Texture, sets `SOFTWARE` trigger mode, then loops 5 times: trigger → wait for acknowledgement and grabbing end → retrieve frame by ID → print matrices.

```bash
uv run examples/get_frame_sw_trigger.py --device_id=<YOUR_DEVICE_ID>
```

Illustrates the `trigger_frame(wait_accept, wait_grabbing_end)` and `get_frame(frame_id)` workflow, and the use of `logout_on_exit` / `stop_acquisition_on_exit` connection options.

---

### `get_frame_sw_trigger_visual.py`

Captures a single software-triggered frame and renders it as a coloured 3D point cloud in an **Open3D** viewer. Texture is mapped as colour (percentile-normalised to `[0, 1]`). Camera orientation is set to the standard sensor coordinate system.

```bash
uv run examples/get_frame_sw_trigger_visual.py --device_id=<YOUR_DEVICE_ID>
```

Requires `open3d`. Shows how to convert PhoXi API matrix arrays to `o3d.utility.Vector3dVector`.

---

### `get_and_set_settings.py`

Comprehensive reference for the settings API. Demonstrates:

- **Attribute access** — `settings.CapturingSettings.LaserPower.value`
- **Availability checks** — `.can_get()`, `.can_set()`
- **Value constraints** — `.min()`, `.max()`, `.enum()`, `.type()`
- **Safe access** — `.get(default=)`, `.set()` (returns `bool`, never raises)
- **Bulk read/write** — `device.get_settings([...])` / `device.set_settings({...})`
- **Direct access mode** — GUI-path names with spaces replaced by `__` (e.g. `General__Settings.LED__Power`)
- Error handling when accessing unavailable settings

```bash
uv run examples/get_and_set_settings.py --device_id=<YOUR_DEVICE_ID>
```

Requires a physical device (not a file camera).

---

### `maintenance_tool_api_example.py`

Demonstrates the `MaintenanceTool` API workflow used for device calibration maintenance:

1. Checks API/PhoXi Control version compatibility
2. Connects to a device by serial number
3. Runs `adjust_power()` (laser power optimisation)
4. Interactively triggers scans and reports acquired frame count and recognised marker point count
5. Calls `analyze()` to compute a correction patch and optionally applies it with `patch()`

```bash
uv run examples/maintenance_tool_api_example.py                  # shows expected connection failures
uv run examples/maintenance_tool_api_example.py <SERIAL_NUMBER>  # full interactive workflow
```

---

### `read_praw_file.py`

Opens a single `.praw` or `.pmraw` file and prints its contents without a live device:

- Device metadata from the file header (device name, variant, firmware, serial, PhoXi Control version)
- List of all scan settings stored in the file
- List of all data matrices stored in the file
- Value of the first setting
- Shape, dtype, min, and max of the first matrix (as a numpy array)

```bash
uv run examples/read_praw_file.py <path/to/file.praw>
uv run examples/read_praw_file.py <path/to/file.pmraw> --frame 2   # select frame in multi-frame file
```

---

### `read_praw_texture.py`

Reads the `Texture` matrix from a `.praw` or `.pmraw` file and normalises it to a displayable `uint8` image using the same **Auto Intensity** algorithm as PhoXi Control (percentile-based clipping at the configurable tail percentage, works for both grayscale `uint16` and 3-channel RGB).

```bash
uv run examples/read_praw_texture.py <path>
uv run examples/read_praw_texture.py <path> --out texture.png          # save PNG (requires Pillow)
uv run examples/read_praw_texture.py <path> --percentile 1.0           # tighter clipping
uv run examples/read_praw_texture.py <path> --frame 3                  # PMRAW frame index
```

Uses `phoxi_api.normalize_texture()`. PNG saving requires `pip install Pillow`.

---

### `read_praw_two_files.py`

Opens two `.praw` or `.pmraw` files simultaneously and compares their common matrices:

- Prints device metadata and matrix lists for both files
- For **PointCloud**: filters out invalid (0, 0, 0) points and reports per-point Euclidean distance statistics (mean, median, max, p95, p99) plus a text histogram of the distance distribution
- For all other matrices: reports max and mean absolute element-wise difference

```bash
uv run examples/read_praw_two_files.py <path1> <path2>
```

Useful for comparing scans of the same scene (e.g. before/after a settings change or calibration update).

## MaintenanceTool robot-controlled calibration
Drives a `MaintenanceTool` calibration session from a robot controller over the network: a TCP
server (`robot_controlled_server.py`) runs on this PC and owns the `MaintenanceTool` session,
while a robot controller (e.g. `ur_client_example.script`) or the included
`localhost_client_simulator.py` acts as the TCP client. See
[`examples/maintenance_tool_robot_calibration/README.md`](examples/maintenance_tool_robot_calibration/README.md)
for the full protocol and setup steps.

## Support

Visit [www.photoneo.com](https://www.photoneo.com/) for the most up-to-date information and documents. If you encounter any issues while using the examples, please do not hesitate to contact our dedicated Support team at our [Help Center](https://www.photoneo.com/Help-Center) for prompt assistance.

## License

Photoneo examples are distributed under the [MIT License](https://opensource.org/licenses/MIT)
