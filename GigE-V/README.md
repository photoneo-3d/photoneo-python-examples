# Photoneo GigE Vision examples

This folder contains examples for interacting with Photoneo 3D Sensors through
the GigE Vision protocol.

⚠️
These examples require PhoXi firmware version 1.13.0.
⚠️

## GenICam Features

When using a GigE Vision framework, most of the interaction with the device will
take place using GenICam features. Photoneo 3D Sensors implement standard
features for acquisition control, component selection and others.  All settings
available through PhoXiAPI to configure the Sensors are also available as
GenICam features.

Most GenICam / GigE Vision frameworks or software contain tools or UI elements
to list and examine these features (such as the arv-tool command from the aravis
project).

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

The components available through GigE Vision generally match the outputs
available in PhoXiAPI with some differences in data representation. Note that
some features (for example point cloud coordinate transformations) are
implemented by PhoXiControl / PhoXiAPI on the client computer and thus not
available through GigE Vision.

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

When multiple components are selected, these are transferred using a multi-part
payload. Multi-part payloads provide meta-data (dimensions, data type, pixel
format) for each component and also an ID used to identify actual components
(data purpose ID on GigE Vision layer, component ID on GenTL layer). The
component IDs to match against the ones provided in the multipart data can be
retrieved using the ComponentIDValue feature, i.e.:

    ComponentSelector = "Range"
    rangeComponentId = ComponentIDValue

Some frameworks don't expose the component IDs for the received parts. To allow
identifying the parts in such cases, the parts are always sent in the same
order of increasing component ID values (see the
[python harvesters example](https://github.com/photoneo-3d/photoneo-python-examples/blob/main/GigEV/harvesters/advanced/connect_grab_save.py#L63-L66)
for a way on how this can be used to identify the parts.)

### Intensity

The `Intensity` component contains the texture image depending on the
`TextureSource` or `CameraTextureSource` setting. The pixel format is `Mono10`
or `Mono12` for monochromatic textures (`Laser` or `Led`), depending on the
device, or one of `RGB8` or `Mono16` for color textures.

#### Color texture

When `Color` is selected as the texture source on an appropriate device, the
`Intensity` component contains the color texture. There are two available pixel
formats:

- `RGB8` (default).

- `Mono16`. This pixel format uses a custom YCoCg encoding that encodes the
  color data in the lowest bits of the intensity.This allows for faster transfer
  speeds while allowing the reconstruction of 10 bit RGB information.
  See
  [`common/YCoCg.h`](https://github.com/photoneo/photoneo-cpp-examples/tree/main/GigEVision/aravis/common/YCoCg.h)
  in C++ examples for more details on the encoding and an example implementation.


### Range

The `Range` component contains the point cloud data or a depth map depending on
the value of the `Scan3dOutputMode` feature.  As with all other components except
`ColorCamera` image, the dimensions are the same as the intensity (texture)
component and the points match 1:1 with those. See PhoXi Control manual for more
details.

The exact contents depends on the chosen `Scan3dOutputMode`:

- `CalibratedABC_Grid` (default) contains directly the `X` / `Y` / `Z`
  coordinates of each point organized in a grid that matches pixels in the other
  components (i.e. `Intensity`) so that 3D data and color / intensity
  information can be paired easily.

- `ProjectedC` contains only the `Z` (depth) measurements for each point, but
  the `X` / `Y` coordinates can be calculated by the client using [static
  coordinate maps](#static-coordinate-maps).

### Confidence

The `Confidence` component contains confidence information for each 3D point in
the `Confidence8` format. Note that this format (0 - invalid, 255 - max
confidence) is different from the confidence values in PhoXi Control.

### Normal

The `Normal` component contains the normal vectors for each point. Two
pixel format representations are available:

- `Coord3D_ABC32f` (default) - the `X` / `Y` / `Z` coordinates of the normal
  vector directly.

- `Coord3D_AC8` - a compact two byte representation for faster transfer speeds
  that encodes the normals as two 8 bit numbers represented in spherical
  coordinates. See the [C++ examples](https://github.com/photoneo-3d/photoneo-cpp-examples/blob/main/GigEV/aravis/common/CalculateNormals.h)
  for an example on how to convert to x,y,z coordinates.

Note: `NormalsEstimationRadius` must be non-zero for normals to be calculated.
See [PhoXi Control manual](http://www.photoneo.com/kb/pxc) for more details.

### Event

The `Event` component contains the event map. See PhoXi Control manual for more
information.

### ColorCamera

The `ColorCamera` component contains the image from the RGB camera unit. It is
encoded the same way as [color texture](#color-texture) but will usually have a
different size than the other components.

See [PhoXi Control manual](http://www.photoneo.com/kb/pxc) for more details on
how to reproject the Range (depth map) data into the perspective of the color
camera unit and obtain the direct mapping also between the full ColorCamera
image and the point cloud information via `CameraSpace` feature.

### Static coordinate maps

Static coordinate maps can be used to convert the depth data from `Range`
component into actual 3D points in `ProjectedC` mode.

These maps (and the related parameters) can change when certain settings are
changed, but stay the same if settings are not changed. This means that they
need to be retrieved only once after a settings change and can then be cached
and used to transform only range (Z) data into a point cloud thus improving
transfer speeds.

The `CoordinateMapA` and `CoordinateMapB` components can be used together with
the `Scan3dFocalLength`, `Scan3dAspectRatio`, `Scan3dPrincipalPointU` and
`Scan3dPrincipalPointV` features can be used as follows to calculate the x,y,z
coordinates:

To calculate the `X` / `Y` / `Z` coordinates, the `CoordinateMapA` and
`CoordinateMapB` components can be used together with the `Scan3dFocalLength`,
`Scan3dAspectRatio`, `Scan3dPrincipalPointU` and `Scan3dPrincipalPointV`
features as follows:

    for row in height:
        for col in width:
            pcl[row,col].x = range[row,col] * (coordMapA[row,col]-Scan3dPrincipalPointU)/Scan3dFocalLength
            pcl[row,col].y = range[row,col] * (coordMapB[row,col]-Scan3dPrincipalPointV)/(Scan3dFocalLength*Scan3dAspectRatio)
            pcl[row,col].z = range[row,col]

See the examples for actual code samples.
