@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ============================================================
echo Baccarat Counter v21.2.124 - Entwicklungsstand Casino-Auswahl
echo ============================================================
echo.

rem ------------------------------------------------------------
rem vswhere.exe suchen.
rem WICHTIG: ProgramFiles(x86) wird mit Delayed Expansion benutzt,
rem damit die Klammern in "Program Files (x86)" den CMD-Parser
rem nicht zerlegen.
rem ------------------------------------------------------------

set "VSWHERE="

if defined ProgramFiles(x86) set "VSWHERE=!ProgramFiles(x86)!\Microsoft Visual Studio\Installer\vswhere.exe"

if defined VSWHERE if exist "!VSWHERE!" goto vswhere_found

set "VSWHERE=!ProgramFiles!\Microsoft Visual Studio\Installer\vswhere.exe"
if exist "!VSWHERE!" goto vswhere_found

echo FEHLER: vswhere.exe wurde nicht gefunden.
echo.
echo Erwartete Orte:
if defined ProgramFiles(x86) echo   !ProgramFiles(x86)!\Microsoft Visual Studio\Installer\vswhere.exe
echo   !ProgramFiles!\Microsoft Visual Studio\Installer\vswhere.exe
echo.
echo Bitte Visual Studio Installer pruefen.
pause
exit /b 1

:vswhere_found
echo vswhere gefunden:
echo !VSWHERE!
echo.

rem ------------------------------------------------------------
rem Neueste VS-Installation mit x64-MSVC suchen.
rem ------------------------------------------------------------

set "VSINSTALL="

for /f "usebackq delims=" %%I in (`"!VSWHERE!" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VSINSTALL=%%I"

if not defined VSINSTALL goto no_vs

echo Visual Studio gefunden:
echo !VSINSTALL!
echo.

set "VCVARS=!VSINSTALL!\VC\Auxiliary\Build\vcvars64.bat"

if not exist "!VCVARS!" goto no_vcvars

echo Lade x64 C++ Build-Umgebung...
call "!VCVARS!"
if errorlevel 1 goto vcvars_error

where cl.exe >nul 2>&1
if errorlevel 1 goto no_cl

echo.
echo Compiler:
where cl.exe
echo.

if not exist "src\main.cpp" goto no_source
if not exist "build" mkdir "build"

echo Kompiliere BaccaratCounterV124_Development.exe...
echo.

cl.exe ^
 /nologo ^
 /std:c++20 ^
 /EHsc ^
 /W4 ^
 /O2 ^
 /MD ^
 /utf-8 ^
 /DUNICODE ^
 /D_UNICODE ^
 /DWIN32_LEAN_AND_MEAN ^
 /DNOMINMAX ^
 /Fe:"build\BaccaratCounterV124_Development.exe" ^
 "src\main.cpp" ^
 /link ^
 /SUBSYSTEM:WINDOWS ^
 winhttp.lib ^
 comctl32.lib ^
 user32.lib ^
 gdi32.lib ^
 shell32.lib ^
 ole32.lib ^
 winmm.lib ^
 comdlg32.lib ^
 advapi32.lib

if errorlevel 1 goto build_failed

echo.
echo ============================================================
echo BUILD ERFOLGREICH
echo ============================================================
echo.
echo Programm:
echo %CD%\build\BaccaratCounterV124_Development.exe
echo.
echo CMake wurde NICHT verwendet.
echo.
pause
exit /b 0

:no_vs
echo FEHLER: Keine Visual-Studio-Installation mit x64 C++ Toolset gefunden.
echo.
echo Oeffne Visual Studio Installer ^> Aendern und pruefe:
echo   - Desktopentwicklung mit C++
echo   - MSVC x64/x86 Build Tools
echo   - Windows 10/11 SDK
echo.
pause
exit /b 1

:no_vcvars
echo FEHLER: vcvars64.bat wurde nicht gefunden:
echo !VCVARS!
echo.
pause
exit /b 1

:vcvars_error
echo FEHLER beim Laden der Visual-Studio-Buildumgebung.
pause
exit /b 1

:no_cl
echo FEHLER: cl.exe wurde nach vcvars64.bat nicht gefunden.
pause
exit /b 1

:no_source
echo FEHLER: src\main.cpp wurde nicht gefunden.
echo Aktueller Ordner:
cd
pause
exit /b 1

:build_failed
echo.
echo ============================================================
echo BUILD FEHLGESCHLAGEN
echo ============================================================
echo.
echo Bitte die komplette Compiler-Ausgabe aus diesem Fenster senden.
echo.
pause
exit /b 1
