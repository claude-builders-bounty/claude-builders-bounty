@echo off
rem llama-server launcher for Windows + CUDA 11.8
rem Usage: start_llama_server.bat [model_path] [port] [gpu_layers] [ctx_size]

setlocal enabledelayedexpansion

rem === CONFIGURATION ======================================================
set CUDA_BIN=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin
set LLAMA_BIN=D:\Ai\llama.cpp-new\build\bin
set DEFAULT_MODEL=D:\Ai\models\DarkIdol-Qwen3.8-27B-v1.1.Q4_K_M.gguf
set DEFAULT_PORT=8080
set DEFAULT_GPU_LAYERS=6
set DEFAULT_CTX_SIZE=32768
rem ========================================================================

set PATH=%CUDA_BIN%;%LLAMA_BIN%;%PATH%
cd /d %LLAMA_BIN%

set MODEL=%~1
if "%MODEL%"=="" set MODEL=%DEFAULT_MODEL%

set PORT=%~2
if "%PORT%"=="" set PORT=%DEFAULT_PORT%

set GPU_LAYERS=%~3
if "%GPU_LAYERS%"=="" set GPU_LAYERS=%DEFAULT_GPU_LAYERS%

set CTX_SIZE=%~4
if "%CTX_SIZE%"=="" set CTX_SIZE=%DEFAULT_CTX_SIZE%

if not exist "%MODEL%" (
  echo ERROR: Model not found: %MODEL%
  exit /b 1
)

echo Starting llama-server...
 echo Model: %MODEL%
 echo Port: %PORT%
 echo GPU Layers: %GPU_LAYERS%
 echo Context: %CTX_SIZE%
 echo.

llama-server.exe --port %PORT% --host 0.0.0.0 \
  --model "%MODEL%" \
  --ctx-size %CTX_SIZE% --n-gpu-layers %GPU_LAYERS% --parallel 1 --api-prefix /v1