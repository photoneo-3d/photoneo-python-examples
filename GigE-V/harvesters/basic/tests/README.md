# Test Examples

These tests iterate through `basic` tests and execute them one by one.  
A test passes if no errors occur during runtime.  
Most tests require a `device_sn` parameter, so be sure to update the variable before running them.

You can also check the logs (`stdout` / logger output) for additional details in `outputs` folder.

## Running the tests

```sh
pytest -vs . --device <DEVICE-SN>
```

## Example output
```sh
test_examples.py::test_example[/home/rtoth/GIT/PhotoneoMain_REPO/PhoXi/GigevTransport/examples/harvesters/basic/read_user_set_settings.py] PASSED
test_examples.py::test_example[/home/rtoth/GIT/PhotoneoMain_REPO/PhoXi/GigevTransport/examples/harvesters/basic/jumbo_frames_compatibility.py] PASSED
test_examples.py::test_example[/home/rtoth/GIT/PhotoneoMain_REPO/PhoXi/GigevTransport/examples/harvesters/basic/read_write_settings.py] PASSED
test_examples.py::test_example[/home/rtoth/GIT/PhotoneoMain_REPO/PhoXi/GigevTransport/examples/harvesters/basic/connect_and_grab.py] PASSED
test_examples.py::test_example[/home/rtoth/GIT/PhotoneoMain_REPO/PhoXi/GigevTransport/examples/harvesters/basic/freerun.py] PASSED
test_examples.py::test_example[/home/rtoth/GIT/PhotoneoMain_REPO/PhoXi/GigevTransport/examples/harvesters/basic/device_status.py] PASSED
test_examples.py::test_example[/home/rtoth/GIT/PhotoneoMain_REPO/PhoXi/GigevTransport/examples/harvesters/basic/gentl_producer_loader.py] PASSED
test_examples.py::test_example[/home/rtoth/GIT/PhotoneoMain_REPO/PhoXi/GigevTransport/examples/harvesters/basic/utils.py] PASSED
test_examples.py::test_example[/home/rtoth/GIT/PhotoneoMain_REPO/PhoXi/GigevTransport/examples/harvesters/basic/read_chunk_data.py] PASSED
test_examples.py::test_example[/home/rtoth/GIT/PhotoneoMain_REPO/PhoXi/GigevTransport/examples/harvesters/basic/list_devices.py] PASSED
test_examples.py::test_example[/home/rtoth/GIT/PhotoneoMain_REPO/PhoXi/GigevTransport/examples/harvesters/basic/__init__.py] PASSED
============================================================================= 11 passed in 31.04s =============================================================================
```