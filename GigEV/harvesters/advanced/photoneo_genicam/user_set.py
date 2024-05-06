from genicam.genapi import NodeMap


def load_default_user_set(features: NodeMap):
    features.UserSetSelector.value = "Default"
    features.UserSetLoad.execute()
