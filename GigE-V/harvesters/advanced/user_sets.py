#!/usr/bin/env python3
import sys
from pathlib import Path

from genicam.genapi import IEnumeration, NodeMap
from harvesters.core import Harvester

from photoneo_genicam.default_gentl_producer import producer_path
from photoneo_genicam.user_set import load_default_user_set


def pretty_print_user_set_options(features: NodeMap):

    def node_exists(s):
        try:
            features.get_node(s)
            return True
        except Exception as e:
            return False

    def is_enum(setting_name):
        return isinstance(features.get_node(setting_name), IEnumeration)

    print(f"Available user set settings: ")
    for setting in features.UserSetFeatureSelector.symbolics:
        if node_exists(setting) and is_enum(setting):
            opts = features.get_node(setting).symbolics
            print(f"{setting} - [{opts}]")
        else:
            print(f"{setting}")


def main(device_sn: str):
    with Harvester() as h:
        h.add_file(str(producer_path), check_existence=True, check_validity=True)
        h.update()

        with h.create({"serial_number": device_sn}) as ia:
            features: NodeMap = ia.remote_device.node_map
            load_default_user_set(features)

            settings_map = {
                "CalibrationVolumeOnly": False,
                "TextureSource": "Laser",
                "ExposureTime": 10.24,
                "LEDPower": 2000,
                "ShutterMultiplier": 2,
                "NormalsEstimationRadius": 2,
            }

            print(f"Available user sets: {features.UserSetSelector.symbolics}")

            print("Changing some settings:")
            for s, v in settings_map.items():
                print(f"  {s}: {features.get_node(s).value} -> {v}")
                features.get_node(s).value = v

            print()
            print(f"Store these changes into UserSet1")
            features.UserSetSelector.value = "UserSet1"
            features.UserSetSave.execute()
            print(f"OK")

            print()
            print(f"Load Default profile to restore default setting values")
            features.UserSetSelector.value = "Default"
            features.UserSetLoad.execute()
            print(f"OK")

            print()
            print(f"Restored settings:")
            for s, v in settings_map.items():
                print(f"  {s}: {features.get_node(s).value}")

            print()
            print("Load UserSet1")
            features.UserSetSelector.value = "UserSet1"
            features.UserSetLoad.execute()
            print(f"OK")

            print()
            print(f"Current settings (from UserSet1):")
            for s, v in settings_map.items():
                print(f"  {s}: {features.get_node(s).value}")


if __name__ == "__main__":
    try:
        device_id = sys.argv[1]
    except IndexError:
        print("Error: no device given, please run it with the device serial number as argument:")
        print(f"    {Path(__file__).name} <device serial>")
        sys.exit(1)
    main(device_id)
