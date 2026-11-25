@echo off
chcp 65001 >nul
title Ollama 本地部署一键安装脚本
echo ========================================
echo  Ollama 本地大模型一键部署脚本
echo 版本: 2026.10
echo ========================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 请以管理员身份运行此脚本！
    echo 请右键点击此脚本选择 "以管理员身份运行"
    pause
    exit /b 1
)

echo [1/6] 检查系统环境...
echo 系统版本: 
ver
echo.

:: 检查 Ollama 是否已安装
where ollama >nul 2>&1
if %errorlevel% equ 0 (
    echo [信息] 检测到已安装 Ollama
    ollama --version
) else (
    echo [信息] 未检测到 Ollama，开始下载安装...
    echo 正在下载 Ollama 安装程序...
    powershell -Command "Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile '%TEMP%\OllamaSetup.exe'"
    if %errorlevel% neq 0 (
        echo [错误] 下载失败，请检查网络或手动下载 https://ollama.com/download
        pause
        exit /b 1
    )
    echo 正在静默安装 Ollama...
    start /wait "" "%TEMP%\OllamaSetup.exe" /quiet
    if %errorlevel% neq 0 (
        echo [错误] 安装失败，请手动安装
        pause
        exit /b 1
    )
    echo [完成] Ollama 安装完成
)
echo.

:: 检查 Ollama 服务
echo [2/6] 启动 Ollama 服务...
tasklist | findstr /i "ollama" >nul
if %errorlevel% neq 0 (
    start /b ollama serve
    timeout /t 5 >nul
)
echo [完成] Ollama 服务已启动
echo.

:: 显存/内存检测
echo [3/6] 检测硬件配置...
wmic path win32_VideoController get AdapterRAM,Name 2>nul | findstr /v "^$" | findstr /v "AdapterRAM"
wmic computersystem get TotalPhysicalMemory
echo.

echo [4/6] 推荐模型配置建议：
echo   显存 >= 8GB  : 推荐 7B-14B 模型 (如 qwen2.5:7b, llama3.1:8b)
echo   显存 >= 16GB : 推荐 32B-70B 模型(量化版)
echo   仅 CPU     : 建议 1.5B/3B/7B 量化模型 (qwen2.5:1.5b, qwen2.5:3b, llama3.2:3b)
echo.

:: 下载常用模型
echo [5/6] 下载推荐模型...
echo 正在下载 qwen2.5:7b (约 4.7GB)...
ollama pull qwen2.5:7b
echo 正在下载 qwen2.5:14b (约 9GB)...
ollama pull qwen2.5:14b
echo 正在下载 codellama:7b 代码模型...
ollama pull codellama:7b
echo 正在下载 nomic-embed-text 嵌入模型...
ollama pull nomic-embed-text
echo 模型下载完成
echo.

:: 安装 Web UI
echo [6/6] 安装 Web UI (Open WebUI)...
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    echo 检测到 Docker，部署 Open WebUI...
    docker run -d -p 3000:8080 -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/open-webui/open-webui:main
    echo Open WebUI 已部署在 http://localhost:3000
) else (
    echo 未检测到 Docker，建议手动安装 Chatbox 或 PageAssist 浏览器插件
    echo Chatbox: https://github.com/Bin-Huang/chatbox
    echo PageAssist: https://github.com/n4ze3m/page-assist
)
echo.

echo ========================================
echo 部署完成！
echo ========================================
echo.
echo 访问地址:
echo   Ollama API: http://localhost:11434
if exist "%PROGRAMFILES%DockerDocker.exe" (
    echo   Open WebUI: http://localhost:3000
)
echo.
echo 常用命令:
echo   ollama list              - 查看已安装模型
echo   ollama run qwen2.5:7b    - 运行模型
echo   ollama pull qwen2.5:14b  - 下载更多模型
echo   ollama rm 模型名        - 删除模型
echo   ollama serve             - 启动服务
echo.
echo 配置文件位置: %USERPROFILE%\.ollama
echo 模型存储位置: %USERPROFILE%\.ollama\models
echo.
pause
