import os
import sys
from sys import platform
from harvesters.core import Harvester
import struct

# PhotoneoTL_DEV_<ID>
device_id = "PhotoneoTL_DEV_InstalledExamples-basic-example"
if len(sys.argv) == 2:
    device_id = "PhotoneoTL_DEV_" + sys.argv[1]
print("--> device_id: ", device_id)

if platform == "win32":
    cti_file_path_suffix = "/API/bin/photoneo.cti"
else:
    cti_file_path_suffix = "/API/lib/photoneo.cti"
cti_file_path = os.getenv('PHOXI_CONTROL_PATH') + cti_file_path_suffix
print("--> cti_file_path: ", cti_file_path)

with Harvester() as h:
    h.add_file(cti_file_path, True, True)
    h.update()

    # Print out available devices
    print()
    print("Name : ID")
    print("---------")
    for item in h.device_info_list:
        print(item.property_dict['serial_number'], ' : ', item.property_dict['id_'])
    print()

    with h.create({'id_': device_id}) as ia:
        features = ia.remote_device.node_map

        ## General settings
        # ReadOnly
        is_phoxi_control_running = features.IsPhoXiControlRunning.value
        api_version = features.PhotoneoAPIVersion.value
        id = features.PhotoneoDeviceID.value
        type = features.PhotoneoDeviceType.value
        is_acquiring = features.IsAcquiring.value
        is_connected = features.IsConnected.value
        device_firmware_version = features.PhotoneoDeviceFirmwareVersion.value
        device_variant = features.PhotoneoDeviceVariant.value
        device_features = features.PhotoneoDeviceFeatures.value

        if type != "MotionCam3D":
            print("Device is not a MotionCam!")
            sys.exit(0)

        # `Freerun` or `Software`
        trigger_mode = features.PhotoneoTriggerMode.value
        features.PhotoneoTriggerMode.value = 'Freerun'
        # True or False
        wait_for_grabbing_end = features.WaitForGrabbingEnd.value
        features.WaitForGrabbingEnd.value = False
        # Timeout in ms, or values 0 (ZeroTimeout) and -1 (Infinity)
        get_frame_timeout = features.GetFrameTimeout.value
        features.GetFrameTimeout.value = 5000
        # True or False
        logout_after_disconnect = features.LogoutAfterDisconnect.value
        features.LogoutAfterDisconnect.value = False
        # True or False
        stop_acquisition_after_disconnect = features.StopAcquisitionAfterDisconnect.value
        features.StopAcquisitionAfterDisconnect.value = False


        ## Capturing settings
        # <1, 20>
        shutter_multiplier = features.ShutterMultiplier.value
        features.ShutterMultiplier.value = 5
        # <1, 20>
        scan_multiplier = features.ScanMultiplier.value
        features.ScanMultiplier.value = 5
        # `Normal` or `Interreflections`
        coding_strategy = features.CodingStrategy.value
        features.CodingStrategy.value = 'Normal'
        # `Fast`, `High` or `Ultra`
        coding_quality = features.CodingQuality.value
        features.CodingQuality.value = 'Ultra'
        # `Computed`, `LED`, `Laser` or `Focus`
        texture_source = features.TextureSource.value
        features.TextureSource.value = 'Laser'
        # <10.24, 40.96>
        single_pattern_exposure = features.SinglePatternExposure.value
        features.SinglePatternExposure.value = 10.24
        # <0.0, 100.0>
        maximum_fps = features.MaximumFPS.value
        features.MaximumFPS.value = 25
        # <1, 4095>
        laser_power = features.LaserPower.value
        features.LaserPower.value = 2000
        # <1, 4095>
        led_power = features.LEDPower.value
        features.LEDPower.value = 2000
        # True or False
        hardware_trigger = features.HardwareTrigger.value
        features.HardwareTrigger.value = True
        # `Falling`, `Rising` or `Both`
        hardware_trigger_signal = features.HardwareTriggerSignal.value
        features.HardwareTriggerSignal.value = 'Both'

        # `CameraMode`, `ScannerMode` or `Mode2D`
        operation_mode = features.OperationMode.value
        features.OperationMode.value = 'ScannerMode'
        # ReadOnly
        resolution = features.CameraResolution.value
        # <10.24, 40.96>
        camera_exposure = features.CameraExposure.value
        features.CameraExposure.value = 10.24
        # `Standard`
        sampling_topology = features.SamplingTopology.value
        features.SamplingTopology.value = 'Standard'
        # `IrregularGrid`, `RegularGrid` or `Raw`
        output_topology = features.OutputTopology.value
        features.OutputTopology.value = 'Raw'
        # `Normal` or `Interreflections`
        camera_coding_strategy = features.CameraCodingStrategy.value
        features.CameraCodingStrategy.value = 'Interreflections'
        # `Laser`, `LED` or `Color`
        camera_texture_source = features.CameraTextureSource.value
        features.CameraTextureSource.value = 'Laser'


        ## Processing settings
        # <0.0, 100.0>
        max_inaccuracy = features.MaxInaccuracy.value
        features.MaxInaccuracy.value = 3.5
        # `MinX`, `MinY`, `MinZ`, `MaxX`, `MaxY` or `MaxZ`
        camera_space_selector = features.CameraSpaceSelector.value
        features.CameraSpaceSelector.value = 'MinZ'
        # <-999999.0, 999999.0>
        camera_space_value = features.CameraSpaceValue.value
        features.CameraSpaceValue.value = 100.5
        # `MinX`, `MinY`, `MinZ`, `MaxX`, `MaxY` or `MaxZ`
        point_cloud_space_selector = features.PointCloudSpaceSelector.value
        features.PointCloudSpaceSelector.value = 'MaxY'
        # <-999999.0, 999999.0>
        point_cloud_space_value = features.PointCloudSpaceValue.value
        features.PointCloudSpaceValue.value = 200.5
        # <0.0, 90.0>
        max_camera_angle = features.MaxCameraAngle.value
        features.MaxCameraAngle.value = 10
        # <0.0, 90.0>
        max_projector_angle = features.MaxProjectorAngle.value
        features.MaxProjectorAngle.value = 15
        # <0.0, 90.0>
        min_halfway_angle = features.MinHalfwayAngle.value
        features.MinHalfwayAngle.value = 20
        # <0.0, 90.0>
        max_halfway_angle = features.MaxHalfwayAngle.value
        features.MaxHalfwayAngle.value = 25
        # True or False
        calibration_volume_only = features.CalibrationVolumeOnly.value
        features.CalibrationVolumeOnly.value = True
        # `Sharp`, `Normal` or `Smooth`
        surface_smoothness = features.SurfaceSmoothness.value
        features.SurfaceSmoothness.value = 'Normal'
        # <0, 4>
        normals_estimation_radius = features.NormalsEstimationRadius.value
        features.NormalsEstimationRadius.value = 1


        ## Coordinates settings
        # `CameraSpace`, `MarkerSpace`, `RobotSpace` or `CustomSpace`
        camera_space = features.CoordinateSpace.value
        features.CoordinateSpace.value = 'MarkerSpace'
        # `Custom` or `Robot`
        transformation_space_selector = features.TransformationSpaceSelector.value
        features.TransformationSpaceSelector.value = 'Robot'
        # `Row0Col0`, `Row0Col1`, `Row0Col2`, `Row1Col0`, .. , `Row2Col2`
        transformation_rotation_matrix_selector = features.TransformationRotationMatrixSelector.value
        features.TransformationRotationMatrixSelector.value = 'Row0Col1'
        # <-999999.0, 999999.0>
        transformation_rotation_matrix_value = features.TransformationRotationMatrixValue.value
        features.TransformationRotationMatrixValue.value = 150.25
        # Read/Write as raw bytes array    
        custom_transformation_rotation_matrix_length = features.CustomTransformationRotationMatrix.length
        custom_transformation_rotation_matrix_bytes = features.CustomTransformationRotationMatrix.get(custom_transformation_rotation_matrix_length)
        custom_transformation_rotation_matrix = struct.unpack('9d', custom_transformation_rotation_matrix_bytes)
        custom_transformation_rotation_matrix_new_values = [1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8, 9.9]
        custom_transformation_rotation_matrix_new_bytes = struct.pack('9d', *custom_transformation_rotation_matrix_new_values)
        features.CustomTransformationRotationMatrix.set(custom_transformation_rotation_matrix_new_bytes)
        robot_transformation_rotation_matrix_length = features.RobotTransformationRotationMatrix.length
        robot_transformation_rotation_matrix_bytes = features.RobotTransformationRotationMatrix.get(robot_transformation_rotation_matrix_length)
        robot_transformation_rotation_matrix = struct.unpack('9d', robot_transformation_rotation_matrix_bytes)
        robot_transformation_rotation_matrix_new_values = [1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8, 9.9]
        robot_transformation_rotation_matrix_new_bytes = struct.pack('9d', *robot_transformation_rotation_matrix_new_values)
        features.RobotTransformationRotationMatrix.set(robot_transformation_rotation_matrix_new_bytes)
        # `X`, `Y` or `Z`
        transformation_translation_vector_selector = features.TransformationTranslationVectorSelector.value
        features.TransformationTranslationVectorSelector.value = 'Z'
        # <-999999.0, 999999.0>
        transformation_translation_vector_value = features.TransformationTranslationVectorValue.value
        features.TransformationTranslationVectorValue.value = 225.50
        # Read/Write as raw bytes array    
        custom_transformation_translation_vector_length = features.CustomTransformationTranslationVector.length
        custom_transformation_translation_vector_bytes = features.CustomTransformationTranslationVector.get(custom_transformation_translation_vector_length)
        custom_transformation_translation_vector = struct.unpack('3d', custom_transformation_translation_vector_bytes)
        custom_transformation_translation_vector_new_values = [1.1, 2.2, 3.3]
        custom_transformation_translation_vector_new_bytes = struct.pack('3d', *custom_transformation_translation_vector_new_values)
        features.CustomTransformationTranslationVector.set(custom_transformation_translation_vector_new_bytes)
        robot_transformation_translation_vector_length = features.RobotTransformationTranslationVector.length
        robot_transformation_translation_vector_bytes = features.RobotTransformationTranslationVector.get(robot_transformation_translation_vector_length)
        robot_transformation_translation_vector = struct.unpack('3d', robot_transformation_translation_vector_bytes)
        robot_transformation_translation_vector_new_values = [1.1, 2.2, 3.3]
        robot_transformation_translation_vector_new_bytes = struct.pack('3d', *robot_transformation_translation_vector_new_values)
        features.RobotTransformationTranslationVector.set(robot_transformation_translation_vector_new_bytes)
        # True or False
        recognize_markers = features.RecognizeMarkers
        features.RecognizeMarkers.value = True
        # <-999999.0, 999999.0>
        marker_scale_width = features.MarkerScaleWidth
        features.MarkerScaleWidth.value = 0.50
        # <-999999.0, 999999.0>
        marker_scale_height = features.MarkerScaleHeight
        features.MarkerScaleHeight.value = 0.50


        ## Calibration settings
        # `Row0Col0`, `Row0Col1`, `Row0Col2`, `Row1Col0`, .. , `Row2Col2`
        camera_matrix_selector = features.CameraMatrixSelector.value
        features.CameraMatrixSelector.value = 'Row0Col1'
        # ReadOnly
        camera_matrix_value = features.CameraMatrixValue.value
        # Read as raw bytes array
        camera_matrix_length = features.CameraMatrix.length
        camera_matrix_bytes = features.CameraMatrix.get(camera_matrix_length)
        camera_matrix = struct.unpack('9d', camera_matrix_bytes)
        # <0, 13>
        distortion_coefficient_selector = features.DistortionCoefficientSelector.value
        features.DistortionCoefficientSelector.value = 3
        # ReadOnly
        distortion_coefficient_value = features.DistortionCoefficientValue.value
        # Read as raw bytes array
        distortion_coefficient_length = features.DistortionCoefficient.length
        distortion_coefficient_bytes = features.DistortionCoefficient.get(distortion_coefficient_length)
        distortion_coefficient = struct.unpack('14d', distortion_coefficient_bytes)

        focus_length = features.FocusLength.value
        pixel_length_width = features.PixelSizeWidth.value
        pixel_length_height = features.PixelSizeHeight.value

        if "Color" in device_features:   
            ## Color calibration settings         
            # `Row0Col0`, `Row0Col1`, `Row0Col2`, `Row1Col0`, .. , `Row2Col2`
            color_calibration_camera_matrix_selector = features.ColorCalibration_CameraMatrixSelector.value
            features.CameraMatrixSelector.value = 'Row0Col1'
            # ReadOnly
            color_calibration_camera_matrix_value = features.ColorCalibration_CameraMatrixValue.value
            # Read as raw bytes array
            color_calibration_camera_matrix_length = features.ColorCalibration_CameraMatrix.length
            color_calibration_camera_matrix_bytes = features.ColorCalibration_CameraMatrix.get(color_calibration_camera_matrix_length)
            color_calibration_camera_matrix = struct.unpack('9d', color_calibration_camera_matrix_bytes)
            # <0, 13>
            color_calibration_distortion_coefficient_selector = features.ColorCalibration_DistortionCoefficientSelector.value
            features.DistortionCoefficientSelector.value = 3
            # ReadOnly
            color_calibration_distortion_coefficient_value = features.ColorCalibration_DistortionCoefficientValue.value
            # Read as raw bytes array
            color_calibration_distortion_coefficient_length = features.ColorCalibration_DistortionCoefficient.length
            color_calibration_distortion_coefficient_bytes = features.ColorCalibration_DistortionCoefficient.get(color_calibration_distortion_coefficient_length)
            color_calibration_distortion_coefficient = struct.unpack('14d', color_calibration_distortion_coefficient_bytes)

            color_calibration_focus_length = features.ColorCalibration_FocusLength.value
            color_calibration_pixel_length_width = features.ColorCalibration_PixelSizeWidth.value
            color_calibration_pixel_length_height = features.ColorCalibration_PixelSizeHeight.value
            # `Row0Col0`, `Row0Col1`, `Row0Col2`, `Row1Col0`, .. , `Row2Col2`
            color_calibration_rotation_matrix_selector = features.ColorCalibration_RotationMatrixSelector.value
            features.ColorCalibration_RotationMatrixSelector = "Row0Col1"
            # ReadOnly
            color_calibration_rotation_matrix_value = features.ColorCalibration_RotationMatrixValue.value
            # Read/Write as raw bytes array    
            color_calibration_rotation_matrix_length = features.ColorCalibration_RotationMatrix.length
            color_calibration_rotation_matrix_bytes = features.ColorCalibration_RotationMatrix.get(color_calibration_rotation_matrix_length)
            color_calibration_rotation_matrix = struct.unpack('9d', color_calibration_rotation_matrix_bytes)
            # `X`, `Y` or `Z`
            color_calibration_translation_vector_selector = features.ColorCalibration_TranslationVectorSelector.value
            features.ColorCalibration_TranslationVectorSelector.value = "Y"
            # ReadOnly
            color_calibration_translation_vector_value = features.ColorCalibration_TranslationVectorSelector.value
            # Read/Write as raw bytes array    
            color_calibration_translation_vector_length = features.ColorCalibration_TranslationVector.length
            color_calibration_translation_vector_bytes = features.ColorCalibration_TranslationVector.get(color_calibration_translation_vector_length)
            color_calibration_translation_vector = struct.unpack('3d', color_calibration_translation_vector_bytes)

            color_calibration_camera_resolution_width = features.ColorCalibration_CameraResolutionWidth.value
            color_calibration_camera_resolution_height = features.ColorCalibration_CameraResolutionHeight.value


            ## Color settings
            # Choose ISO value from supported ISO values
            if features.ColorSettings_SupportedISOsSize.value > 0:
                # Select via selector supported value in range [0, listSize - 1]
                features.ColorSettings_SupportedISOsSelector.value = 0
                # Set selected value to the settings
                features.ColorSettings_ISO.value = features.ColorSettings_SupportedISO.value

            # Choose exposure value from supported exposure values
            if features.ColorSettings_SupportedExposuresSize.value > 0:
                # Select using selector supported value in range [0, listSize - 1]
                features.ColorSettings_SupportedExposuresSelector.value = 0
                # Set selected value to the settings
                features.ColorSettings_Exposure.value = features.ColorSettings_SupportedExposure.value

            # Choose value of camera resolution from supported capturing modes
            if features.ColorSettings_SupportedCapturingModesSize.value > 0:
                # Select via selector supported value in range [0, listSize - 1]
                features.ColorSettings_SupportedCapturingModesSelector.value = 0
                # Get selected values
                color_settings_capturing_mode_resolution_width = features.ColorSettings_SupportedCapturingModeResolutionWidth.value
                color_settings_capturing_mode_resolution_height = features.ColorSettings_SupportedCapturingModeResolutionHeight.value

            # `Res_3864_2192`, `Res_1932_1096` or `Res_1288_730`
            resolution = features.ColorSettings_Resolution.value
            features.ColorSettings_Resolution.value = 'Res_1932_1096'

            # Set required gamma value in range [0.0, 1.0]
            features.ColorSettings_Gamma.value = 1.0

            # Enable white balance if required (True, False)
            features.ColorSettings_WhiteBalanceEnabled.value = True
            # Set required white balance coefficients if required in range [0.0, 1.0]
            features.ColorSettings_WhiteBalanceR.value = 1.0
            features.ColorSettings_WhiteBalanceG.value = 1.0
            features.ColorSettings_WhiteBalanceB.value = 1.0

        ## FrameOutput settings
        # Enable/Disable transfer of spefific images (True or False)
        features.SendPointCloud.value = True
        features.SendNormalMap.value = True
        features.SendDepthMap.value = True
        features.SendConfidenceMap.value = True
        features.SendEventMap.value = True
        features.SendTexture.value = True
        features.SendColorCameraImage.value = True # Available only with "MotionCam-3D Color" variant

        # The ia object will automatically call the destroy method
        # once it goes out of the block.

    # The h object will automatically call the reset method
    # once it goes out of the block.
