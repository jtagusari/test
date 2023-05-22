[日本語版 README ](/README-ja.md)

# H-RISK with NoiseModelling

## About

This is a QGIS plugin, which implements NoiseModelling (https://github.com/Universite-Gustave-Eiffel/NoiseModelling) and help estimate the health risks posed by (road traffic) noise.

## Features

This plugin can

- fetch geometries from OpenStreetMap, Shuttle Radar Topography Mission, and Vector Tiles (provided by the Geospatial Information Authority of Japan).
- predict sound levels using NoiseModelling, by executing the Java script (specified Java implementation is required).
- estimate health risks based on the predicted sound levels and expore-response relationships shown in the Environmental Noise Guidelines in European Region (WHO Regional Office for Europe).

At this moment, the operation of the plugin with NoiseModelling v4.0.2 is confirmed. (Not with v4.0.4)

## License

This plug-in complies with the GPL v3 license. 
Please see the LICENSE file for details.

License of the external program used by this plug-in:

- NoiseModelling: GPL v3
- OpenJDK: GPL v2 (Classpath Exception)

Note: This service uses the API function of the e-Stat (e-Stat), but the content of the service is not guaranteed by the government.

## How to install

Install QGIS (version >= 3.22.0) and install the plugin according to the following instruction.
Note that to calculate the sound levels, NoiseModelling (https://noise-planet.org/noisemodelling.html) and Java implementation are needed.

The installer (`installer/hrisk-setup.exe`) will help install required components including the present plugin.

### Using installer (Windows 10)

Execute the installer (`installer/hrisk-setup.exe`). 
The program can also install this plugin, as well as all the required components. 
Environmental variables that are needed to execute NoiseModelling are also set. 

### Manual install

#### This plugin

Install from QGIS repo (currently preparing) or download all the files in the repository (https://gitlab.com/jtagusari/hrisk-noisemodelling) and save them in the QGIS plugin folder.

#### NoiseModelling

1. Download No-GUI version of NoiseModelling (see https://github.com/Universite-Gustave-Eiffel/NoiseModelling/releases)
2. Save all the files in your PC (e.g. `C:\Program Files`)
3. Set environmental variable of `NOISEMODELLING_HOME` to the installed folder

#### Java

1. Check the requirements of NoiseModelling and obtain the required version of Java implementation
2. Save all the files in your PC (e.g. `C:\Program Files`)
3. Set environmental variable of `JAVA_FOR_NOISEMODELLING` to the installed folder. Note that `%JAVA_FOR_NOISEMODELLING%\bin\java.exe` exists.


## How to use

### Fetch the geometries

The user can fetch the geometries of roads and buildings using algorithms in `Fetch geometries` group.
In Japan, precised data (including population) can be obtained using algorithms in `Fetch geometries (Ja)` group.

To fetch geometries from OpenStreetMap, `QuickOSM` plugin (https://docs.3liz.org/QuickOSM/) is needed.
To fetch geometries from Shuttle Radar Topography Mission, user id and password of Earthdata Login (https://urs.earthdata.nasa.gov/users/new) is needed.

### Set information on the sound sources

Before calculating sound levels, the user must set traffic volumes (light/medium/heavy vehicles during day/evening/night) or the sound power levels, as the fields of road layer.
Required fields are already set in the layer fetched if the features are fetched using the algorithms in `Fetch geometries` group (previous procedure).
Or, the user can manually set the fields using algorithms in `Initialize features` group.

### Set receiver points

To set receiver points, algorithms in `Set receivers` group are available.
The algorithms, employing `NoiseModelling` algorithms, set receiver points, such as at the facades of the buildings and at delaunay grid points.

### Calculate the sound levels

The sound levels at receiver points can be calculate using algorithms stored in `Predict sound level` group, employing `NoiseModelling`.

### Estimate health risks

The user can assign the number of residents of each building and estimate health risks posed by the noise, using algorithms in `Evaluate health risk` group.

## How to uninstall

Delete the files and folders in `JAVA_FOR_NOISEMODELLING` and `NOISEMODELLING_HOME` paths and delete the environmental variables.
