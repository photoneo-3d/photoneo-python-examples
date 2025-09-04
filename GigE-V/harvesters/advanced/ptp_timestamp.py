#!/usr/bin/env python3
import logging
import sys
import threading
import time
from datetime import datetime, timezone
from enum import Enum
from io import StringIO
from pathlib import Path

from harvesters.core import Harvester

from photoneo_genicam.default_gentl_producer import producer_path
from photoneo_genicam.utils import data_stream_reset, version_check

SCAN_COUNT = 5


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


def decimal_to_ptp_identity(decimal_id: int) -> str:
    hex_id = f"{decimal_id:016x}"
    return f"{hex_id[:6]}.fffe.{hex_id[6:]}"


class BufferedLogger:
    _buffers = {}
    _loggers = {}

    def __init__(self, name):
        if name not in self._loggers:
            stream = StringIO()
            logger = logging.getLogger(name)
            logger.setLevel(logging.INFO)

            handler = logging.StreamHandler(stream)
            handler.setFormatter(logging.Formatter("[%(name)s] %(message)s"))
            logger.addHandler(handler)
            logger.propagate = False

            self._loggers[name] = logger
            self._buffers[name] = stream

        self.name = name
        self.logger = self._loggers[name]
        self.buffer = self._buffers[name]

    def log(self, msg):
        self.logger.info(msg)

    def print(self):
        print(self.buffer.getvalue(), end="")

    @classmethod
    def print_all(cls):
        for name, buffer in cls._buffers.items():
            print(buffer.getvalue(), end="")
        print("-" * 20)


def connect_device(h, serial_number):
    logger = BufferedLogger(serial_number)

    with h.create({"serial_number": serial_number}) as ia:
        features = ia.remote_device.node_map
        version_check(features, "1.14.0-a")

        features.UserSetSelector.value = "Default"
        features.UserSetLoad.execute()

        features.TriggerSelector.value = "FrameStart"
        features.TriggerMode.value = "On"
        features.TriggerSource.value = "Software"

        old_laser_power = features.LaserPower.value
        features.LaserPower.value = 1

        features.PtpEnable.value = True
        features.TimestampLatch.execute()
        features.PtpDataSetLatch.execute()

        ia.data_streams[0].node_map.mvResendActive.value = True
        data_stream_reset(ia)
        ia.start()
        for i in range(SCAN_COUNT):
            features.TriggerSoftware.execute()
            with ia.fetch(timeout=10) as buffer:
                logger.log(
                    f"Frame start acquisition time is {to_datetime(buffer.timestamp_ns)}, "
                    f"PTP port state is {PtpStatus(features.PtpStatus.value)}, "
                    f"PTP grandmaster identity is {decimal_to_ptp_identity(features.PtpGrandmasterClockID.value)}"
                )
        time.sleep(1)
        features.LaserPower.value = old_laser_power


def main(device1_sn: str, device2_sn: str):
    with Harvester() as h:
        h.add_file(str(producer_path), check_existence=True, check_validity=True)
        h.update()

        print(f"Collecting {SCAN_COUNT} frames from connected devices")
        connect_device(h, device1_sn)
        time.sleep(2)
        connect_device(h, device2_sn)

        BufferedLogger.print_all()


if __name__ == "__main__":
    try:
        device1_id = sys.argv[1]
        device2_id = sys.argv[2]
        main(device1_id, device2_id)
    except IndexError:
        print(
            "Error: no device given, please run it with the device serial number as argument:"
        )
        print(f"{Path(__file__).name} <device1 serial> <device2 serial>")
        sys.exit(1)
