@echo off
setlocal

echo Downloading Python.zip...

REM Set URL and output file
set URL=https://github.com/Clicker-games-Studio/Custom-Launcher/releases/download/Python/Python.zip
set ZIPFILE=Python.zip
set EXTRACTDIR=Python

REM Download using PowerShell
powershell -Command "Invoke-WebRequest -Uri '%URL%' -OutFile '%ZIPFILE%'"

if not exist "%ZIPFILE%" (
    echo Download failed.
    pause
    exit /b
)

echo Download complete.
echo Extracting...

REM Create extract directory
if not exist "%EXTRACTDIR%" (
    mkdir "%EXTRACTDIR%"
)

REM Unzip
powershell -Command "Expand-Archive -Path '%ZIPFILE%' -DestinationPath '%EXTRACTDIR%' -Force"

echo Extraction complete.
echo Done.

pause
endlocal
