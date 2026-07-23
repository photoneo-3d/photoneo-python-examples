import argparse
import pprint
import sys

import numpy as np
import open3d as o3d
from phoxi_api import PhoXiControl, PhoXiDevice

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--device_id", type=str, help="Device ID", required=True)
    args = arg_parser.parse_args()

    phoxi_control = PhoXiControl()
    if not phoxi_control.is_phoxicontrol_running():
        print("PhoXi Control is not running. Please start PhoXi Control and try again.")
        sys.exit(1)

    with phoxi_control.connect(args.device_id) as device:
        print("Connected device:")
        pprint.pp(device.info())

        # By default, device is NOT logged out from PhoXi Control and acquisition is stopped when
        # device handle is destroyed.
        # This behaviour can be modified by these attributes:
        device.logout_on_exit = True
        device.stop_acquisition_on_exit = True

        if not device.info()["file_camera"]:
            frame_settings_handle = device.frame_settings()
            all_frame_settings = frame_settings_handle.value
            print("Default frame settings:")
            pprint.pprint(all_frame_settings)

            # Disable all frame matrices
            for key in all_frame_settings:
                all_frame_settings[key] = False
            frame_settings_handle.value = all_frame_settings
            print("Disabled frame settings:")
            pprint.pprint(frame_settings_handle.value)

            # Enable selected ones
            frame_settings_handle.PointCloud.value = True
            frame_settings_handle.Texture.value = True
            print("Enabled selected frame settings:")
            pprint.pprint(frame_settings_handle.value)

        # Stop acquisition before changing trigger mode
        if device.is_acquiring():
            device.stop_acquisition()

        # Set trigger mode
        device.set_trigger_mode(PhoXiDevice.TriggerMode.SOFTWARE)
        # Restart acquisition
        device.start_acquisition()

        print()

        # Trigger frame
        # wait_accept - Wait for device to acknowledge this call for frame trigger. If False
        # and if there is currently another trigger waiting this call will raise an
        # exception
        # wait_grabbing_end - Wait until grabbing operation is finished. Useful e.g. when
        # triggering multiple devices
        # on the same scene to prevent cross illumination of the scene
        frame_id = device.trigger_frame(True, True)

        # Get specific frame
        # frame_id - if returned by trigger_frame or -1 to get last available frame
        frame = device.get_frame(frame_id)

        # Check if grabbing was successful, if False expect error in the messages
        if not frame.Info.Successful:
            print("Frame grabbing failed! Messages:")
            pprint.pprint(frame.Info.Messages)
            sys.exit(1)

        # Helper function to convert PhoXiAPI matrices to format expected by Open3D
        def convert_for_o3d(component, normalize: bool = False):
            point_size = component.shape[2]
            flat_component = component.reshape(-1).astype(np.float64)
            vec = np.zeros((flat_component.size // point_size, 3), dtype=component.dtype)
            if point_size == 1:
                vec[:, 0] = flat_component
                vec[:, 1] = flat_component
                vec[:, 2] = flat_component
            elif point_size == 3:
                vec[:, 0] = flat_component[0::3]
                vec[:, 1] = flat_component[1::3]
                vec[:, 2] = flat_component[2::3]
            else:
                ex_msg = "Point size must be 1 or 3"
                raise ValueError(ex_msg)

            if normalize:
                minimum = np.percentile(vec, 5)
                maximum = np.percentile(vec, 95)
                if maximum > minimum:
                    vec = (vec - minimum) / (maximum - minimum)

            return o3d.utility.Vector3dVector(vec)

        # Fill Open3D point cloud object
        point_cloud = o3d.geometry.PointCloud()
        point_cloud.points = convert_for_o3d(frame.PointCloud)
        point_cloud.colors = convert_for_o3d(frame.Texture, normalize=True)

        # Create Open3D visualizer and set point cloud to visualize
        visualizer = o3d.visualization.Visualizer()
        visualizer.create_window()
        visualizer.add_geometry(point_cloud)

        # Rotate camera to correct orientation
        view_control = visualizer.get_view_control()
        view_control.set_front([0, 0, -1])
        view_control.set_up([0, -1, 0])

        visualizer.run()
