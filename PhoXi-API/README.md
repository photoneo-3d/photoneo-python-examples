# Photoneo PhoXi API Python examples
![image](https://photoneo.com/files/dw/dw/github/Personal_Linkedin_banner_v4.png)

## Introduction
This repository provides the building blocks necessary for developing your custom Python 
application for working with [Photoneo](https://www.photoneo.com/) devices. You may start your 
development based on one of the examples and modify it to suit your specific needs.

#### Prerequisites
- Python >= 3.10
- Git
- PhoXi Control >= 1.17.0
#### Python packages
```
phoxi-api
numpy
semver
```
or see `pyproject.toml`

### Quick start using `uv`
First download and install **PhoXi Control** application of **version >= 1.17.0** from [Photoneo 
Downloads](https://www.photoneo.com/downloads/phoxi-control)

#### Clone examples repo
```
git clone https://github.com/photoneo-3d/photoneo-python-examples.git
cd photoneo-python-examples/PhoXiAPI
```
Or download whole `PhoXiAPI` directory and place it somewhere in your PC. Following commands then 
launch from within `PhoXiAPI` directory.

#### Install `uv`
```
pip install uv
```
For other installation options please see 
[uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

#### Configure project
```
uv sync
```

#### Run example
Before running an example, please launch `PhoXi Control` application
```
uv run examples/get_device_list.py
uv run examples/get_frame_sw_trigger.py --device_id=<YOUR DEVICE ID>
```

### Support
Visit [www.photoneo.com](https://www.photoneo.com/) for the most up-to-date information and 
documents. If you encounter any issues while using the examples, please do not hesitate to 
contact our dedicated Support team at our [Help Center](https://www.photoneo.com/Help-Center) 
for prompt assistance.

### License
Photoneo examples are distributed under the [MIT License](https://opensource.org/licenses/MIT).