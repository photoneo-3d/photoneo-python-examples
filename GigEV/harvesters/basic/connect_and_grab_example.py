import sys
from pathlib import Path

from genicam.genapi import NodeMap
from harvesters.core import Harvester

from common import CONNECTION_SETTINGS, cti_file_path

FRAME_COUNT = 3


def main(device_sn: str):
    with Harvester() as h:
        print("Load .cti file...")
        h.add_file(str(cti_file_path), check_existence=True, check_validity=True)
        h.update()

        print(f"Connecting to: {device_sn}")
        with h.create({"serial_number": device_sn}, config=CONNECTION_SETTINGS) as ia:
            features: NodeMap = ia.remote_device.node_map

            # "FrameStart" is the only supported trigger currently, so the following line could
            # be skipped, but it's safer to set it in case more triggers are added in the future.
            features.TriggerSelector.value = "FrameStart"
            features.TriggerMode.value = "On"
            features.TriggerSource.value = "Software"

            ia.start()
            for i in range(FRAME_COUNT):
                features.TriggerSoftware.execute()
                with ia.fetch(timeout=10) as buff:
                    print(f"Frame ID: {i}")
                    components = buff.payload.components
                    for component in components:
                        print(
                            f"Component: {components.index(component)}\n"
                            f"DataFormat: {component.data_format}\n"
                            f"Width: {component.width}\n"
                            f"Height: {component.height}\n"
                        )


if __name__ == "__main__":
    try:
        device_id = sys.argv[1]
    except IndexError:
        print(
            f"Error: no device given, please run it with the device serial number as argument:"
        )
        print(f"    {Path(__file__).name} <device serial>")
        sys.exit(1)
    main(device_id)
