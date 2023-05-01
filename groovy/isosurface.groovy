import org.h2gis.api.ProgressVisitor
import org.slf4j.Logger
import org.slf4j.LoggerFactory
import java.sql.Connection
import java.nio.file.Path;
import java.nio.file.Paths;

title = 'Create Isosurface'
description = 'Create isosurface (sound-level contour) using results'

inputs = [
  resultGeomPath:[
    name : "Path of the result file",
    title : "Path of the result file",
    description : "Path of the result file",
    type : String.class
  ],
  triangleGeomPath:[
    name : "Path of the triangle file",
    title : "Path of the triangle file",
    description : "Path of the triangle file, of which file name must be 'triangles'",
    type : String.class
  ],
  isoClass         : [
    name: 'Iso levels in dB',
    title: 'Iso levels in dB',
    description: 'Separation of sound levels for isosurfaces. ' +
            '</br> </br> <b> Default value : 35.0,40.0,45.0,50.0,55.0,60.0,65.0,70.0,75.0,80.0,200.0 </b>',
    min: 0, max: 1,
    type: String.class
  ],
  smoothCoefficient: [
    name: 'Polygon smoothing coefficient',
    title: 'Polygon smoothing coefficient',
    description: 'This coefficient (Bezier curve coefficient) will smooth generated isosurfaces. If equal to 0, it disables the smoothing step.' +
            '</br> </br> <b> Default value : 1.0 </b>',
    min: 0, max: 1,
    type: Double.class
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

  // set result table
  String resultTable =  importAndGetTable(connection, input["resultGeomPath"], input["inputSRID"])
  String triangleTable =  importAndGetTable(connection, input["triangleGeomPath"], input["inputSRID"])

  // run calculation
  Map args = [
      "resultTable": resultTable, 
      "isoClass": input["isoClass"],
      "smoothCoefficient": input["smoothCoefficient"]
    ].findAll{ it.value!=null }

  runScript(
    connection, 
    "noisemodelling/wps/Acoustic_Tools/Create_Isosurface.groovy",
    args
  )
  
  // export results
  for (tbl in ["CONTOURLNG_NOISE_MAP"]){
    Path p_result = Paths.get(input["exportDir"]).resolve(Paths.get(tbl + ".geojson"))
    runScript(
      connection, 
      "noisemodelling/wps/Import_and_Export/Export_Table.groovy",
      ["exportPath": p_result, "tableToExport":tbl]
    )
  }
}

