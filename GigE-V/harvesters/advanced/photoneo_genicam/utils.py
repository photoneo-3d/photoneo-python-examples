import logging
import os
import platform
import sys
import time
from enum import Enum, auto
from functools import wraps
from genicam.genapi import NodeMap
from harvesters.core import ImageAcquirer
from packaging import version


def get_system_info() -> str:
    return f"OS: {platform.system()} ({platform.version().split()[0]}) | Python: {sys.version.split()[0]}"


def setup_logger(name="HarverserExamples", level=logging.DEBUG):
    log_format = "[%(asctime)s] %(levelname)s: %(message)s"
    logging.basicConfig(level=level, format=log_format, datefmt="%H:%M:%S")
    return logging.getLogger(name)


logger = setup_logger()


def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time_ms = (end_time - start_time) * 1000
        logger.debug(f"Execution time of {func.__name__}: {execution_time_ms:.2f} milliseconds")
        return result

    return wrapper


def write_raw_array(filename: str, array):
    with open(filename, "wb") as file:
        for element in array:
            file.write(element.tobytes())


def data_stream_reset(ia: ImageAcquirer):
    """
    Reset the stream channel before calling ia.start again when start/stop is called multiple times
    on the same ImageAcquirer object.

    Note: These are Harvesters internal functions, so the API may change in the future.
    """
    ia._release_data_streams()
    ia._setup_data_streams(file_dict=ia._file_dict)


def version_check(features: NodeMap, minimal_fw_version: str):
    fw: str = features.DeviceFirmwareVersion.value
    if version.parse(fw) < version.parse(minimal_fw_version):
        logger.warning(f"Minimal FW requirement not met: {fw} < {minimal_fw_version}")
        return

class OSType(Enum):
    WINDOWS = auto()
    LINUX = auto()
    MACOS = auto()
    UNKNOWN = auto()

    @staticmethod
    def detect():
        os_name = platform.system()
        if os_name == "Windows":
            return OSType.WINDOWS
        elif os_name == "Linux":
            return OSType.LINUX
        elif os_name == "Darwin":
            return OSType.MACOS
        else:
            return OSType.UNKNOWN
