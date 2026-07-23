# Read a single PRAW or PMRAW file and print its metadata, settings, and first matrix.
#
# Prerequisites:
#   - PHOXI_CONTROL_PATH environment variable pointing to PhoXi Control installation directory
#   - phoxi_api Python package installed
#
# Usage:
#   python read_praw_file.py <path>
#   python read_praw_file.py <path> --frame <index>   # PMRAW only

import argparse
import pprint
import sys

from phoxi_api import PrawReader

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("path", type=str, help="Path to a .praw or .pmraw file")
    arg_parser.add_argument(
        "--frame", type=int, default=0, help="Frame index to open (PMRAW only, default: 0)"
    )
    args = arg_parser.parse_args()

    # PrawReader is used as a context manager — the file is closed automatically on exit.
    # For PMRAW files use frame_index to select which frame to read (default: 0).
    with PrawReader(args.path, frame_index=args.frame) as reader:
        # info() returns device metadata stored in the file header: device name,
        # variant, firmware version, serial number, and PhoXi Control version.
        info = reader.info()
        print("File info:")
        pprint.pp(info._asdict())

        # list_settings() returns the names of all scan settings saved in the file
        # (e.g. Resolution, ShutterMultiplier, TriggerMode).
        settings = reader.list_settings()
        print(f"\nAvailable settings ({len(settings)}):")
        pprint.pp(settings)

        # list_matrices() returns the names of all data matrices stored in the file
        # (e.g. Texture, DepthMap, PointCloud, NormalMap).
        matrices = reader.list_matrices()
        print(f"\nAvailable matrices ({len(matrices)}):")
        pprint.pp(matrices)

        # read_setting() returns the value with its native type (bool, int, float, str).
        if settings:
            path = settings[0]
            value = reader.read_setting(path)
            print(f"\nSetting '{path}': {value!r}")

        if not matrices:
            print("No matrices found.")
            sys.exit(0)

        # read_matrix() returns a numpy array. The dtype reflects the raw sensor data
        # (e.g. float32 for DepthMap, uint16 for Texture).
        path = matrices[0]
        mat = reader.read_matrix(path)
        print(f"\nMatrix '{path}':")
        print(f"  shape : {mat.shape}")
        print(f"  dtype : {mat.dtype}")
        print(f"  min   : {mat.min():.4f}")
        print(f"  max   : {mat.max():.4f}")
