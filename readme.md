[日本語版 README ](/README-ja.md)

## About

This is a QGIS plugin, which implements NoiseModelling (https://github.com/Universite-Gustave-Eiffel/NoiseModelling) and help estimate the health risks posed by (road traffic) noise.

## Features

This plugin can

- fetch geometries from OpenStreetMap, Shuttle Radar Topography Mission, and Vector Tiles (provided by the Geospatial Information Authority of Japan).
- predict sound levels using NoiseModelling.
- estimate health risks based on the predicted sound levels and expore-response relationships shown in the Environmental Noise Guidelines in European Region (WHO Regional Office for Europe).

## License

This plug-in complies with the GPL v3 license. 
Please see the LICENSE file for details.

License of the external program used by this plug-in:

- NoiseModelling: GPL v3
- OpenJDK: GPL v2 (Classpath Exception)

## How to install

To calculate the sound levels, NoiseModelling (https://noise-planet.org/noisemodelling.html) and Java implementation are needed.


### Using installer (Windows 10)

 Execute the installer (`installer/hrisk-setup.exe`). 
 The program can also install this plugin, as well as all the required components. 
 Environmental variables that are needed to execute NoiseModelling are also set. 

### Manual install

#### This plugin

Install from QGIS repo or Download all the files in the repository (https://gitlab.com/jtagusari/hrisk-noisemodelling) and save them in the QGIS plugin folder.

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

Specify area and fetch the geometries of roads and buildings in the area.
The algorithms are stored in `Fetch geometries (Global)` group.
In Japan, precised data (including population) can be obtained using the algorithms stored in `Fetch geometries (Ja)` group.

### Set information on the sound sources

Traffic volumes (light/medium/heavy vehicles during day/evening/night) or the sound power levels are set in the fields of road layer.
Required fields are set in the layer fetched in the previous procedure.

### Set receiver points

Set receiver points, such as the facades of the buildings.
The algorithms are stored in `Set receivers` group, which employs NoiseModelling algorithms implemented using Java.

### Calculate the sound levels

Calculate the sound levels using the algorithms stored in `Predict sound level` group.
Sound-level contours can also be created.
It employs NoiseModelling algorithms.

### Estimate health risks

The health risks are estimated using the sound level of each building, base-line risk level and exposure-response relationships.
The algorithms are stored in `Evaluate health risk` group.
The affected population can also be evaluated if each building has the population field.
