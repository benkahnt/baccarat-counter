@echo off
setlocal
set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%LocalAppData%\Google\Chrome\Application\chrome.exe"

if not exist "%CHROME%" (
  echo Google Chrome wurde nicht gefunden.
  timeout /t 5 /nobreak >nul
  exit /b 1
)

set "PROFILE=%LocalAppData%\BaccaratCounterChrome"
rem Keep the dedicated monitoring browser responsive when covered/backgrounded.
set "MONITOR_FLAGS=--disable-background-timer-throttling --disable-renderer-backgrounding --disable-backgrounding-occluded-windows"

set "START_MODE=normal"
if /I "%~1"=="simulator" set "START_MODE=simulator"
if not "%~1"=="" if /I not "%~1"=="simulator" (
  echo Unbekannter Startmodus: %~1
  exit /b 2
)
rem Clear only the dedicated profile, before Chrome can lock or reuse its data.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0reset_chrome_debug_data.ps1" -Mode "%START_MODE%"
if errorlevel 1 (
  echo Bitte die Fehlermeldung oben beachten. Chrome wurde nicht neu gestartet.
  pause
  exit /b 1
)

if /I "%~1"=="simulator" (
  rem Same debug profile/port: Chrome reuses the running debug instance and opens one additional tab.
  start "" "%CHROME%" %MONITOR_FLAGS% --remote-debugging-port=9222 --user-data-dir="%PROFILE%" "https://roulette-simulator.info/en/games/baccarat-simulator"
  exit /b 0
)

rem Normal EXE startup: only an empty Debug-Chrome window. On Verbinden this
rem exact tab is navigated by CDP to the common Betify home page. The selected
rem game page is loaded only after Betify has positively confirmed the login.
if not "%~1"=="" (
  echo Unbekannter Startmodus: %~1
  exit /b 2
)
start "" "%CHROME%" %MONITOR_FLAGS% --remote-debugging-port=9222 --user-data-dir="%PROFILE%" --new-window "about:blank"
exit /b 0
