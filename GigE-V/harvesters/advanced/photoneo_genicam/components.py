from typing import List

from genicam.genapi import NodeMap


def enable_components(features: NodeMap, component_list: List[str]):
    for component in features.ComponentSelector.symbolics:
        features.ComponentSelector.value = component
        features.ComponentEnable.value = component in component_list
    features.ComponentSelector.value = component_list[-1]


def sorted_components(features: NodeMap) -> List[str]:
    """Returns the components sorted in the order they appear in multipart (i.e. their IDValue.)"""

    def component_id_value(comp: str) -> int:
        features.ComponentSelector.value = comp
        return features.ComponentIDValue.value

    componentIdValues = {c: component_id_value(c) for c in features.ComponentSelector.symbolics}
    return sorted(features.ComponentSelector.symbolics, key=lambda x: componentIdValues[x])


def is_component_enabled(features: NodeMap, component: str) -> bool:
    features.ComponentSelector.value = component
    return features.ComponentEnable.value


def enabled_components(features: NodeMap) -> List[str]:
    """Return enabled components in the order in which they will appear in the multipart payload / as chunks.

    The harvesters module doesn't expose component / purpose ids of the parts, but they are always sent in
    a fixed order (by increasing IDValue of the component), so it's possible to match them this way.
    """
    return [
        component
        for component in sorted_components(features)
        if is_component_enabled(features, component)
    ]


def get_component_statuses(features: NodeMap, include_pixel_format=False) -> str:
    """Returns the components statuses as formatted string."""

    def mark_enabled(pixel_format):
        return ("*" if features.PixelFormat.value == pixel_format else "") + pixel_format

    res = ""
    for component in sorted_components(features):
        res += f"[EnumID: {features.ComponentIDValue.value}]".ljust(16)
        res += f"  {component:<16}"
        res += f"{'Enabled' if is_component_enabled(features, component) else 'Disabled':<12}"
        if include_pixel_format:
            res += f"({', '.join(mark_enabled(pf) for pf in features.PixelFormat.symbolics):>})"
        res += "\n"
    return res
