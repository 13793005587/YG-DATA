@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ====================================
echo   开始打包 YG-DATA
echo ====================================

echo [0/3] 检查环境...
if not exist ".venv\Scripts\pyinstaller.exe" (
    echo [错误] 未找到 PyInstaller，请先执行：
    echo     .venv\Scripts\activate
    echo     pip install pyinstaller
    pause
    exit /b 1
)

if not exist "resources\app_icon.ico" (
    echo [警告] 未找到 resources\app_icon.ico，将不使用自定义图标
    set ICON_ARG=
    set DATA_ARG=
) else (
    set ICON_ARG=--icon "resources\app_icon.ico"
    set DATA_ARG=--add-data "resources;resources"
)

echo [1/3] 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [2/3] 开始打包...
.venv\Scripts\pyinstaller.exe --noconsole --onefile ^
  --name YG-DATA ^
  %ICON_ARG% ^
  %DATA_ARG% ^
  --hidden-import win32com ^
  --hidden-import win32com.client ^
  --hidden-import pythoncom ^
  --hidden-import pywintypes ^
  --hidden-import PySide6.QtNetwork ^
  --collect-submodules win32com ^
  --exclude-module PySide6.QtWebEngineCore ^
  --exclude-module PySide6.QtWebEngineWidgets ^
  --exclude-module PySide6.Qt3DCore ^
  --exclude-module PySide6.QtCharts ^
  --exclude-module PySide6.QtQuick ^
  --exclude-module PySide6.QtQml ^
  main.py

if errorlevel 1 (
    echo.
    echo ====================================
    echo   打包失败！请查看上方错误信息
    echo ====================================
    pause
    exit /b 1
)

echo [3/3] 完成！
echo.
echo 成品位置：dist\YG-DATA.exe
echo.
pause