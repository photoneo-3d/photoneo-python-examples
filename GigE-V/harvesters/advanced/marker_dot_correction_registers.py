#!/usr/bin/env python3
import sys
from pathlib import Path

import numpy as np
from genicam.genapi import NodeMap
from harvesters.core import Harvester
from photoneo_genicam.default_gentl_producer import producer_path
from photoneo_genicam.features import enable_software_trigger
from photoneo_genicam.user_set import load_default_user_set
from photoneo_genicam.utils import data_stream_reset, logger

def main(device_sn: str):
    with (Harvester() as h):
        h.add_file(str(producer_path), check_existence=True, check_validity=True)
        h.update()

        logger.info(f"Connecting to: {device_sn}")
        with h.create({"serial_number": device_sn}) as ia:
            features: NodeMap = ia.remote_device.node_map
            logger.info(f"Device Firmware version: {features.DeviceFirmwareVersion.value}")

            load_default_user_set(features)
            enable_software_trigger(features)

            if not features.MarkerDotCorrectionAvailable.value:
                raise RuntimeError("Marker Dot Correction is not available")

            # Set OutputTopology to RegularGrid or FullGrid for MotionCam-3D device
            if features.has_node("OutputTopology"):
                features.OutputTopology.value = "RegularGrid"

            # Enable frame payload chunks
            features.ChunkModeActive.value = True

            # Enables `ChunkMarkerDotCorrection_Status` and
            # `ChunkMarkerDotCorrection_AvailableMarkersCount`
            features.ChunkSelector.value = "MarkerDotCorrection"
            features.ChunkEnable.value = True

            # Enable chunks with marker dot coordinates needed
            marker_chunks = [
                "MarkerDotCorrection_ReferenceMarkers2d",
                "MarkerDotCorrection_ReferenceMarkers3d",
                "MarkerDotCorrection_ObservedMarkers2d",
                "MarkerDotCorrection_ObservedMarkers3d",
                "MarkerDotCorrection_CorrectedMarkers3d",
            ]
            for chunk in marker_chunks:
                features.ChunkSelector.value = chunk
                features.ChunkEnable.value = True

            # Enable chunk with transformation matrix to read corrected matrix
            features.ChunkSelector.value = "CurrentCameraToCoordinateSpaceTransformation"
            features.ChunkEnable.value = True

            # Set expected number of marker dots present in the scene (default 10)
            # Total number of recognized/observed marker dots in the scene
            # will be set in `ChunkMarkerDotCorrection_AvailableMarkersCount`.
            # The number of marker dots present in the chunk register is set to:
            #   ChunkMarkerDotCorrection_{point type}Count (e.g. ChunkMarkerDotCorrection_ReferenceMarkers2dCount)
            # which is also equal to:
            #   min(MarkerDotCorrection_MarkersCount, ChunkMarkerDotCorrection_AvailableMarkersCount).
            features.MarkerDotCorrection_MarkersCount.value = 5

            # Chunks and count of Marker Dots must be set before stream channel is opened
            data_stream_reset(ia)
            ia.start()

            # Marker Dot coordinates parser
            def get_marker_dots(chunk_name: str, point_size: int):
                chunk_node = features.get_node(chunk_name)
                if chunk_node.length == 0:
                    return None

                buffer = chunk_node.get(chunk_node.length)
                arr = np.frombuffer(buffer, dtype=np.float32)
                count = features.get_node(f"{chunk_name}Count").value
                return arr.reshape((count, point_size))

            # Transformation matrix parser
            def get_transformation_matrix(chunk_name: str):
                chunk_node = features.get_node(chunk_name)
                buffer = chunk_node.get(chunk_node.length)
                arr = np.frombuffer(buffer, dtype=np.float64)
                return np.vstack([arr.reshape((3, 4)), [0.0, 0.0, 0.0, 1.0]])

            # Record reference
            reference_dots = None
            transformation_matrix = None
            features.MarkerDotCorrection_Mode.value = "ReferenceRecording"
            features.TriggerSoftware.execute()
            with ia.fetch(timeout=30) as _:
                if features.ChunkMarkerDotCorrection_Status.value != "ReferenceSuccessfullyRecorded":
                    ex_msg = f"Failed to record Marker Dot Correction reference. Status: {features.ChunkMarkerDotCorrection_Status.value}"
                    raise RuntimeError(ex_msg)
                reference_dots = get_marker_dots("ChunkMarkerDotCorrection_ReferenceMarkers2d", 2)
                transformation_matrix = get_transformation_matrix("ChunkCurrentCameraToCoordinateSpaceTransformationValueAll")

            if reference_dots is None:
                ex_msg = "No reference Marker Dots found"
                raise RuntimeError(ex_msg)
            if transformation_matrix is None:
                ex_msg = "Failed to get transformation matrix"
                raise RuntimeError(ex_msg)

            print(f"Recorded {len(reference_dots)} reference Marker Dots")

            # Capture test frame
            observed_dots = None
            observed_dots_reference = None
            corrected_transformation_matrix = None
            features.MarkerDotCorrection_Mode.value = "Active"
            features.TriggerSoftware.execute()
            with ia.fetch(timeout=30) as _:
                if features.ChunkMarkerDotCorrection_Status.value != "CorrectionApplied":
                    ex_msg = f"Failed to apply Marker Dot Correction. Status: {features.ChunkMarkerDotCorrection_Status.value}"
                    raise RuntimeError(ex_msg)
                observed_dots = get_marker_dots("ChunkMarkerDotCorrection_ObservedMarkers2d", 2)
                observed_dots_reference = get_marker_dots("ChunkMarkerDotCorrection_ReferenceMarkers2d", 2)
                corrected_transformation_matrix = get_transformation_matrix("ChunkCurrentCameraToCoordinateSpaceTransformationValueAll")

            if observed_dots is None or observed_dots_reference is None:
                ex_msg = "No Marker Dots observed"
                raise RuntimeError(ex_msg)
            if transformation_matrix is None:
                ex_msg = "Failed to get corrected transformation matrix"
                raise RuntimeError(ex_msg)

            print(f"Observed {len(observed_dots)} Marker Dots")

            # Process Marker Dot Correction data
            for index, reference_dot in enumerate(reference_dots):
                for observed_dot, observed_dot_reference in zip(
                        observed_dots, observed_dots_reference):
                    if np.all(observed_dot_reference == reference_dot):
                        distance = np.linalg.norm(observed_dot - reference_dot)
                        print(f"Marker Dot {index} seen in the reference at {reference_dot} was recognized at {observed_dot}, displaced by {distance}px")
                        break
                else:
                    print(f"Marker Dot {index} was not recognized in current frame.")

            # In the `Active` mode the transformation matrix is corrected by Marker Dot Correction
            # and should be then applied to relevant frame matrices to obtain corrected values from
            # the frame
            print("Original transformation matrix:")
            print(transformation_matrix)
            print("Corrected transformation matrix:")
            print(corrected_transformation_matrix)


if __name__ == "__main__":
    try:
        device_id = sys.argv[1]
    except IndexError:
        print("Error: no device given, please run it with the device serial number as argument:")
        print(f"    {Path(__file__).name} <device serial>")
        sys.exit(1)
    main(device_id)
