# Photoneo GigE Vision examples

This folder contains examples for interacting with Photoneo 3D Sensors through
the GigE Vision protocol.

## GenICam Features

When using a GigE Vision framework, most of the interaction with the device will
take place using GenICam features. Photoneo 3D Sensors implement standard
features for acquisition control, component selection and others.  All settings
available through PhoXiAPI to configure the Sensors are also available as
GenICam features.

Most GenICam / GigE Vision frameworks or software contains tools or UI elements
to list and examine these features (such as the arv-tool command from the aravis
project.)

## Continuous acquisition (freerun), software and hardware trigger

While there are standard GenICam commands for acquisition control
(`AcquisitionStart`, `AcquisitionStop` etc.) most frameworks provide dedicated
interfaces to actually control the acquisition. See the respective examples for
particular framework.

The only supported `AcquisitionMode` is `Continuous` (i.e. "freerun".) Software
and hardware trigger are available through the `TriggerMode[TriggerSelector]` and
`TriggerSource[TriggerSelector]` features.

Note: currently only the `FrameStart` trigger is supported, so technically the
`TriggerSelector = FrameStart` lines could be left out from the following
examples, though it is safer to include them in case other triggers are added in
later releases.

To set up software trigger, configure the features as follows:

    TriggerSelector = FrameStart
    TriggerMode = On
    TriggerSource = Software

Afterwards start the acquisition normally and use the `TriggerSoftware` command
to trigger a frame:

    TriggerSoftware.Execute()

To set up hardware trigger, configure the device similarly with `TriggerSource`
set to `Line1`:

    TriggerSelector = FrameStart
    TriggerMode = On
    TriggerSource = Line1

## Components

The components available through GigE Vision generally match the outputs available
in PhoXiAPI with some differences in data representation due to network
transfer efficiency (i.e. point cloud data is not transferred and must be
calculated from the depth data, color images are transferred in a more space
efficient format etc.).

### Selecting components

Enabling and disabling of components is performed through the
`ComponentSelector` and `ComponentEnable` standard features.

For example to enable the `Intensity` and `Range` components and to disable the
`ColorCamera` component one must execute the following feature assignments:

    ComponentSelector = "Intensity"
    ComponentEnable = True

    ComponentSelector = "Range"
    ComponentEnable = True

    ComponentSelector = "ColorCamera"
    ComponentEnable = False

### Retrieving components

When multiple components are selected, these are transferred either using
a multi-part payload or using chunks. This should be auto-negotiated by the
framework / library (preferring multi-part if supported), but some frameworks
provide an interface to select the actual method used.

#### Multipart

Multi-part payloads provide meta-data (dimensions, data type, pixel format) for
each component and also an ID used to identify actual components
(data purpose ID on GigE Vision layer, component ID on GenTL layer.) The
component IDs to match against the ones provided in the multipart data can be
retrieved using the ComponentIDValue feature, i.e.:

    ComponentSelector = "Range"
    rangeComponentId = ComponentIDValue

Some frameworks don't expose the component IDs for the received parts. To allow
identifying the parts in such cases, the parts are always sent in the same
order of increasing component ID values (see the python harvesters example for a
way on how this can be used to identify the parts.)

#### Chunked data

In chunked data mode the `Intensity` component is always transferred as the Image
payload and the other components are transferred as additional chunks. If the
`Intesity` component is not enabled, then the Chunk data payload is used (and
thus contains only the chunks for the enabled components.)

Chunks are identified by a chunk ID which is set equal to the component ID
value and thus can be identified through that. Chunk data does not include any
meta-data and thus the dimensions and data format must be derived from the chunk
ID.

### Intensity

The `Intensity` component contains the texture depending on the `TextureSource` or
`CameraTextureSource` setting. The pixel format is always `Mono16` even though
it may contain data with lower bit depth depending on the chosen source.

#### Color texture

When `Color` is selected as `TextureSource` on an appropriate device, the
`Intensity` component contains the color texture. The data is still transferred
using `Mono16` as pixel format, however it uses a custom YCoCg encoding which
encodes the color data in the lowest bits of the intensity. See
[`common/YCoCg.h`](https://github.com/photoneo-3d/photoneo-cpp-examples/blob/main/GigEV/aravis/common/YCoCg.h)
in C++ examples for more details on the encoding and an example implementation.

### Range

The `Range` component contains the depth map. As with all other components except
ColorCamera image, the dimensions are the same as the intensity (texture)
component and the points match 1:1 with those. See PhoXi Control manual for more
details.

### Confidence

The `Confidence` component contains confidence map. See PhoXi Control manual for
more details.

### Normal

The `Normal` component contains the normal vectors for each point. Unlike
PhoXiAPI, the normals are transferred as two 8 bit numbers represented in
spherical coordinates. See the C++ examples for an example on how to convert to
x,y,z coordinates.

Note: `NormalsEstimationRadius` must be non-zero for normals to be calculated.

### Event

The `Event` component contains the event map. See PhoXi Control manual for more
information.

### ColorCamera

The `ColorCamera` component contains the image from the RGB camera unit. It is
transferred as `Mono16` and encoded the same way as [color texture](#color-texture).

### Reprojection

The `Reprojection` component contains the reprojection map that can be used to
convert the depth data from `Range` component into actual 3D points (see
PhoXi Control manual for more information.)

The reprojection map can change when certain settings are changed, but stays the
same if settings are not changed. This means that it needs to be retrieved only
once a after a settings change and can then be cached and used to transform
depth data into a point cloud.

The reprojection map is transferred as two floating point numbers per pixel: the
`x` and `y` coordinates, while `z` is fixed to 1. The following examples shows
how to calculate the point cloud from the depth and reprojection map:

    for row in height:
        for col in width:
            pcl[row,col].x = depth[row,col] * reprojection[row,col].x
            pcl[row,col].y = depth[row,col] * reprojection[row,col].y
            pcl[row,col].z = depth[row,col]

See the examples or PhoXi Control manual for actual code samples.
