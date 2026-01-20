@echo off
setlocal

echo =============================================
echo   Opening all .ts files in Qt Linguist via OSGeo4W Shell
echo =============================================
echo.

REM Path to OSGeo4W.bat inside your QGIS installation
set OSGEO4W_BAT="C:\Program Files\QGIS 3.38.3\OSGeo4W.bat"

if not exist %OSGEO4W_BAT% (
    echo ERROR: OSGeo4W.bat not found at %OSGEO4W_BAT%
    pause
    exit /b
)

REM Go to plugin folder
cd /d "%~dp0"

REM Ensure i18n folder exists
if not exist i18n (
    echo ERROR: i18n folder not found
    pause
    exit /b
)

set COUNT=0

REM Open all .ts files in Qt Linguist
for %%F in (i18n\*.ts) do (
    echo Opening %%F ...
    call %OSGEO4W_BAT% linguist "%%F"
    set /a COUNT+=1
)

echo.
echo =============================================
echo Opened %COUNT% translation file(s) in Qt Linguist.
echo =============================================
pause
