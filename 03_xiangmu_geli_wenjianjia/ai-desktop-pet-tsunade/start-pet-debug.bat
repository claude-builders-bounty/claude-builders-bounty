@echo off
chcp 65001 >nul
title AI Desktop Pet - Debug Launcher

set PROJECT_DIR=D:\Ai\Agent\gongzuoqu\03_xiangmu_geli_wenjianjia\ai-desktop-pet-tsunade
set TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%-%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set LOG_FILE=%PROJECT_DIR%\pet-debug-%TIMESTAMP%.log

echo ==========================================
echo  AI Desktop Pet - Debug Launcher
echo  Log file: %LOG_FILE%
echo ==========================================
echo.

cd /d "%PROJECT_DIR%"

echo [1/4] Cleaning stale processes...
taskkill /IM electron.exe /F >nul 2>&1
taskkill /IM node.exe /F >nul 2>&1
for /f "tokens=5" %%i in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
    taskkill /PID %%i /F >nul 2>&1
)
timeout /t 1 >nul

echo [2/4] Checking dependencies...
if not exist node_modules (
    echo First run, installing dependencies...
    npm install >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo Dependency install failed. Check log: %LOG_FILE%
        type "%LOG_FILE%"
        pause
        exit /b 1
    )
    echo Dependencies installed.
) else (
    echo Dependencies already exist.
)

echo [3/4] Compiling main process...
npx tsc -p tsconfig.main.json >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo Compilation failed. Check log: %LOG_FILE%
    type "%LOG_FILE%"
    pause
    exit /b 1
)
echo Compilation successful.

echo [4/4] Starting dev mode...
echo.
echo ----------------------------------------
echo  Pet window: screen (100,100) - transparent frameless
echo  Right-click menu: Chat / Settings / Monitor / Reminder / About
echo  DevTools: opens automatically, can close manually
echo  Close this window = exit program
echo ----------------------------------------
echo.

echo === Start time: %date% %time% === >> "%LOG_FILE%"
npm run electron:dev >> "%LOG_FILE%" 2>&1

echo.
echo Program exited. Full log saved: %LOG_FILE%
type "%LOG_FILE%"
pause