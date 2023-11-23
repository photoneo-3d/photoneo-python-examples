import os
from pathlib import Path
from sys import platform

from harvesters.core import ParameterKey, ParameterSet

# Example usage how to change connection parameters
CONNECTION_SETTINGS: ParameterSet = ParameterSet(
    {
        ParameterKey.NUM_BUFFERS_FOR_FETCH_CALL: 2,
    }
)

module_dir = Path(__file__).resolve().parent
GENTL_PATHS = os.getenv("GENICAM_GENTL64_PATH", default=str(module_dir)).split(
    os.pathsep
)

GenTL_file = "libmvGenTLProducer.so"
if platform == "win32":
    GenTL_file = "mvGenTLProducer.cti"


def first(iterable, predicate, default=None):
    return next((i for i in iterable if predicate(i)), default)


cti_file_path: Path = first(
    (Path(p) / GenTL_file for p in GENTL_PATHS), Path.exists, default="CTI NOT FOUND"
)
