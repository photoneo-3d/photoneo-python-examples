import logging
import platform
import sys

from harvesters.core import ImageAcquirer


def get_system_info() -> str:
    return f"OS: {platform.system()} ({platform.version().split()[0]}) | Python: {sys.version.split()[0]}"


def setup_logger(name="HarverserExamples", level=logging.DEBUG):
    log_format = "[%(asctime)s] %(levelname)s: %(message)s"
    logging.basicConfig(level=level, format=log_format, datefmt="%H:%M:%S")
    return logging.getLogger(name)


logger = setup_logger()


def data_stream_reset(ia: ImageAcquirer):
    """
    Reset the stream channel before calling ia.start again when start/stop is called multiple times
    on the same ImageAcquirer object.

    Note: These are Harvesters internal functions, so the API may change in the future.
    """
    ia._release_data_streams()
    ia._setup_data_streams(file_dict=ia._file_dict)
