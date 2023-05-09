@rem
@rem This is a modified version of wps_scripts.bat bundled in NoiseModelling 4.0.0
@rem by Junta Tagusari

@if "%DEBUG%" == "" @echo off

@rem ##########################################################################
@rem
@rem  wps_scripts startup script for Windows
@rem
@rem ##########################################################################

@rem Set local scope for the variables with windows NT shell
if "%OS%"=="Windows_NT" setlocal

@rem Check environment
:checkenv_noisemodelling
if defined NOISEMODELLING_HOME goto checkenv_java
echo.
echo ERROR: NOISEMODELLING_HOME is not set and no NoiseModelling classes could be found.
echo.
echo Please set the NOISEMODELLING_HOME variable in your environment to match the
echo location of your NoiseModelling installation.

goto fail


@rem Check environment
:checkenv_java
if defined JAVA_FOR_NOISEMODELLING goto check_javaexe
echo.
echo ERROR: JAVA_FOR_NOISEMODELLING is not set.
echo.
echo Please set the JAVA_FOR_NOISEMODELLING variable in your environment to match the
echo location of your NoiseModelling installation.
echo Note that the version of Java must match the NoiseModelling requirements.

goto fail

@rem Check java.exe
:check_javaexe
set JAVA_EXE=%JAVA_FOR_NOISEMODELLING:"=%/bin/java.exe
if exist "%JAVA_EXE%" goto init
echo.
echo ERROR: JAVA_FOR_NOISEMODELLING is set to an invalid directory: %JAVA_FOR_NOISEMODELLING%
echo.
echo Please set the JAVA_FOR_NOISEMODELLING variable in your environment to match the
echo location of your Java installation.

goto fail

:init
@rem Set APP_HOME and CLASSPATH (Resolve any "." and ".." in APP_HOME to make it shorter.)
set APP_HOME=%NOISEMODELLING_HOME:"=%
for %%i in ("%APP_HOME%") do set APP_HOME=%%~fi
set CLASSPATH=.;%APP_HOME%/lib/*

@rem Add options if necessary
set DEFAULT_JVM_OPTS=
set JAVA_OPTS=
set WPS_SCRIPTS_OPTS=


@rem Get command-line arguments, handling Windows variants
set CMD_LINE_ARGS=

@rem If blank, goto execute. / if not blank, set args
if "x%~1" == "x" goto execute
set CMD_LINE_ARGS=%*

:execute
@rem Execute wps_scripts
"%JAVA_EXE%" %DEFAULT_JVM_OPTS% %JAVA_OPTS% %WPS_SCRIPTS_OPTS%  -classpath "%CLASSPATH%" org.noisemodelling.runner.Main %CMD_LINE_ARGS%
if "%ERRORLEVEL%"=="0" goto mainEnd


:fail
rem Set variable WPS_SCRIPTS_EXIT_CONSOLE if you need the _script_ return code instead of
rem the _cmd.exe /c_ return code!
if  not "" == "%WPS_SCRIPTS_EXIT_CONSOLE%" exit 1
exit /b 1

:mainEnd
if "%OS%"=="Windows_NT" endlocal
