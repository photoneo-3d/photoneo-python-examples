# Harvester examples

We provide 2 sets of examples to cover specific use cases.

## Basic examples
The `basic` folder contains examples that show simple usage of the harvesters API with Photoneo devices without any additional dependencies.


## Advanced examples
The `advanced` folder contains more elaborate examples with visualization.

## Python requirements
Create a virtual environment and install the dependencies:

```
python3.9 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install -r ./basic/requirements.txt # or folder advanced
```

## Installing a GenTL Producer
To use Harvesters, you need a compatible GenTL producer. A list of GenTL producers that work with Harvesters is available at [this link](https://github.com/genicam/harvesters/wiki#gentl-producers).

**Recommended Producer:** We recommend using the `Balluf ImpactAcquire` GenTL producer. The version currently tested is `3.0.3`, which can be downloaded from [here](https://static.matrix-vision.com/mvIMPACT_Acquire/3.0.3/).

**Environment Variable:** Regardless of whether you are using Windows or Linux, you need to set the `GENICAM_GENTL64_PATH` environment variable correctly.

### Windows Installation

1. Download and install the package using the [ImpactAcquire-x86_64-3.0.3.exe](https://static.matrix-vision.com/mvIMPACT_Acquire/3.0.3/ImpactAcquire-x86_64-3.0.3.exe) executable.
2. The installer sets the `GENICAM_GENTL64_PATH` environment variable to `C:\Program Files\Balluff\ImpactAcquire\bin\x64\` by default.
3. Make sure the `mvGenTLProducer.cti` file is accessible, as it is essential for proper functioning.
4. On Windows, it's important to disable the `GigE Vision NDIS 6.x Filter Driver`.

![Disable Capture Driver on Windows](./gigev_capture_driver_disable.png?raw=true)

### Linux Installation

1. Download the installer script `install_ImpactAcquire.sh` and the archive file `ImpactAcquire-x86_64_ABI2-3.0.3.tgz` from [here](https://static.matrix-vision.com/mvIMPACT_Acquire/3.0.3/)
2. Change the permissions of the installer script to make it executable: `chmod a+x install_ImpactAcquire.sh`. After installation, relog into your system for the changes to take effect.
3. The installer sets the `GENICAM_GENTL64_PATH` environment variable to `/opt/ImpactAcquire/lib/x86_64` by default.
4. Make sure the `libmvGenTLProducer.so` file is accessible, as it is essential for proper functioning.

All the examples were tested and work with the `MATRIX VISION` producer. 
To use a different producer, change the `GenTL_file` variable in `common.py`.