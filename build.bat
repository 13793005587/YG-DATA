@echo off
cd /d "%~dp0"

echo ====================================
echo   开始打包 YG-DATA
echo ====================================

echo [0/4] 检查环境...
if not exist ".venv\Scripts\pyinstaller.exe" (
    echo [错误] 未找到 PyInstaller，请先执行：
    echo     .venv\Scripts\activate
    echo     pip install -r requirements-dev.txt
    pause
    exit /b 1
)

if not exist "resources\app_icon.ico" (
    echo [错误] 未找到 resources\app_icon.ico，无法打包
    pause
    exit /b 1
)

if not exist "YG-DATA.spec" (
    echo [错误] 未找到 YG-DATA.spec
    pause
    exit /b 1
)

echo [1/4] 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [2/4] 开始打包（使用 YG-DATA.spec）...
rem 打包参数全部集中在 YG-DATA.spec 中，避免命令行与 spec 两处不一致
.venv\Scripts\pyinstaller.exe --noconfirm YG-DATA.spec

if errorlevel 1 (
    echo.
    echo ====================================
    echo   打包失败！请查看上方错误信息
    echo ====================================
    pause
    exit /b 1
)

if not exist "dist\YG-DATA.exe" (
    echo.
    echo [错误] 打包命令已结束，但没有生成 dist\YG-DATA.exe
    pause
    exit /b 1
)

echo [3/4] 完成！
echo.
echo 成品位置：dist\YG-DATA.exe
echo [4/4] 按任意键关闭本窗口...
pause