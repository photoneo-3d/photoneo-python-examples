import sys
from pathlib import Path

from genicam.genapi import NodeMap
from harvesters.core import Harvester

from common import (CONNECTION_SETTINGS, console, cti_file_path,
                    enable_components, enabled_components,
                    get_component_statuses, sorted_components)


def main(device_sn: str):
    with Harvester() as h:
        h.add_file(str(cti_file_path), check_existence=True, check_validity=True)
        h.update()

        console.print(f"[bold]Connecting to: {device_sn}")
        with h.create({"serial_number": device_sn}, config=CONNECTION_SETTINGS) as ia:
            features: NodeMap = ia.remote_device.node_map

            # Enable software trigger mode
            features.TriggerSelector.value = "FrameStart"
            features.TriggerMode.value = "On"
            features.TriggerSource.value = "Software"

            if features.IsMotionCam3D_Val.value:
                features.OperationMode.value = "Camera"

            # To get Normals we need to enable this value
            features.NormalsEstimationRadius.value = 2

            enable_components(features, sorted_components(features))
            console.print(get_component_statuses(features))

            console.print("[green]Start Acquisition")
            ia.start()
            features.TriggerSoftware.execute()
            enabled_comps: list = enabled_components(features)
            with ia.fetch(timeout=10) as buff:
                # match the components based on their order
                for name, part in zip(enabled_comps, buff.payload.components):
                    console.print(
                        f"[yellow]Component {name}:[/yellow]\n"
                        f"DataFormat: {part.data_format}\n"
                        f"Width: {part.width}\n"
                        f"Height: {part.height}\n"
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
