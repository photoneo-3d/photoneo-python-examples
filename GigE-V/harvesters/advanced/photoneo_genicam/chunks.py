import numpy as np
from genicam.genapi import NodeMap


def parse_chunk_selector(features: NodeMap, chunk_feature_name: str) -> dict:
    selector_alias: str = f"Chunk{chunk_feature_name}Selector"
    value_alias: str = f"Chunk{chunk_feature_name}Value"
    chunk_data = {}
    for s_opts in features.get_node(selector_alias).symbolics:
        features.get_node(selector_alias).value = s_opts
        chunk_data[s_opts] = features.get_node(value_alias).value
    return chunk_data


def get_transformation_matrix_from_chunk(parsed_chunk: dict) -> np.ndarray:
    # We can not trust the Harvesters .symbolics order of the Enum node, so we explicitly set the order
    order = [
        "Rot00",
        "Rot01",
        "Rot02",
        "TransX",
        "Rot10",
        "Rot11",
        "Rot12",
        "TransY",
        "Rot20",
        "Rot21",
        "Rot22",
        "TransZ",
    ]

    chunk_data: list = [parsed_chunk.get(key) for key in order]
    transformation_matrix_3x4 = np.array(chunk_data).reshape(3, 4)
    return np.vstack([transformation_matrix_3x4, [0.0, 0.0, 0.0, 1.0]])
