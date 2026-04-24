@echo off
REM PRAXIS Kit Desktop — Build Script
REM Produces dist/praxis-desktop.exe via PyInstaller
REM
REM Prerequisites:
REM   pip install customtkinter pyinstaller
REM
REM Usage:
REM   cd D:\PRAXIS\universal-kit
REM   desktop\build_exe.bat

echo ========================================
echo  PRAXIS Kit Desktop — Build
echo ========================================

cd /d "%~dp0\.."

echo.
echo [1/3] Checking dependencies...
python -c "import customtkinter; print('  customtkinter OK')" 2>nul || (
    echo   Installing customtkinter...
    pip install customtkinter
)
python -c "import PyInstaller; print('  PyInstaller OK')" 2>nul || (
    echo   Installing PyInstaller...
    pip install pyinstaller
)

echo.
echo [2/3] Quick import test...
python -c "from desktop.app import main; print('  Import OK')"

if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Import test failed. Fix errors before building.
    pause
    exit /b 1
)

echo.
echo [3/3] Building executable...
pyinstaller --onefile --windowed --name "praxis-desktop" --noconfirm ^
    --add-data "collector;collector" ^
    --add-data "adapters;adapters" ^
    --add-data "config;config" ^
    --add-data "export;export" ^
    --add-data "templates;templates" ^
    --hidden-import customtkinter ^
    desktop\app.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: PyInstaller build failed.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Build complete!
echo  Output: dist\praxis-desktop.exe
echo ========================================
pause
