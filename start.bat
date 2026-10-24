@echo off
setlocal EnableExtensions
title Maryam's Planner Studio
cd /d "%~dp0"

echo.
echo  ==============================================
echo     Maryam's Planner Studio
echo  ==============================================
echo.

rem ---- 0. Make sure the whole project is here (not run from inside the zip) --
if not exist "%~dp0backend\requirements.txt" goto :notextracted
if not exist "%~dp0backend\app\main.py" goto :notextracted

rem ---- 1. Find Python 3.11 or newer ---------------------------------------
set "PY="
where py >nul 2>nul && py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul && set "PY=py -3"
if not defined PY (
  where python >nul 2>nul && python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo  [!] Python 3.11 or newer was not found.
  echo      Install it from https://www.python.org/downloads/  and tick
  echo      "Add python.exe to PATH" during installation. Then run start.bat again.
  echo.
  pause
  exit /b 1
)

rem ---- 2. Virtual environment ----------------------------------------------
if not exist "%~dp0backend\.venv\Scripts\python.exe" (
  echo  First run: creating a private Python environment ^(one time only^)...
  %PY% -m venv "%~dp0backend\.venv"
  if errorlevel 1 goto :fail
)
set "VPY=%~dp0backend\.venv\Scripts\python.exe"

rem ---- 3. Python packages (re-installed only when requirements.txt changes) --
fc /b "%~dp0backend\requirements.txt" "%~dp0backend\.venv\installed-requirements.txt" >nul 2>nul
if errorlevel 1 (
  echo  Installing Python packages ^(needs internet, takes a few minutes the first time^)...
  "%VPY%" -m pip install --disable-pip-version-check --upgrade pip >nul
  "%VPY%" -m pip install --disable-pip-version-check -r "%~dp0backend\requirements.txt"
  if errorlevel 1 goto :fail
  copy /y "%~dp0backend\requirements.txt" "%~dp0backend\.venv\installed-requirements.txt" >nul
)

rem ---- 4. Chromium PDF engine (quick no-op when already installed) ----------
if not exist "backend\.venv\chromium-ok.txt" echo  Installing the Chromium PDF engine ^(one time, about 150 MB^)...
"%VPY%" -m playwright install chromium
if errorlevel 1 (
  echo  [!] Chromium could not be installed right now. The app will start, but PDF export
  echo      will not work until this succeeds. Check your internet connection and run start.bat again.
) else (
  echo ok> "backend\.venv\chromium-ok.txt"
)

rem ---- 5. Interface (already built in the zip; rebuilt only if missing) -----
if not exist "frontend\dist\index.html" (
  where npm >nul 2>nul
  if errorlevel 1 (
    echo  [!] The interface build is missing and Node.js is not installed.
    echo      Install Node.js LTS from https://nodejs.org and run start.bat again.
  ) else (
    echo  Building the interface...
    pushd frontend
    call npm install
    call npm run build
    popd
  )
)

rem ---- 6. Start --------------------------------------------------------------
echo.
echo  Starting... your browser will open at http://localhost:8000
echo  Keep this window open while you use the app. Close it to stop the studio.
echo.
set "PS_OPEN_BROWSER=1"
"%VPY%" -m uvicorn app.main:app --app-dir "%~dp0backend" --host 127.0.0.1 --port 8000
if errorlevel 1 (
  echo.
  echo  [!] The server stopped with an error. If it says the port is already in use,
  echo      the studio is probably already running - open http://localhost:8000
)
pause
exit /b 0

:fail
echo.
echo  [!] Setup failed. Scroll up to see the error, check your internet connection,
echo      then run start.bat again. See README.md - Troubleshooting.
pause
exit /b 1

:notextracted
echo  [!] The project files were not found next to start.bat.
echo      This happens when start.bat is opened directly from inside the zip file.
echo.
echo      Fix: close this window, right-click planner-studio.zip, choose "Extract All...",
echo      open the extracted "planner-studio" folder and double-click start.bat in there.
echo      ^(It must sit next to the "backend" and "frontend" folders.^)
echo.
echo      Current folder: %~dp0
pause
exit /b 1
