import os
from pathlib import Path
from sys import platform
from typing import List

import cv2
from genicam.genapi import NodeMap
from harvesters.core import ParameterKey, ParameterSet
from rich.console import Console

# Example usage how to change connection parameters
CONNECTION_SETTINGS: ParameterSet = ParameterSet(
    {
        ParameterKey.NUM_BUFFERS_FOR_FETCH_CALL: 2,
    }
)

GENTL_PATHS = os.getenv("GENICAM_GENTL64_PATH", default=".").split(os.pathsep)

GenTL_file = "libmvGenTLProducer.so"
if platform == "win32":
    GenTL_file = "mvGenTLProducer.cti"


def first(iterable, predicate, default=None):
    return next((i for i in iterable if predicate(i)), default)


cti_file_path: Path = first(
    (Path(p) / GenTL_file for p in GENTL_PATHS), Path.exists, default="CTI NOT FOUND"
)

console = Console(width=150)

INTENSITY = "Intensity"
RANGE = "Range"
CONFIDENCE = "Confidence"
NORMAL = "Normal"
EVENT = "Event"
COLOR_CAMERA = "ColorCamera"
REPROJECTION = "Reprojection"


def get_opencv_image(input_tex):
    """Returns opencv image from numpy array."""
    if input_tex.width > 0 and input_tex.height > 0:
        texture = input_tex.data.reshape(input_tex.height, input_tex.width, 1).copy()
        normalized = cv2.normalize(
            texture, dst=None, alpha=0, beta=65535, norm_type=cv2.NORM_MINMAX
        )
        return normalized
    else:
        raise Exception("Texture is empty")


def enable_components(f: NodeMap, components: List[str]) -> None:
    """Enable exactly the listed components, disabling all others."""
    for component in f.ComponentSelector.symbolics:
        f.ComponentSelector.value = component
        f.ComponentEnable.value = component in components


def sorted_components(f: NodeMap) -> List[str]:
    """Returns the components sorted in the order they appear in multipart (i.e. their IDValue.)"""

    def component_id_value(comp: str) -> int:
        f.ComponentSelector.value = comp
        return f.ComponentIDValue.value

    componentIdValues = {c: component_id_value(c) for c in f.ComponentSelector.symbolics}
    return sorted(f.ComponentSelector.symbolics, key=lambda x: componentIdValues[x])


def is_component_enabled(f: NodeMap, component: str) -> bool:
    f.ComponentSelector.value = component
    return f.ComponentEnable.value


def enabled_components(f: NodeMap) -> List[str]:
    """ Return enabled components in the order in which they will appear in the multipart payload / as chunks.

    The harvesters module doesn't expose component / purpose ids of the parts, but they are always sent in
    a fixed order (by increasing IDValue of the component), so it's possible to match them this way.
    """
    return [
        component
        for component in sorted_components(f)
        if is_component_enabled(f, component)
    ]


def get_component_statuses(f: NodeMap) -> str:
    """Returns the components statuses as formatted string."""
    console.print("[green]Component selector status")
    res = ""
    for comp in sorted_components(f):
        state = (
            "[green]Enabled[/green]"
            if is_component_enabled(f, comp)
            else "[red]Disabled[/red]"
        )
        res += f"[EnumID: {f.ComponentIDValue.value}] ValID: = {f.ComponentIDValue.value}: {comp}: {state}\n"
    return res
