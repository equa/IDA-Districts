@echo off
setlocal enabledelayedexpansion

echo =============================================
echo   Updating translations (auto-discover .py)
echo   Using OSGeo4W environment
echo =============================================
echo.

REM Detect OSGeo4W root
set OSGEO4W_ROOT=C:\Program Files\QGIS 3.38.3
if not exist "%OSGEO4W_ROOT%\OSGeo4W.bat" set OSGEO4W_ROOT=C:\OSGeo4W

if not exist "%OSGEO4W_ROOT%\OSGeo4W.bat" (
    echo ERROR: Could not find OSGeo4W.bat
    pause
    exit /b
)

echo Found OSGeo4W at: %OSGEO4W_ROOT%
echo.

REM Change to plugin root folder (where .bat is)
cd /d "%~dp0"

echo Collecting Python files...
del pyfiles.txt 2>nul

REM Recursively collect all plugin .py files
for /r %%F in (*.py) do (
    echo "%%F" >> pyfiles.txt
)

REM Add the translations.py file one folder above
echo "..\utility_functions\translations.py" >> pyfiles.txt

echo Files found:
type pyfiles.txt
echo.

REM ---- Process in chunks of 20 files ----
set CHUNK=
set NUM=0
set TOTAL=0

for /f "usebackq delims=" %%A in ("pyfiles.txt") do (
    set CHUNK=!CHUNK! %%A
    set /a NUM+=1
    set /a TOTAL+=1

    if !NUM! GEQ 20 (
        echo Running pylupdate5 on chunk...
        call "%OSGEO4W_ROOT%\OSGeo4W.bat" pylupdate5 -noobsolete !CHUNK! -ts i18n\ida_mosim_de.ts i18n\ida_mosim_en.ts
        set CHUNK=
        set NUM=0
    )
)

REM Process the remainder (final chunk)
if NOT "!CHUNK!"=="" (
    echo Running pylupdate5 on final chunk...
    call "%OSGEO4W_ROOT%\OSGeo4W.bat" pylupdate5 -noobsolete !CHUNK! -ts i18n\ida_mosim_de.ts i18n\ida_mosim_en.ts
)

echo.
echo =============================================
echo Translations updated successfully.
echo Total files: %TOTAL%
echo =============================================
echo.

pause
