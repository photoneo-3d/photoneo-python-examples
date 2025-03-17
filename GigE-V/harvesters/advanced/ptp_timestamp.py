#!/usr/bin/env python3
import sys
import threading
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from harvesters.core import Harvester

from photoneo_genicam.default_gentl_producer import producer_path
from photoneo_genicam.utils import (data_stream_reset, setup_logger,
                                    version_check)


class PtpStatus(Enum):
    INITIALIZING = "Initializing"
    FAULTY = "Faulty"
    DISABLED = "Disabled"
    LISTENING = "Listening"
    PRE_MASTER = "PreMaster"
    MASTER = "Master"
    PASSIVE = "Passive"
    UNCALIBRATED = "Uncalibrated"
    SLAVE = "Slave"


def to_datetime(timestamp: int) -> datetime:
    ptp_timestamp_sec = timestamp / 1e9
    return datetime.fromtimestamp(ptp_timestamp_sec, tz=timezone.utc)


def connect_device(h, serial_number):
    logger = setup_logger(name=serial_number)

    logger.info(f"Connecting to: {serial_number}")
    with h.create({"serial_number": serial_number}) as ia:
        features = ia.remote_device.node_map
        logger.info(f"Device Firmware version: {features.DeviceFirmwareVersion.value}")
        version_check(features, "1.14.0-a")

        features.UserSetSelector.value = "Default"
        features.UserSetLoad.execute()

        features.TriggerSelector.value = "FrameStart"
        features.TriggerMode.value = "On"
        features.TriggerSource.value = "Software"

        features.PtpEnable.value = True
        features.TimestampLatch.execute()

        logger.info(f"PTP State: {PtpStatus(features.PtpStatus.value)}")
        logger.info(f"GrandMaster ID: {features.PtpGrandmasterClockID.value}")
        logger.info(f"Latched timestamp: {features.TimestampLatchValue.value}")
        logger.info(f"Datetime: {to_datetime(features.TimestampLatchValue.value)}")

        data_stream_reset(ia)
        ia.start()
        features.TriggerSoftware.execute()
        with ia.fetch(timeout=10) as buffer:
            logger.info(f"Frame timestamp: {buffer.timestamp}")
            logger.info(f"Frame timestamp as datetime: {to_datetime(buffer.timestamp_ns)}")
        ia.stop()


def main(device1_sn: str, device2_sn: str):
    with Harvester() as h:
        h.add_file(str(producer_path), check_existence=True, check_validity=True)
        h.update()

        thread1 = threading.Thread(target=connect_device, args=(h, device1_sn))
        thread2 = threading.Thread(target=connect_device, args=(h, device2_sn))

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()


if __name__ == "__main__":
    try:
        device1_id = sys.argv[1]
        device2_id = sys.argv[2]
        main(device1_id, device2_id)
    except IndexError:
        print("Error: no device given, please run it with the device serial number as argument:")
        print(f"{Path(__file__).name} <device1 serial> <device2 serial>")
        sys.exit(1)
