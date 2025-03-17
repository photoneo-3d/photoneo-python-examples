#!/usr/bin/env python3

import platform
import re
import subprocess
import sys
import time
from pathlib import Path

from harvesters.core import Harvester

from gentl_producer_loader import producer_path
from utils import logger


def get_windows_interfaces():
    try:
        out = subprocess.check_output(
            ["netsh", "interface", "ipv4", "show", "interfaces"], text=True
        )
        interfaces = []
        for line in out.splitlines()[2:]:  # Skip headers
            parts = re.split(r"\s{2,}", line.strip())
            if len(parts) >= 4 and parts[3] == "connected":
                name, mtu = parts[4], parts[2]
                if name.lower() != "loopback pseudo-interface 1":  # Ignore loopback
                    interfaces.append((name, mtu))
        return interfaces
    except subprocess.CalledProcessError:
        logger.error("Failed to get Windows interface information.")
        return []


def get_linux_interfaces():
    try:
        out = subprocess.check_output(["ip", "link"], text=True)
        interfaces = []
        for line in out.splitlines():
            match = re.search(r"^(\d+):\s+(\S+):\s+<([^>]+)>", line)
            if match:
                iface_name, flags = match.group(2), match.group(3)
                if "UP" in flags and "LOOPBACK" not in flags:
                    mtu_line = next(
                        (l for l in out.splitlines() if f"mtu" in l and iface_name in l), None
                    )
                    if mtu_line:
                        mtu_match = re.search(r"mtu\s+(\d+)", mtu_line)
                        if mtu_match:
                            interfaces.append((iface_name, mtu_match.group(1)))
        return interfaces
    except subprocess.CalledProcessError:
        logger.error("Failed to get Linux interface information.")
        return []


def get_connected_interfaces():
    interfaces = (
        get_windows_interfaces() if platform.system() == "Windows" else get_linux_interfaces()
    )
    for name, mtu in interfaces:
        logger.info(f"\tInterface: {name:30}  MTU: {mtu}")


def main(device_sn: str):
    with Harvester() as h:
        h.add_file(str(producer_path), check_existence=True, check_validity=True)
        h.update()

        logger.info(f"Interface information")
        get_connected_interfaces()

        start_time = time.time()
        timeout = 3  # in seconds

        while time.time() - start_time < timeout:
            try:
                logger.info(f"Trying to connect to: {device_sn}")
                ia = h.create({"serial_number": device_sn})
                logger.info("Connected successfully!")
                break
            except Exception as e:
                logger.error(f"Error: {e}, retrying...")
                time.sleep(1)
        else:
            logger.error(
                "Timeout: Device did not respond. Check your interface MTU value to ensure compatibility."
            )


if __name__ == "__main__":
    try:
        device_id = sys.argv[1]
    except IndexError:
        print("Error: no device given, please run it with the device serial number as argument:")
        print(f"    {Path(__file__).name} <device serial>")
        sys.exit(1)
    main(device_id)
