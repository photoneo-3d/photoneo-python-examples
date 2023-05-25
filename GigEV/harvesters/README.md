# Harvester examples

We provide 2 sets of examples to cover specific use cases.


## Basic examples
The `basic` folder contains examples that show simple usage of the harvesters API with Photoneo devices without any additional dependencies.


## Phoharvesters
The `phoharvesters` folder contains more elaborate examples with visualization.


## Installing GenTL Producer
A list of GenTL producers compatible with Harvesters can be found at: 
https://github.com/genicam/harvesters/wiki#gentl-producers.

Install the producer properly (might require re-login or restart to have proper `GENICAM_GENTL64_PATH` value),
or point `GENICAM_GENTL64_PATH` to the lib/x86_64 subfolder of where you unpacked it.

If you choose `mvGenTL Acquire` you can follow installation guide at:
https://www.matrix-vision.com/manuals/mvBlueFOX/mvBF_quickstart_software.html

```
wget http://static.matrix-vision.com/mvIMPACT_Acquire/2.49.0/mvGenTL_Acquire-x86_64_ABI2-2.49.0.tgz
wget http://static.matrix-vision.com/mvIMPACT_Acquire/2.49.0/install_mvGenTL_Acquire.sh

chmod a+x install_mvGenTL_Acquire.sh
./install_mvGenTL_Acquire.sh --gev_support --unattended --minimal
```

All the examples were tested and work with the `MATRIX VISION` producer. 
To use a different producer, change the `GenTL_file` variable in `common.py`.