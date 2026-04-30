import argparse
import pprint
import sys

from phoxi_api import PhoXiControl, PhoXiError

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser("get_and_set_settings")
    arg_parser.add_argument("--device_id", type=str, help="Device ID", required=True)
    args = arg_parser.parse_args()

    phoxi_control = PhoXiControl()
    if not phoxi_control.is_phoxicontrol_running():
        print("PhoXi Control is not running. Please start PhoXi Control and try again.")
        exit(1)

    with phoxi_control.connect(args.device_id) as device:
        # By default, device is NOT logged out from PhoXi Control and acquisition is stopped when
        # device handle is destroyed.
        # This behaviour can be modified by these attributes:
        device.logout_on_exit = True
        device.stop_acquisition_on_exit = True

        if device.info()["file_camera"]:
            print("Use physical device to run this example, file camera settings can not be set!")
            sys.exit(1)

        print("Connected device:")
        pprint.pp(device.info())

        print("")

        # Get settings handle
        settings_handle = device.settings()

        # Read single setting
        print(f"LaserPower: {settings_handle.CapturingSettings.LaserPower.value}")
        # Set single setting
        settings_handle.CapturingSettings.LaserPower.value = 1024
        print(f"LaserPower - after change: {settings_handle.CapturingSettings.LaserPower.value}")

        print("")

        # Check setting availability
        print(
            f"LaserPower is "
            f"{'' if settings_handle.CapturingSettings.LaserPower.can_get() else 'not'} gettable"
        )
        print(
            f"LaserPower is "
            f"{'' if settings_handle.CapturingSettings.LaserPower.can_set() else 'not'} settable"
        )
        print(f"FooBar is {'' if settings_handle.FooBar.can_get() else 'not'} gettable")
        print(f"FooBar is {'' if settings_handle.FooBar.can_set() else 'not'} settable")

        print("")

        # Reading or setting not available settings via value attribute raises an exception
        try:
            print(f"FooBar value: {settings_handle.FooBar.value}")
        except PhoXiError as e:
            print(f"Exception: {e}")
        # Setting not available setting raises an exception
        try:
            settings_handle.FooBar.value = "Baz"
        except PhoXiError as e:
            print(f"Exception: {e}")

        # Reading setting with default value
        print(f"LaserPower: {settings_handle.CapturingSettings.LaserPower.get(default=10)}")
        print(f"FooBar: {settings_handle.FooBar.get(default=10)}")
        print(f"FooBar: {settings_handle.FooBar.get()}")

        # Setting setting value with result return
        set_result = settings_handle.CapturingSettings.LaserPower.set(2048)
        print(f"LaserPower set {'successful' if set_result else 'failed'}")
        print(f"FooBar set {'successful' if settings_handle.FooBar.set(2048) else 'failed'}")

        # Settings can have limits applied to them, use min() and max() to check these limits.
        # Values outside of this range will be clamped to this range
        print(f"LaserPower min: {settings_handle.CapturingSettings.LaserPower.min()}")
        print(f"LaserPower max: {settings_handle.CapturingSettings.LaserPower.max()}")

        # Some settings can accept only selected values, use enum() to obtain list of values
        print(f"Available ISOs: {settings_handle.CapturingSettings.ISO.enum()}")

        # Obtaining string representation of setting type
        print(f"LaserPower is of type: {settings_handle.CapturingSettings.LaserPower.type()}")
        print(f"ISO is of type: {settings_handle.CapturingSettings.ISO.type()}")

        print("")

        # Read of whole group of settings
        capturing_settings = settings_handle.CapturingSettings.value
        print("Capturing settings:")
        pprint.pprint(capturing_settings)

        print("")

        # Change some values by setting dictionary of settings
        settings_handle.value = {
            "CapturingSettings/ISO": "100",
            "CapturingSettings/LEDPower": 100,
            "CapturingSettings/LaserPower": 100,
        }
        print("Capturing settings after change:")
        pprint.pprint(settings_handle.CapturingSettings.value)

        # Change some values by setting sub-dictionary of settings
        settings_handle.CapturingSettings.value = {
            "ISO": "200",
            "LEDPower": 200,
            "LaserPower": 200,
        }
        print("Capturing settings after change:")
        pprint.pprint(settings_handle.CapturingSettings.value)

        # Unavailable setting in dictionary raises an exception
        try:
            settings_handle.value = {
                "CapturingSettings/ISO": "100",
                "Foo/Bar": "Baz",
            }  # <-- Unavailable
        except PhoXiError as e:
            print(f"Exception: {e}")

        # set() can be also used to set dictionary of settings.
        # Unavailable setting will be printed in warning and result will be False
        set_dict_result = settings_handle.set(
            {"CapturingSettings/ISO": "100", "Foo/Bar": "Baz"}
        )  # <-- Unavailable
        print(f"Setting unavailable settings via .set() result: {set_dict_result}")

        print("")

        # Read of list of settings at once
        settings, errors = device.get_settings(
            [
                "CapturingSettings/ISO",
                "CapturingSettings/LEDPower",
                "CapturingSettings/LaserPower",
                "CapturingSettings/FooBar",  # <- Unavailable will be reported in 'errors'
            ]
        )
        print("Read of multiple settings:")
        pprint.pprint(settings)
        print("Errors which occurred during settings read:")
        pprint.pprint(errors)

        # Accessing setting read from device
        print(f"ISO: {settings['CapturingSettings/ISO']}")
        print(f"LEDPower: {settings['CapturingSettings/LEDPower']}")
        print(f"LaserPower: {settings['CapturingSettings/LaserPower']}")

        print("")

        # Set multiple settings at once by path
        errors = device.set_settings(
            {
                "CapturingSettings/ISO": "300",
                "CapturingSettings/LEDPower": 1,
                "CapturingSettings/LaserPower": 1,
                "CapturingSettings/FooBar": "Baz",  # <- Unavailable will be reported in 'errors'
            }
        )
        print("Errors which occurred during settings set:")
        pprint.pprint(errors)

        print("")
        print("Direct access:")
        print("")

        # Access settings with PhoXi Control GUI paths
        # Same as above but spaces in setting paths are replaced by double underscore "__"
        # Get settings handle
        direct_settings_handle = device.settings(access_type="direct")
        # Check single setting availability
        print(
            f"LaserPower is"
            f" {'' if direct_settings_handle.General__Settings.LED__Power.can_get() else 'not'} "
            f"gettable"
        )
        print(
            f"LaserPower is"
            f" {'' if direct_settings_handle.General__Settings.LED__Power.can_set() else 'not'} "
            f"settable"
        )
        # Set single setting
        direct_settings_handle.General__Settings.LED__Power.value = 1024
        # Read single setting
        print(f"LaserPower - direct: {direct_settings_handle.General__Settings.LED__Power.value}")

        # Reading not available settings raises an exception
        try:
            print(f"FooBar value: {direct_settings_handle.Foo__Bar.value}")
        except PhoXiError as e:
            print(f"Exception: {e}")
        # Setting not available setting raises an exception
        try:
            direct_settings_handle.Foo__Bar.value = "Baz"
        except PhoXiError as e:
            print(f"Exception: {e}")

        print("")

        # When using string paths no space replacement is necessary
        # Read of list of settings at once
        direct_settings, direct_errors = device.get_settings(
            [
                "General Settings/ISO",
                "General Settings/LED Power",
                "General Settings/Laser Power",
                "General Settings/Foo Bar",  # <- Unavailable will be reported
            ],
            access_type="direct",
        )
        print("Read of multiple settings:")
        pprint.pprint(direct_settings)
        print("Errors which occurred during settings read:")
        pprint.pprint(direct_errors)

        # Accessing setting read from device
        print(f"ISO: {direct_settings['General Settings/ISO']}")
        print(f"LED Power: {direct_settings['General Settings/LED Power']}")
        print(f"Laser Power: {direct_settings['General Settings/Laser Power']}")

        print("")

        # Set multiple settings at once by path
        direct_errors = device.set_settings(
            {
                "General Settings/ISO": "300",
                "General Settings/LED Power": 1,
                "General Settings/Laser Power": 1,
                "General Settings/Foo Bar": "Baz",  # <- Unavailable will be reported
            },
            access_type="direct",
        )
        print("Errors which occurred during settings set:")
        pprint.pprint(direct_errors)

        print("")
