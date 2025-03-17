import os
from pathlib import Path
from sys import platform

from utils import get_system_info, logger

GENTL_PATHS = os.getenv("GENICAM_GENTL64_PATH").split(os.pathsep)


default_gentl_producer_file = "libmvGenTLProducer.so"
if platform == "win32":
    default_gentl_producer_file = "mvGenTLProducer.cti"

logger.debug(get_system_info())


def first(iterable, predicate, default=None):
    return next((i for i in iterable if predicate(i)), default)


def find_producer_path(producer_file_name: str) -> Path:
    return first(
        (Path(p) / producer_file_name for p in GENTL_PATHS),
        Path.exists,
        default="GentlProducerNotFound",
    )


producer_path: Path = find_producer_path(default_gentl_producer_file)
logger.debug(f"Loading: {producer_path}")
