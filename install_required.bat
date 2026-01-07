@echo off
echo Installing required Python packages...

"python\python\python.exe" -m pip install --upgrade pip
"python\python\python.exe" -m pip install msal

echo.
echo Installation complete!
pause
