import argparse
import pprint
import sys

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
            frame_settings_handle.DepthMap.value = True
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

        for _ in range(5):
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

            print(f"Frame ID: {frame_id}")

            # Check if grabbing was successful, if False expect error in the messages
            print(f"Frame successful: {frame.Successful}")

            # Frame can contain messages from the device like, errors, warnings, etc.
            print("Frame messages:")
            pprint.pprint(frame.Messages)

            # Read frame info
            print("\nInfo:")
            pprint.pprint(frame.Info)

            # Read requested frame matrices
            print("\nPointCloud:")
            pprint.pprint(frame.PointCloud)

            print("\nDepthMap:")
            pprint.pprint(frame.DepthMap)

            print("\nTexture:")
            pprint.pprint(frame.Texture)

            print("----------")
