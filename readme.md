[日本語版 README はこちら](/README-ja.md)

## About

This is a QGIS plugin, which implements NoiseModelling (https://github.com/Universite-Gustave-Eiffel/NoiseModelling) and help estimate the health risks posed by (road traffic) noise.

## Features

This plugin can
- fetch geometries from OpenStreetMap, Shuttle Radar Topography Mission, and Vector Tiles (provided by the Geospatial Information Authority of Japan).
- predict sound levels using NoiseModelling.
- estimate health risks based on the predicted sound levels and expore-response relationships shown in the Environmental Noise Guidelines in European Region (WHO Regional Office for Europe).

## How to install

### Required components to execute the plugin

- Java implementation (required by NoiseModelling)
- NoiseModelling
- H-RISK

### Using installer (Windows 10)

1. Download and install QGIS (https://qgis.org/).
2. Download and execute `installer/hrisk-setup.exe`.
3. All the required components are installed.
4. Activate the plugin in QGIS.

### Manual install

1. Download and install QGIS (https://qgis.org/).
2. Download all the files in this repository and save them in QGIS pluin path.
3. Install Java implementation (see the requirements of NoiseModelling)
4. Set the install folder as an environmental variable `JAVA_FOR_NOISEMODELLING`
5. Install NoiseModelling (without-gui version)
6. Set the install folder as an environmental variable `NOISEMODELLING_HOME`


