#!/usr/bin/env python3
import sys
from pathlib import Path

import numpy as np
from genicam.genapi import NodeMap
from harvesters.core import Harvester
from photoneo_genicam.default_gentl_producer import producer_path
from photoneo_genicam.chunks import parse_chunk_selector, get_transformation_matrix_from_chunk
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
            # Actual number of recognized/observed marker dots in the scene
            # will be set in `ChunkMarkerDotCorrection_AvailableMarkersCount`
            # The number of marker dots present in the chunk data is equal to:
            #   min(MarkerDotCorrection_MarkersCount, ChunkMarkerDotCorrection_AvailableMarkersCount)
            features.MarkerDotCorrection_MarkersCount.value = 5

            # Chunks and count of Marker Dots must be set before stream channel is opened
            data_stream_reset(ia)
            ia.start()

            # Record reference
            reference_dots = []
            transformation_matrix = []
            features.MarkerDotCorrection_Mode.value = "ReferenceRecording"
            features.TriggerSoftware.execute()
            with ia.fetch(timeout=30) as _:
                if features.ChunkMarkerDotCorrection_Status.value != "ReferenceSuccessfullyRecorded":
                    ex_msg = f"Failed to record Marker Dot Correction reference. Status: {features.ChunkMarkerDotCorrection_Status.value}"
                    raise RuntimeError(ex_msg)
                for i in range(features.ChunkMarkerDotCorrection_ReferenceMarkers2dCount.value):
                    features.ChunkMarkerDotCorrection_ReferenceMarkers2dIndex.value = i
                    reference_dots.append([
                        features.ChunkMarkerDotCorrection_ReferenceMarkers2dX.value,
                        features.ChunkMarkerDotCorrection_ReferenceMarkers2dY.value
                    ])

                transformation_matrix = get_transformation_matrix_from_chunk(
                    parse_chunk_selector(features, "CurrentCameraToCoordinateSpaceTransformation"))

            print(f"Recorded {len(reference_dots)} reference Marker Dots")

            # Capture test frame
            observed_dots = []
            observed_dots_reference = []
            corrected_transformation_matrix = []
            features.MarkerDotCorrection_Mode.value = "Active"
            features.TriggerSoftware.execute()
            with ia.fetch(timeout=30) as _:
                if features.ChunkMarkerDotCorrection_Status.value != "CorrectionApplied":
                    ex_msg = f"Failed to apply Marker Dot Correction. Status: {features.ChunkMarkerDotCorrection_Status.value}"
                    raise RuntimeError(ex_msg)
                for i in range(features.ChunkMarkerDotCorrection_ReferenceMarkers2dCount.value):
                    features.ChunkMarkerDotCorrection_ReferenceMarkers2dIndex.value = i
                    observed_dots_reference.append([
                        features.ChunkMarkerDotCorrection_ReferenceMarkers2dX.value,
                        features.ChunkMarkerDotCorrection_ReferenceMarkers2dY.value
                    ])
                for i in range(features.ChunkMarkerDotCorrection_ObservedMarkers2dCount.value):
                    features.ChunkMarkerDotCorrection_ObservedMarkers2dIndex.value = i
                    observed_dots.append([
                        features.ChunkMarkerDotCorrection_ObservedMarkers2dX.value,
                        features.ChunkMarkerDotCorrection_ObservedMarkers2dY.value
                    ])
                corrected_transformation_matrix = get_transformation_matrix_from_chunk(
                    parse_chunk_selector(features, "CurrentCameraToCoordinateSpaceTransformation"))

            print(f"Observed {len(observed_dots)} Marker Dots")

            # Process Marker Dot Correction data
            for index, reference_dot in enumerate(reference_dots):
                for observed_dot, observed_dot_reference in zip(
                        observed_dots, observed_dots_reference):
                    if np.all(observed_dot_reference == reference_dot):
                        distance = np.linalg.norm(np.array(observed_dot) - np.array(reference_dot))
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
