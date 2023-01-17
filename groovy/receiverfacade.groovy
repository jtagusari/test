import org.h2gis.api.ProgressVisitor
import org.slf4j.Logger
import org.slf4j.LoggerFactory
import java.sql.Connection
import java.nio.file.Path;
import java.nio.file.Paths;

title = 'Receiver at building facade'
description = 'Geometry of receivers at building facade is obtained'

inputs = [
  buildingGeomPath:[
    name : "Path of the building file",
    title : "Path of the building file",
    description : "Path of the building file",
    type : String.class
  ],
  sourceGeomPath:[
    name : "Path of the source file",
    title : "Path of the source file",
    description : "Path of the source file",
    min        : 0, max: 1,
    type : String.class
  ],
  fenceGeomPath:[
    name : "Path of the fence file",
    title : "Path of the fence file",
    description : "Path of the fence file",
    min        : 0, max: 1,
    type : String.class
  ],
  delta: [
    name       : 'Receivers minimal distance',
    title      : 'Distance between receivers',
    description: 'Distance between receivers in the Cartesian plane in meters',
    min        : 0, max: 100,
    type       : Double.class
  ],
  height: [
    name       : 'height',
    title      : 'height',
    description: 'Height of receivers in meters (FLOAT)' +
            '</br> </br> <b> Default value : 4 </b> ',
    min        : 0, max: 10,
    type       : Double.class
  ],
  exportPath : [
    name: "Path of export",
    title: "Path of export",
    description: "Path of export",
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

def importAndGetTable(connection, filepath){
  runScript(
    connection, 
    "noisemodelling/wps/Import_and_Export/Import_File.groovy", 
    ["pathFile":filepath]
    )
  File f = new File(filepath)
	String bname = f.getName()
  return bname.substring(0,bname.lastIndexOf('.')).toUpperCase()
}

def exec(Connection connection, input) {

  // set building table
  String tableBuilding =  importAndGetTable(connection, input["buildingGeomPath"])

  // set source table
  String sourcesTableName = null
  if (input["sourceGeomPath"]) {
    sourcesTableName = importAndGetTable(connection, input["sourceGeomPath"])
  } 
  

  // set fance table
  String fenceTableName = null
  if (input["fenceGeomPath"]) {
    fenceTableName = importAndGetTable(connection, input["fenceGeomPath"])
  } 

  // run calculation
  Map args = [
      "tableBuilding": tableBuilding, 
      "sourcesTableName": sourcesTableName, 
      "fenceTableName": fenceTableName, 
      "delta": input["delta"],
      "height": input["height"]
    ].findAll{ it.value!=null }

  runScript(
    connection, 
    "noisemodelling/wps/Receivers/Building_Grid.groovy",
    args
  )

  // export results
  Path p_result = Paths.get(input["exportPath"])
  runScript(
    connection, 
    "noisemodelling/wps/Import_and_Export/Export_Table.groovy",
    ["exportPath": p_result, "tableToExport": "RECEIVERS"]
  )
}

