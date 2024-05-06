from genicam.genapi import NodeMap


def enable_trigger(features: NodeMap, source: str):
    features.TriggerSelector.value = "FrameStart"
    features.TriggerMode.value = "On"
    features.TriggerSource.value = source


def enable_software_trigger(features: NodeMap):
    enable_trigger(features, "Software")


def enable_hardware_trigger(features: NodeMap):
    enable_trigger(features, "Line1")
