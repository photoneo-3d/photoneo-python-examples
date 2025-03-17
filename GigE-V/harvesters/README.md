# Harvester examples

We provide 2 sets of examples to cover specific use cases.

## Basic examples
The `basic` folder contains examples that show simple usage of the harvesters API with Photoneo devices without any additional dependencies.

## Advanced examples
The `advanced` folder contains more elaborate examples with visualization.

## Python requirements
Create a virtual environment and install the dependencies:

```
python3.11 -m venv .venv
source .venv/bin/activate # on Linux
# On windows: source .venv/Scripts/activate
python3 -m pip install --upgrade pip
pip install -r ./basic/requirements.txt # or folder advanced
```

## Installing a GenTL Producer
To use Harvesters, you need a compatible GenTL producer. A list of GenTL producers that work with Harvesters is available at [this link](https://github.com/genicam/harvesters/wiki#gentl-producers).

**Recommended Producer:** We recommend using the `MATRIX VISION ImpactAcquire` GenTL producer. The version currently tested is `2.49.0`, which can be downloaded from [here](https://static.matrix-vision.com/mvIMPACT_Acquire/2.49.0/).

**Environment Variable:** Regardless of whether you are using Windows or Linux, you need to set the `GENICAM_GENTL64_PATH` environment variable correctly.

### Troubleshooting

If you followed all the steps in this README but still encounter a `TimeoutException`, explicitly enabling the `PacketResend` functionality could help:

Add this line after connecting to the device:
```python
ia.data_streams[0].node_map.mvResendActive.value = True
```

This is a specific setting for `mvGenTLProducer` and may change in the future.

### Windows Installation

1. Download and install the package using the [mvGenTL_Acquire-x86_64-2.49.0.exe](https://static.matrix-vision.com/mvIMPACT_Acquire/2.49.0/mvGenTL_Acquire-x86_64-2.49.0.exe) executable.
2. The installer sets the `GENICAM_GENTL64_PATH` environment variable to `C:\Program Files\MATRIX VISION\mvIMPACT Acquire\bin\x64\` by default.
3. Make sure the `mvGenTLProducer.cti` file is accessible, as it is essential for proper functioning.
4. On Windows, it's important to disable the `GigE Vision NDIS 6.x Filter Driver`.
5. Setup firewall rules to allow unsolicited incoming UDP traffic from the device IP address.

![Disable Capture Driver on Windows](./gigev_capture_driver_disable.png?raw=true)

### Linux Installation

1. Download the installer script `install_mvGenTL_Acquire.sh` and the archive file `mvGenTL_Acquire-x86_64_ABI2-2.49.0.tgz` from [here](https://static.matrix-vision.com/mvIMPACT_Acquire/2.49.0/mvGenTL_Acquire-x86_64_ABI2-2.49.0.tgz)
2. Change the permissions of the installer script to make it executable: `chmod a+x install_mvGenTL_Acquire.sh`. After installation, relog into your system for the changes to take effect.
3. The installer sets the `GENICAM_GENTL64_PATH` environment variable to `/opt/mvIMPACT_Acquire/lib/x86_64` by default.
4. Make sure the `libmvGenTLProducer.so` file is accessible, as it is essential for proper functioning.

All the examples were tested and work with the `MATRIX VISION` producer. 
To use a different producer, change the `GenTL_file` variable in `common.py`.