import org.h2gis.api.ProgressVisitor
import org.slf4j.Logger
import org.slf4j.LoggerFactory
import java.sql.Connection
import java.nio.file.Path;
import java.nio.file.Paths;

title = 'Road emission from traffic'
description = 'Road emission (LW) is obtained from the information on the traffic'

inputs = [
  roadGeomPath:[
    name : "Path of the road file",
    title : "Path of the road file",
    description : "Path of the road file",
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
  noiseModellingHome : [
    name: "Path of NOISEMODELLING_HOME",
    title: "Path of NOISEMODELLING_HOME",
    description: "Path of NOISEMODELLING_HOME",
    type : String.class
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


def noiseModellingPath

def runScript(connection, scriptFile, arguments) {
  Path scriptPath = noiseModellingPath.resolve(Paths.get(scriptFile))
  Logger logger = LoggerFactory.getLogger("script")
  GroovyShell shell = new GroovyShell()
  Script scriptInstance = shell.parse(new File(scriptPath.toString()))
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
  // set noiseModellingPath
  noiseModellingPath = Paths.get(input["noiseModellingHome"])

  // set building table
  String tableRoads =  importAndGetTable(connection, input["roadGeomPath"], input["inputSRID"])


  // run calculation
  Map args = [
      "tableRoads": tableRoads
    ].findAll{ it.value!=null }

  runScript(
    connection, 
    "noisemodelling/wps/NoiseModelling/Road_Emission_from_Traffic.groovy",
    args
  )

  // export results
  for (tbl in ["LW_ROADS"]){
    Path p_result = Paths.get(input["exportDir"]).resolve(Paths.get(tbl + ".geojson"))
    runScript(
      connection, 
      "noisemodelling/wps/Import_and_Export/Export_Table.groovy",
      ["exportPath": p_result, "tableToExport":tbl]
    )
  }
}

