import org.h2gis.api.ProgressVisitor
import org.slf4j.Logger
import org.slf4j.LoggerFactory
import java.sql.Connection
import java.nio.file.Path;
import java.nio.file.Paths;

title = 'Calculation of road traffic noise'
description = 'Sound levels at receivers are calculated using information on road (including geometry and traffic conditions), buildings, etc.'

inputs = [
  roadGeomPath:[
    name : "Path of the road file",
    title : "Path of the road file",
    description : "Path of the road file",
    type : String.class
  ],
  buildingGeomPath:[
    name : "Path of the building file",
    title : "Path of the building file",
    description : "Path of the building file",
    type : String.class
  ],
  receiverGeomPath:[
    name : "Path of the receiver file",
    title : "Path of the receiver file",
    description : "Path of the receiver file",
    type : String.class
  ],
  demGeomPath:[
    name : "Path of the dem file",
    title : "Path of the dem file",
    description : "Path of the road file",
    min        : 0, max: 1,
    type : String.class
  ],
  groundAbsGeomPath:[
    name : "Path of the ground absorption file",
    title : "Path of the ground absorption file",
    description : "Path of the ground absorption file",
    min        : 0, max: 1,
    type : String.class
  ],
  inputSRID: [
    name: 'Projection identifier',
    title: 'Projection identifier',
    description: 'Original projection identifier (also called SRID) of your table. It should be an EPSG code, a integer with 4 or 5 digits (ex: 3857 is Web Mercator projection). ' +
            '</br>  All coordinates will be projected from the specified EPSG to WGS84 coordinates. ' +
            '</br> This entry is optional because many formats already include the projection and you can also import files without geometry attributes.</br> ' +
            '</br> <b> Default value : 4326 </b> ',
    type: Integer.class,
    min: 0, max: 1
  ],
  paramWallAlpha          : [
    name       : 'wallAlpha',
    title      : 'Wall absorption coefficient',
    description: 'Wall absorption coefficient (FLOAT between 0 : fully absorbent and strictly less than 1 : fully reflective)' +
            '</br> </br> <b> Default value : 0.1 </b> ',
    min        : 0, max: 1,
    type       : String.class
  ],
  confReflOrder           : [
    name       : 'Order of reflexion',
    title      : 'Order of reflexion',
    description: 'Maximum number of reflections to be taken into account (INTEGER).' +
            '</br> </br> <b> Default value : 1 </b>',
    min        : 0, max: 1,
    type       : String.class
  ],
  confMaxSrcDist          : [
    name       : 'Maximum source-receiver distance',
    title      : 'Maximum source-receiver distance',
    description: 'Maximum distance between source and receiver (FLOAT, in meters).' +
            '</br> </br> <b> Default value : 150 </b>',
    min        : 0, max: 1,
    type       : String.class
  ],
  confMaxReflDist         : [
    name       : 'Maximum source-reflexion distance',
    title      : 'Maximum source-reflexion distance',
    description: 'Maximum reflection distance from the source (FLOAT, in meters).' +
            '</br> </br> <b> Default value : 50 </b>',
    min        : 0, max: 1,
    type       : String.class
  ],
  confThreadNumber        : [
    name       : 'Thread number',
    title      : 'Thread number',
    description: 'Number of thread to use on the computer (INTEGER).' +
            '</br> To set this value, look at the number of cores you have.' +
            '</br> If it is set to 0, use the maximum number of cores available.' +
            '</br> </br> <b> Default value : 0 </b>',
    min        : 0, max: 1,
    type       : String.class
  ],
  confDiffVertical        : [
    name       : 'Diffraction on vertical edges',
    title      : 'Diffraction on vertical edges',
    description: 'Compute or not the diffraction on vertical edges.Following Directive 2015/996, enable this option for rail and industrial sources only.' +
            '</br> </br> <b> Default value : false </b>',
    min        : 0, max: 1,
    type       : Boolean.class
  ],
  confDiffHorizontal      : [
    name       : 'Diffraction on horizontal edges',
    title      : 'Diffraction on horizontal edges',
    description: 'Compute or not the diffraction on horizontal edges.' +
            '</br> </br> <b> Default value : false </b>',
    min        : 0, max: 1,
    type       : Boolean.class
  ],
  confSkipLday            : [
    name       : 'Skip LDAY_GEOM table',
    title      : 'Do not compute LDAY_GEOM table',
    description: 'Skip the creation of this table.' +
            '</br> </br> <b> Default value : false </b>',
    min        : 0, max: 1,
    type       : Boolean.class
  ],
  confSkipLevening        :[
    name       : 'Skip LEVENING_GEOM table',
    title      : 'Do not compute LEVENING_GEOM table',
    description: 'Skip the creation of this table.' +
            '</br> </br> <b> Default value : false </b>',
    min        : 0, max: 1, type: Boolean.class
  ],
  confSkipLnight          : [
    name       : 'Skip LNIGHT_GEOM table',
    title      : 'Do not compute LNIGHT_GEOM table',
    description: 'Skip the creation of this table.' +
            '</br> </br> <b> Default value : false </b>',
    min        : 0, max: 1, type: Boolean.class
  ],
  confSkipLden            : [
    name       : 'Skip LDEN_GEOM table',
    title      : 'Do not compute LDEN_GEOM table',
    description: 'Skip the creation of this table.' +
            '</br> </br> <b> Default value : false </b>',
    min        : 0, max: 1, type: Boolean.class
  ],
  confExportSourceId      : [
    name       : 'keep source id',
    title      : 'Separate receiver level by source identifier',
    description: 'Keep source identifier in output in order to get noise contribution of each noise source.' +
            '</br> </br> <b> Default value : false </b>',
    min        : 0, max: 1, type: Boolean.class
  ],
  confHumidity            : [
    name       : 'Relative humidity',
    title      : 'Relative humidity',
    description: 'Humidity for noise propagation, default value is <b>70</b>',
    min        : 0, max: 1, type: Double.class
  ],
  confTemperature         : [
    name       : 'Temperature',
    title      : 'Air temperature',
    description: 'Air temperature in degree celsius, default value is <b>15</b>',
    min        : 0, max: 1, type: Double.class
  ],
  confFavorableOccurrencesDay: [
    name       : 'Probability of occurrences (Day)',
    title      : 'Probability of occurrences (Day)',
    description: 'comma-delimited string containing the probability of occurrences of favourable propagation conditions.' +
            'The north slice is the last array index not the first one<br/>' +
            'Slice width are 22.5&#176;: (16 slices)<br/><ul>' +
            '<li>The first column 22.5&#176; contain occurrences between 11.25 to 33.75 &#176;</li>' +
            '<li>The last column 360&#176; contains occurrences between 348.75&#176; to 360&#176; and 0 to 11.25&#176;</li></ul>Default value <b>0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5</b>',
    min        : 0, max: 1,
    type       : String.class
  ],
  confFavorableOccurrencesEvening: [
    name       : 'Probability of occurrences (Evening)',
    title      : 'Probability of occurrences (Evening)',
    description: 'comma-delimited string containing the probability of occurrences of favourable propagation conditions.' +
            'The north slice is the last array index not the first one<br/>' +
            'Slice width are 22.5&#176;: (16 slices)<br/><ul>' +
            '<li>The first column 22.5&#176; contain occurrences between 11.25 to 33.75 &#176;</li>' +
            '<li>The last column 360&#176; contains occurrences between 348.75&#176; to 360&#176; and 0 to 11.25&#176;</li></ul>Default value <b>0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5</b>',
    min        : 0, max: 1,
    type       : String.class
  ],
  confFavorableOccurrencesNight: [
    name       : 'Probability of occurrences (Night)',
    title      : 'Probability of occurrences (Night)',
    description: 'comma-delimited string containing the probability of occurrences of favourable propagation conditions.' +
            'The north slice is the last array index not the first one<br/>' +
            'Slice width are 22.5&#176;: (16 slices)<br/><ul>' +
            '<li>The first column 22.5&#176; contain occurrences between 11.25 to 33.75 &#176;</li>' +
            '<li>The last column 360&#176; contains occurrences between 348.75&#176; to 360&#176; and 0 to 11.25&#176;</li></ul>Default value <b>0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5</b>',
    min        : 0, max: 1,
    type       : String.class
  ],
  confRaysName            : [
    name       : 'Export propagation ray',
    title      : 'Export propagation ray',
    description: 'Save each propagation ray into the specified table (ex:RAYS) ' +
            'or file URL (ex: file:///Z:/dir/map.kml)' +
            'You can set a table name here in order to save all the rays computed by NoiseModelling' +
            '. The number of rays has been limited in this script in order to avoid memory exception' +
            '</br> <b> Default value : empty (do not keep rays) </b>',
    min        : 0, max: 1, type: String.class
  ],
  exportDir : [
    name: "Path of export directory",
    title: "Path of export directory",
    description: "Path of export directory",
    min        : 0, max: 1,
    type : String.class
  ]
]

outputs = [
  result: [
    name: 'Result output string', 
    title: 'Result output string', 
    description: 'This type of result does not allow the blocks to be linked together.', 
    type: String.class
  ]
]


def runScript(connection, scriptFile, arguments) {
  Logger logger = LoggerFactory.getLogger("script")
  GroovyShell shell = new GroovyShell()
  Script scriptInstance = shell.parse(new File(scriptFile))
  Object result = scriptInstance.invokeMethod("exec", [connection, arguments])
  if(result != null) {
    logger.info(result.toString())
  }
}

def importAndGetTable(connection, pathFile, inputSRID){
  runScript(
    connection, 
    "noisemodelling/wps/Import_and_Export/Import_File.groovy", 
    ["pathFile":pathFile, "inputSRID": inputSRID]
    )
  File f = new File(pathFile)
	String bname = f.getName()
  return bname.substring(0,bname.lastIndexOf('.')).toUpperCase()
}

def exec(Connection connection, input) {
  // set road table
  String tableRoads = importAndGetTable(connection, input["roadGeomPath"], input["inputSRID"])

  // set building table
  String tableBuilding =  importAndGetTable(connection, input["buildingGeomPath"], input["inputSRID"])

  // set reciver table
  String tableReceivers = importAndGetTable(connection, input["receiverGeomPath"], input["inputSRID"])

  // set dem table
  String tableDEM = null
  if (input["demGeomPath"]) {
    tableDEM = importAndGetTable(connection, input["demGeomPath"], input["inputSRID"])
  } 
  

  // set groundAbs table
  String tableGroundAbs = null
  if (input["groundAbsGeomPath"]) {
    tableGroundAbs = importAndGetTable(connection, input["groundAbsGeomPath"], input["inputSRID"])
  } 

  // run calculation
  Map args = [
      "tableBuilding": tableBuilding, 
      "tableRoads": tableRoads, 
      "tableReceivers": tableReceivers,
      "tableDEM": tableDEM, 
      "tableGroundAbs": tableGroundAbs,
      "paramWallAlpha": input["paramWallAlpha"],
      "confReflOrder": input["confReflOrder"],
      "confMaxSrcDist": input["confMaxSrcDist"],
      "confMaxReflDist": input["confMaxReflDist"],
      "confThreadNumber": input["confThreadNumber"],
      "confDiffVertical": input["confDiffVertical"] == 1 ? 1 : null,
      "confDiffHorizontal": input["confDiffHorizontal"] == 1 ? 1 : null,
      "confExportSourceId": input["confExportSourceId"],
      "confHumidity": input["confHumidity"],
      "confTemperature": input["confTemperature"],
      "confFavorableOccurrencesDay": input["confFavorableOccurrencesDay"],
      "confFavorableOccurrencesEvening": input["confFavorableOccurrencesEvening"],
      "confFavorableOccurrencesNight": input["confFavorableOccurrencesNight"],
      "confRaysName": input["confRaysName"]
    ].findAll{ it.value!=null }

  runScript(
    connection, 
    "noisemodelling/wps/NoiseModelling/Noise_level_from_traffic.groovy",
    args
  )

  // export results
  for (tbl in ["LDAY_GEOM", "LEVENING_GEOM", "LNIGHT_GEOM", "LDEN_GEOM"]){
    Path p_result = Paths.get(input["exportDir"]).resolve(Paths.get(tbl + ".geojson"))
    runScript(
      connection, 
      "noisemodelling/wps/Import_and_Export/Export_Table.groovy",
      ["exportPath": p_result, "tableToExport":tbl]
    )
  }
}

