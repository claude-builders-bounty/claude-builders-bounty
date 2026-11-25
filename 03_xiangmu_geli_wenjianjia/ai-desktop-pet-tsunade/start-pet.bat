@echo off
chcp 65001 >nul
title AI桌宠·纲手 启动器

set PROJECT_DIR=D:\Ai\Agent\gongzuoqu\03_xiangmu_geli_wenjianjia\ai-desktop-pet-tsunade
set LOG_FILE=%PROJECT_DIR%\pet-startup-%date:~-4,4%%date:~-10,2%%date:~-7,2%-%time:~0,2%%time:~3,2%%time:~6,2%.log
set LOG_FILE=%LOG_FILE: =0%

echo ==========================================
echo  AI桌宠·纲手 一键启动器
echo  日志文件: %LOG_FILE%
echo ==========================================
echo.

cd /d "%PROJECT_DIR%"

echo [1/4] 清理残留进程...
taskkill /IM electron.exe /F >nul 2>&1
taskkill /IM node.exe /F >nul 2>&1
for /f "tokens=5" %%i in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
    taskkill /PID %%i /F >nul 2>&1
)
timeout /t 1 >nul

echo [2/4] 检查依赖...
if not exist node_modules (
    echo 首次运行，安装依赖中...
    npm install >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo 依赖安装失败，查看日志: %LOG_FILE%
        pause
        exit /b 1
    )
)

echo [3/4] 编译主进程...
npx tsc -p tsconfig.main.json >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo 编译失败，查看日志: %LOG_FILE%
    pause
    exit /b 1
)

echo [4/4] 启动开发模式...
echo.
echo ----------------------------------------
echo  宠物窗口将出现在屏幕左上角 (100,100)
echo  右键宠物可打开菜单: 聊天/设置/监控/提醒
echo  DevTools 会自动打开，可关闭它
echo  关闭此窗口即退出程序
echo ----------------------------------------
echo.

echo === 启动时间: %date% %time% === >> "%LOG_FILE%"
npm run electron:dev >> "%LOG_FILE%" 2>&1

echo.
echo 程序已退出，查看完整日志: %LOG_FILE%
pause