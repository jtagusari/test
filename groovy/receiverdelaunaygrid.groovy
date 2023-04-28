import org.h2gis.api.ProgressVisitor
import org.slf4j.Logger
import org.slf4j.LoggerFactory
import java.sql.Connection
import java.nio.file.Path;
import java.nio.file.Paths;

title = 'Receiver at delaunay grid point'
description = 'Geometry of receivers at delaunay grid points is obtained'

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
    type : String.class
  ],
  fenceGeomPath:[
    name : "Path of the fence file",
    title : "Path of the fence file",
    description : "Path of the fence file",
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
  maxPropDist : [
    name: 'Maximum Propagation Distance',
    title: 'Maximum Propagation Distance',
    description: 'Set Maximum propagation distance in meters. Avoid loading to much geometries when doing Delaunay triangulation. (FLOAT)' +
            '</br> </br> <b> Default value : 500 </b>',
    min: 100, max: 2000,
    type: Double.class
  ],
  roadWidth          : [
    name: 'Source Width',
    title: 'Source Width',
    description: 'Set Road Width in meters. No receivers closer than road width distance.(FLOAT) ' +
            '</br> </br> <b> Default value : 2 </b>',
    min: 1, max: 20,
    type: Double.class
  ],
  maxArea            : [
    name: 'Maximum Area',
    title: 'Maximum Area',
    description: 'Set Maximum Area in m2. No triangles larger than provided area. Smaller area will create more receivers. (FLOAT)' +
            '</br> </br> <b> Default value : 2500 </b> ',
    min: 100, max: 10000,
    type: Double.class
  ],
  height: [
    name       : 'height',
    title      : 'height',
    description: 'Height of receivers in meters (FLOAT)' +
            '</br> </br> <b> Default value : 4 </b> ',
    min        : 0, max: 10,
    type       : Double.class
  ],
  isoSurfaceInBuildings: [
    name: 'Create IsoSurfaces over buildings',
    title: 'Create IsoSurfaces over buildings',
    description: 'If enabled isosurfaces will be visible at the location of buildings',
    min: 0, max: 1,
    type: Boolean.class,
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

  // set building table
  String tableBuilding =  importAndGetTable(connection, input["buildingGeomPath"], input["inputSRID"])

  // set source table
  String sourcesTableName = null
  if (input["sourceGeomPath"]) {
    sourcesTableName = importAndGetTable(connection, input["sourceGeomPath"], input["inputSRID"])
  } 
  

  // set fance table
  String fenceTableName = null
  if (input["fenceGeomPath"]) {
    fenceTableName = importAndGetTable(connection, input["fenceGeomPath"], input["inputSRID"])
  } 

  // run calculation
  Map args = [
      "tableBuilding": tableBuilding, 
      "sourcesTableName": sourcesTableName, 
      "fenceTableName": fenceTableName, 
      "maxPropDist": input["maxPropDist"],
      "roadWidth": input["roadWidth"],
      "maxArea": input["maxArea"],
      "height": input["height"],
      "isoSurfaceInBuildings": input["isoSurfaceInBuildings"] == 1 ? true : null
    ].findAll{ it.value!=null }

  runScript(
    connection, 
    "noisemodelling/wps/Receivers/Delaunay_Grid.groovy",
    args
  )

  // export results
  for (tbl in ["RECEIVERS", "TRIANGLES"]){
    Path p_result = Paths.get(input["exportDir"]).resolve(Paths.get(tbl + ".geojson"))
    runScript(
      connection, 
      "noisemodelling/wps/Import_and_Export/Export_Table.groovy",
      ["exportPath": p_result, "tableToExport":tbl]
    )
  }

}

