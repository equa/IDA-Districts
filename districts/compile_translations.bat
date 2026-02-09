@echo off
setlocal

echo =============================================
echo        Compiling Translation Files
echo        Using Qt lrelease (Qt 6.10.0)
echo =============================================
echo.

REM Path to lrelease.exe
set LRELEASE="C:\Program Files\linguist_6.10.0\lrelease.exe"

REM Check if lrelease exists
if not exist %LRELEASE% (
    echo ERROR: lrelease not found at:
    echo %LRELEASE%
    echo Please adjust the path in this script.
    pause
    exit /b
)

REM Change to script location
cd /d "%~dp0"

REM Ensure i18n folder exists
if not exist i18n (
    echo ERROR: i18n folder not found.
    echo Put your .ts files into .\i18n\
    pause
    exit /b
)

echo Using lrelease:
echo %LRELEASE%
echo.

set COUNT=0

for %%F in (i18n\*.ts) do (
    echo Compiling %%F ...
    %LRELEASE% "%%F"
    set /a COUNT+=1
)

echo.
echo =============================================
echo Successfully compiled %COUNT% translation file(s)
echo Output: i18n\*.qm
echo =============================================
echo.

pause
