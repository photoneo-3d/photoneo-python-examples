import sys
from pathlib import Path

import argparse
from genicam.genapi import NodeMap
from harvesters.core import Harvester

from gentl_producer_loader import producer_path
from utils import logger


def main(device_sn: str, enable: bool):
    with Harvester() as h:
        h.add_file(str(producer_path), check_existence=True, check_validity=True)
        h.update()

        logger.info(f"Connecting to: {device_sn}")
        with h.create({"serial_number": device_sn}) as ia:
            features: NodeMap = ia.remote_device.node_map
            logger.info(f"Device Firmware version: {features.DeviceFirmwareVersion.value}")

            # Please note that after executing this command, the network interface is reset,
            # and the device will not be available for a few seconds. 
            # As a result, the following commands may time out, and a reconnect procedure should be followed.
            features.EnableJumboFrames.value = enable
            logger.info(f"Jumbo frames {'enabled' if enable else 'disabled'}")

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("device_id", help="Device serial number")
    argparser.add_argument("--enable", help="Enable jumbo frames", action="store_true")
    argparser.add_argument("--disable", help="Disable jumbo frames", action="store_true")
    args = argparser.parse_args()

    if args.enable and args.disable:
        print("Error: cannot enable and disable jumbo frames at the same time")
        sys.exit(1)
    if not args.enable and not args.disable:
        print("Error: please specify either --enable or --disable")
        sys.exit(1)
    
    main(args.device_id, args.enable)
