@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ============================================================
echo Visual Studio / C++ Diagnose
echo ============================================================
echo.

set "VSWHERE="
if defined ProgramFiles(x86) set "VSWHERE=!ProgramFiles(x86)!\Microsoft Visual Studio\Installer\vswhere.exe"
if defined VSWHERE if exist "!VSWHERE!" goto found

set "VSWHERE=!ProgramFiles!\Microsoft Visual Studio\Installer\vswhere.exe"
if exist "!VSWHERE!" goto found

echo vswhere.exe: NICHT GEFUNDEN
pause
exit /b 1

:found
echo vswhere:
echo !VSWHERE!
echo.

set "VSINSTALL="
for /f "usebackq delims=" %%I in (`"!VSWHERE!" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VSINSTALL=%%I"

if not defined VSINSTALL goto no_vs

echo Visual Studio:
echo !VSINSTALL!
echo.

set "VCVARS=!VSINSTALL!\VC\Auxiliary\Build\vcvars64.bat"
echo vcvars64:
echo !VCVARS!
echo.

if not exist "!VCVARS!" goto no_vcvars

call "!VCVARS!"

echo.
echo cl.exe:
where cl.exe
echo.

echo Compiler-Version:
cl.exe 2>&1 | findstr /I /C:"Version"
echo.

echo Windows SDK Tools:
where rc.exe 2>nul
echo.

pause
exit /b 0

:no_vs
echo MSVC x64 Toolset: NICHT GEFUNDEN
pause
exit /b 1

:no_vcvars
echo vcvars64.bat: NICHT GEFUNDEN
pause
exit /b 1
