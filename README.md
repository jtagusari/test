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

The installer (`installer/hrisk-setup.exe` or `Install required components` algorithm in `Configurations` group) will help install required components including the present plugin.

### Using installer (Windows 10)

Execute the installer and restart QGIS.
The program can also install this plugin, as well as all the required components. 
Environmental variables needed to execute NoiseModelling are also set. 

### Manual install

#### This plugin

Install from QGIS repo or download all the files in the repository (https://gitlab.com/jtagusari/hrisk-noisemodelling) and save them in the QGIS plugin folder.

#### NoiseModelling

1. Download No-GUI version of NoiseModelling (see https://github.com/Universite-Gustave-Eiffel/NoiseModelling/releases)
2. Save all the files in your PC (e.g. `C:\Program Files\NoiseModelling`)
3. Set environmental variable of `NOISEMODELLING_HOME` to the installed folder

#### Java

1. Check the requirements of NoiseModelling and obtain the required version of Java implementation
2. Save all the files in your PC (e.g. `C:\Program Files\Java`)
3. Set environmental variable of `JAVA_FOR_NOISEMODELLING` to the installed folder. Note that `%JAVA_FOR_NOISEMODELLING%\bin\java.exe` exists.


## Tutorial (Test the plugin)

Here is a tutorial (and the test) of this plugin.
Execute the following procedures using QGIS, where the sound levels and health risks in 1km2 area in Sapporo City (141.295,141.305,43.158,43.168 [EPSG:4326]) are estimated step-by-step.
The results are also stored in `tutorial` directory, by comparing which the functinality of the plugin can be tested.

### Fetch the geometries

With following procedures, roads, buildings, elevation points, and a raster containing population information are fetched.
If the parameters are unspecified, use the default values.

- Execute `Road centerline (OSM)` algorithm (in `Fetch geometries` group) using following parameters. Note that `QuickOSM` plugin is needed before the execution.
  - `FETCH_EXTENT`: 141.295,141.305,43.158,43.168 [EPSG:4326]
  - `TARGET_CRS`: EPSG: 32654
  - `BUFFER`: 500.0 (m)
- Execute `Building (OSM)` algorithm using following parameters:
  - `FETCH_EXTENT`: 141.295,141.305,43.158,43.168 [EPSG:4326]
  - `TARGET_CRS`: EPSG: 32654
  - `BUFFER`: 500.0
- Execute `Elevation points (SRTM)` algorithm using following parameters. Note that user id and password of Earthdata Login (https://urs.earthdata.nasa.gov/users/new) is needed before the execution.
  - `FETCH_EXTENT`: 141.295,141.305,43.158,43.168 [EPSG:4326]
  - `TARGET_CRS`: EPSG: 32654
  - `BUFFER`: 500.0
  - `USERNAME`: (registered user name)
  - `PASSWORD`: (registered password)
- Execute `Population (Ja)` algorithm (in `Fetch geometries (Ja)` group) using following parameters. Note that only the population in Japan can be fetched using this algorithm.
  - `FETCH_EXTENT`: 141.295,141.305,43.158,43.168 [EPSG:4326]
  - `TARGET_CRS`: EPSG: 32654
  - `BUFFER`: 500.0


If you want to obtain the information on roads and buildings and set them as sound sources and obstacles without this plugin, following procedures are needed (difficult!). 

1. Get the fetch extent as a rectangle
   1. Execute `native:extenttolayer` using the above `FETCH_EXTENT` as `INPUT` 
   2. Execute `native:reprojectlayer` using the output of the previous procedure as `INPUT` and the above `TARGET_CRS` as `TARGET_CRS`
   3. Execute `native:buffer` using the output of the previous procedure as `INPUT` and the above `BUFFER` as `DISTANCE`
2. Get the features from OpenStreetMap
   1. Execute `quickosm:downloadosmdataextentquery` using highway as `KEY` (if for buildings, building as `KEY`) and the extent of the obtained rectangle as the `EXTENT`
   2. Execute `native:reprojectlayer` using the output of the previous procedure as `INPUT` and the above `TARGET_CRS` as `TARGET_CRS`
   3. Execute `native:dissolve` using the output of the previous procedure as `INPUT` and the all the fields as `FIELD`
   4. Execute `native:multiparttosingleparts` using the output of the previous procedure as `INPUT`
3. Set required fields
   1. Add required fields to the road layer (`PK`,`LV_d`, `LV_e`, `LV_n`, `MV_d`, `MV_e`, `MV_n`, `HV_d`, `HV_e`, `HV_n`, `LV_spd_d`, `LV_spd_e`, `LV_spd_n`, `MV_spd_d`, `MV_spd_e`, `MV_spd_n`, `HV_spd_d`, `HV_spd_e`, `HV_spd_n`, `LWd63`, `LWd125`, `LWd250`, `LWd500`, `LWd1000`, `LWd2000`, `LWd4000`, `LWd8000`, `LWe63`, `LWe125`, `LWe250`, `LWe500`, `LWe1000`, `LWe2000`, `LWe4000`, `LWe8000`, `LWn63`, `LWn125`, `LWn250`, `LWn500`, `LWn1000`, `LWn2000`, `LWn4000`, `LWn8000`, `pvmt`, `temp_d`, `temp_e`, `temp_n`, `ts_stud`, `pm_stud`, `junc_dist`, `slope`, `way`)
   2. Add required fields to the building layer (`PK`,`height`)

### Set traffic volume

As an example, set following traffic volumes, for roads of which `osm_id` are `202548600` and `1128470753`

- `LV_d`: 1000
- `LV_e`: 400
- `LV_n`: 120
- `HV_d`: 140
- `HV_e`: 20
- `HV_n`: 20

### Set receivers (at building facade)

- Execute `Building facade` algorithm in `Set receiver` group using following parameters. Receiver points in front of the buildings are created using algorithms implemented in `NoiseModelling`. Note that `NoiseModelling` and `Java` are needed before the execution (see "How to install" section)
  - `BUILDING`: (buildings fetched in the previous procedure)
  - `SOURCE`: (roads fetched in the previous procedure)
  - `FENCE_EXTENT`: 141.295,141.305,43.158,43.168 [EPSG:4326]
  - `DELTA`: 2.0

The receivers at buildings facade are used to estimate health risks posed by noise exposure.

### Set receivers (at delaunay grid)

- Execute `Delaunay grid` algorithm in `Set receiver` group using following parameters.
  - `BUILDING`: (buildings fetched in the previous procedure)
  - `SOURCE`: (roads fetched in the previous procedure)
  - `FENCE_EXTENT`: 141.295,141.305,43.158,43.168 [EPSG:4326]
  - `MAX_AREA`: 100.0

The receivers at delaunay grid points are used to create sound-level contours.
The delaunay triangular polygons, which is one of the outputs of the procedure, are also needed for creating sound-level contour.

### Calculate sound levels

- Execute `Prediction from traffic` algorithm in `Predict sound level` group using following parameters. The sound levels are computed using algorithms implemented in `NoiseModelling`.
  - `ROAD`: (roads fetched in the previous procedure)
  - `BUILDING`: (buildings fetched in the previous procedure)
  - `RECEIVER`: (receiver points created in the previous procedure)
  - `DEM`: (elevation points fetched in the previous procedure)
  - `MAX_SRC_DIST`: 500

### Create sound-level contour (delaunay-grid receivers)

- Execute `Isosurface` algorithm in `Predict sound level` group using following parameters. The sound-level counters are computed using algorithms implemented in `NoiseModelling`. As an example, Lden contour is created.
  - `LEVEL_RESULT`: (Lden computed in the previous procedure, using delaunay grid)
  - `LEVEL_RID`: IDRECEIVER
  - `LEVEL_LID`: LAEQ
  - `TRIANGLES`: (delaunay triangles obtained in the previous procedure)

### Estimate health risks (building-facade receivers)

- Execute `Estimate populations of buildings using Raster` algorithm in `Evaluate health risk` group using following parameters.
  - `BUILDING`: (buildings fetched in the previous procedure)
  - `POPULATION`: (population fetched in the previous procedure)
- Execute `Estimate level of buildings` algorithm using following parameters (assign Lden)
  - `BUILDING`: (buildings with population information obtained in the previous procedure)
  - `BUILDING_BID`: PK
  - `RECEIVER`: (receivers at buildings facade obtained in the previous procedure)
  - `RECEIVER_BID`: BUILD_PK
  - `RECEIVER_RID`: PK
  - `LEVEL`: (Lden at buildings facade, obtained in the previous procedure)
  - `LEVEL_RID`: IDRECEIVER
  - `LEVEL_ASSIGN`: LAEQ
  - `LEVEL_PREFIX`: Lden_
- Execute `Estimate level of buildings` algorithm using following parameters (assign Lnight)
  - `BUILDING`: (buildings with population and Lden, obtained in the previous procedure)
  - `BUILDING_BID`: PK
  - `RECEIVER`: (receivers at buildings facade obtained in the previous procedure)
  - `RECEIVER_BID`: BUILD_PK
  - `RECEIVER_RID`: PK
  - `LEVEL`: (Lnight at buildings facade obtained in the previous procedure)
  - `LEVEL_RID`: IDRECEIVER
  - `LEVEL_ASSIGN`: LAEQ
  - `LEVEL_PREFIX`: Lnight_
- Execute `Estimate health risks of buildings` algorithm using following parameters
  - `BUILDING`: (buildings with population and sound level, obtained in the previous procedure)
  - `LDEN`: Lden_LAEQ_Maximum
  - `LNIGHT`: Lnight_LAEQ_Maximum
  - `POP`: popEst

## How to use

### Fetch the geometries

The user can fetch the geometries of roads and buildings using algorithms in `Fetch geometries` group.
In Japan, precised data (including population) can be obtained using algorithms in `Fetch geometries (Ja)` group.

The algorithms are:

- `Fetch geometries` group
  - Road centerline (OSM) (`fetchosmroad.py`): fetch road geometries from OpenStreetMap. `QuickOSM` is needed.
  - Building (OSM) (`fetchosmbuilding.py`): fetch building geometries from OpenStreetMap. `QuickOSM` is needed.
  - Elevation points (SRTM) (`fetchsrtmdem.py`): fetch elevation-points geometries from Shuttle Radar Topography Mission dataset. User id and password of Earthdata Login (https://urs.earthdata.nasa.gov/users/new) is needed.
- `Fetch geometries (Ja)` group
  - Road centerline (Ja) (`fetchjaroad.py`): fetch road geometries from vector-tile map provided by the GSI of Japan
  - Buildings (Ja) (`fetchjabuilding.py`): fetch building geometries from vector-tile map provided by the GSI of Japan
  - Elevation points (Ja) (`fetchjadem.py`): fetch elevation-points geometries from vector-tile map provided by the GSI of Japan
  - Population (Ja) (`fetchjapop.py`): fetch 250m-mesh population from the ESTAT-API of Japan
  - Fetch geometries (Ja) (`fetchjageom.py`): fetch all geometries listed above (and also set receivers, if specified)

Note that `QuickOSM` plugin (https://docs.3liz.org/QuickOSM/) is needed to fetch geometries from OpenStreetMap.
To fetch geometries from Shuttle Radar Topography Mission, user id and password of Earthdata Login (https://urs.earthdata.nasa.gov/users/new) is needed.

### Set information on the sound sources

Before calculating sound levels, the user must set traffic volumes (light/medium/heavy vehicles during day/evening/night) or the sound power levels, as the fields of road layer.
Required fields are already set in the layer fetched if the features are fetched using the algorithms in `Fetch geometries` group (previous procedure).
Or, the user can manually set the fields using algorithms in `Initialize features` group.

The algorithms in `Initialize features` group are:

- Road with acoustic information (`initroad.py`): initialize linestrings as roads
- Road emission calculated from traffic (`initroademissionfromtraffic.py`): calculate the emission level (sound power level) using the traffic volume
- Building (`initbuilding.py`): initialize polygons as buildings
- Elevation point (`initelevationpoint.py`): initialize points as elevation points
- Ground absorption (`initgroundabsorption.py`): initialize polygons as ground absorption


### Set receiver points

To set receiver points, algorithms in `Set receivers` group are available.
The algorithms, employing `NoiseModelling` algorithms, set receiver points, such as at the facades of the buildings and at delaunay grid points.


The algorithms in `Set receiver` group are:

- At building facade (`receiverfacade.py`): create receivers at building facades
- Delaunay grid (`receiverdelaunaygrid.py`): create receivers at delaunay grid points
- Regular grid (`receiverregulargrid.py`): create receivers at regular grid points

### Calculate the sound levels

The sound levels at receiver points can be calculate using algorithms stored in `Predict sound level` group, employing `NoiseModelling`.

The algorithms in `Predict sound level` group are:

- Prediction from traffic (`noisefromtraffic.py`): calculate the sound levels from traffic volume
- Prediction from emission (`noisefromemission.py`): calculate the sound levels from the sound power level

### Estimate health risks

The user can assign the number of residents of each building and estimate health risks posed by the noise, using algorithms in `Evaluate health risk` group.

The algorithms in `Evaluate health risk` group are:

- Estimate populations of buildings using Raster (`estimatepopulationofbuilding.py`): estimate the number of residents for each building using a raster representing the population
- Estimate populations of buildings using Polygon (`estimatepopulationofbuildingplg.py`): estimate the number of residents for each building using polygons representing the population
- Estimate level of buildings (`estimatelevelofbuilding.py`): estimate the sound level for each building
- Estimate health risks of buildings (`estimateriskofbuilding.py`): estimate the health risks for each building

### For developers

There are several scripts for developers, as follows:

- `algabstract`: an abstract class inheriting `QgsProcessingAlgorithm`, defining attributes and methods
  - attributes
    - `PARAMETERS`: to set UIs.
    - `NOISEMODELLING`: to use NoiseModelling, such as paths and arguments.
  - methods
    - `initParameters(self) -> None`: convert `PARAMETERS` attributes to UIs.
    - `initNoiseModellingPath(self, paths:dict) -> None`: set NoiseModelling paths.
    - `initNoiseModellingArg(self, parameters:dict, context: QgsProcessingContext, feedback:QgsProcessingFeedback) -> None`: initialize NoiseModelling arguments from UIs.
    - `addNoiseModellingArg(self, args:dict) -> None`: add NoiseModelling arguments.
    - `saveVectorLayer(self, vector_layer: QgsVectorLayer, path: str) -> None)`: save a vector layer.
    - `saveRasterLayer(self, raster_layer: QgsVectorLayer, path: str) -> None)`: save a raster layer.
    - `execNoiseModellingCmd(self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback) -> None`: exec NoiseModelling.
    - `streamNoiseModellingCmd(self, cmd: str, feedback: QgsProcessingFeedback) -> None`: stream NoiseModelling
    - `importNoiseModellingResultsAsSink(self, parameters: dict, context: QgsProcessingContext, attribute: str, path: str) -> None`: import NoiseModelling results as a sink
- `fetchabstract`: an abstract class inheriting `algabstract`, defining attributes and methods
  - attributes
    - `FETCH_AREA`: the fetch area (`QgsReferencedRectangle`)
    - `TILEMAP_ARGS`: arguments for tile-map
    - `OSM_ARGS`: arguments for OpenStreetMap
    - `WEBFETCH_ARGS`: arguments for fetching geometries from web without tile-map or OpenStreetMap
  - methods
    - `initUsingCanvas(self) -> None`: set `FETCH_EXTENT` and `TARGET_CRS` to the current canvas settings
    - `getUtmCrs(self, lng: float, lat: float) -> QgsCoordinateReferenceSystem`: get Universal Transverse Melcator CRS
    - `setFetchArea(self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback, new_crs: QgsCoordinateReferenceSystem = None) -> None`: set the `FETCH_AREA` attribute
    - `fetchAreaAsVectorLayer(self) -> QgsVectorLayer` get a vector layer from the `FETCH_AREA` attribute
    - `setTileMapArgs(self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback, geom_type: str = None) -> None`: set the arguments for tile maps.
    - `setOsmArgs(self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback, geom_type: str=None) -> None`: set the arguments for OpenStreetMap.
    - `setWebFetchArgs(self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback) -> None`: set the arguments for fetching geometries from web (but not tile maps or OpenStreetMap)
    - `fetchFeaturesFromTile(self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback) -> None`: fetch features from tile maps
    - `fetchFeaturesFromOsm(self, parameters:dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback) -> None`: fetch features from OpenStreetMap
    - `fetchFeaturesFromWeb(self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback) -> None`: fetch features from web (but not tile maps or OpenStreetMap). Note that the fetched features are stored just as files
    - `modifyFeaturesFromTile(self, fts: QgsVectorLayer | QgsRasterLayer, z: int, tx: int, ty: int)- > QgsVectorLayer | QgsRasterLayer`: modify features fetched from tile maps
    - `dissolveFeatures(self, fts: QgsVectorLayer) -> QgsVectorLayer`: dissolve features
    - `transformToTargetCrs(self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback, fts: QgsVectorLayer) -> QgsVectorLayer`: transform features (to the `TARGET_CRS`)
- `initabstract`: an abstract class inheriting `algabstract`, defining attributes and methods
  - attributes
    - `FIELDS_ADD`: the fields to be initialized
    - `FIELDS_INIT`: the existing fields and `FIELDS_ADD`
    - `FIELDS_FROM`: whether each field existed or in `FIELDS_ADD`
  - methods
    - `setFields(self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback) -> None`: set `FIELDS_INIT` and `FIELDS_FROM`
    - `createVectorLayerAsSink(self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback) -> str`: create a sink using the fields and return `dest_id`
- `noiseabstract`: an abstract class inheriting `algabstract`, defining attributes and methods
  - attributes
    - `BLDG_LEVEL_ARGS`: arguments to assign the sound level to each building
    - `ISOSURFACE_ARGS`: arguments to create isosurface
    - `PROC_RESULTS`: results of the calculation
  - methods
    - `outputWpsArgs(self, parameters:dict, context:QgsProcessingContext, extent_rec: QgsReferencedRectangle) -> str`: output a polygon (sink and output the `dest_id`) that stores arguments of the calculation
    - `cmptBuildingLevel(self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback, bldg_layer: QgsVectorLayer, rcv_layer: QgsVectorLayer) -> None`: create sound-level-assigned buildings
- `worldmesh.py`: used for obtaining the world mesh code (from Research Institute for World Grid Squares)

## How to uninstall

Delete the files and folders in `JAVA_FOR_NOISEMODELLING` and `NOISEMODELLING_HOME` paths and delete the environmental variables.
