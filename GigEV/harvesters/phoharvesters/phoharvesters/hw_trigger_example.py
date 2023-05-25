import sys
from pathlib import Path

import cv2
from genicam.genapi import NodeMap
from harvesters.core import Component2DImage, Harvester

from common import (CONNECTION_SETTINGS, console, cti_file_path,
                    get_opencv_image, enable_components, INTENSITY)


def main(device_sn: str):
    with Harvester() as h:
        h.add_file(str(cti_file_path), check_existence=True, check_validity=True)
        h.update()

        console.print(f"[bold]Connecting to: {device_sn}")
        with h.create({"serial_number": device_sn}, config=CONNECTION_SETTINGS) as ia:
            features: NodeMap = ia.remote_device.node_map

            console.print(f"[green]Enable HW Trigger")
            features.TriggerSelector.value = "FrameStart"
            features.TriggerMode.value = "On"
            features.TriggerSource.value = "Line1"

            enable_components(features, [INTENSITY])

            if features.IsMotionCam3D_Val.value:
                features.OutputTopology.value = "RegularGrid"

            ia.start()
            timeout = 180
            console.print(f"[yellow]Wait {timeout}s for hw-trigger signal...")
            with ia.fetch(timeout=timeout) as buff:
                intensity_tex: Component2DImage = buff.payload.components[0]
                intensity_img = get_opencv_image(intensity_tex)

                cv2.namedWindow("Intensity", cv2.WINDOW_NORMAL)
                cv2.imshow("Intensity", intensity_img)

                # wait until a key was pressed in the opencv window
                while cv2.waitKey(100) == -1:
                    # or the windows were closed
                    if cv2.getWindowProperty("Intensity", cv2.WND_PROP_VISIBLE) < 1:
                        break


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
