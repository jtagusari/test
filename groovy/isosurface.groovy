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

  // set result table
  String resultTable =  importAndGetTable(connection, input["resultGeomPath"])
  String triangleTable =  importAndGetTable(connection, input["triangleGeomPath"])

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
  Path p_result = Paths.get(input["exportPath"])
  runScript(
    connection, 
    "noisemodelling/wps/Import_and_Export/Export_Table.groovy",
    ["exportPath": p_result, "tableToExport": "CONTOURING_NOISE_MAP"]
  )
}

