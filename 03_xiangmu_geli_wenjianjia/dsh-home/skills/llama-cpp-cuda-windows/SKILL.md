---
name: llama-cpp-cuda-windows
description: "Compile llama.cpp with CUDA on Windows for llama-server."
version: 1.0.0
license: MIT
platforms: [windows]
author: Hermes Agent
metadata:
  tags: [llama.cpp, cuda, gguf, llama-server, gtx1060, local-llm, openai-api]
  hermes:
    tags: [llama.cpp, cuda, gguf, llama-server, local-llm]
    related_skills: [configure-ollama-wsl, windows-system-maintenance, vs2022-buildtools-cuda-setup]
---

# llama.cpp CUDA Build & Deploy on Windows

## When to Use

- Compiling llama.cpp with CUDA on Windows (MSVC + CMake) for `llama-server` deployment
- Targeting consumer NVIDIA GPUs (GTX 10-series Pascal through RTX 40-series Ada)
- Reusing existing Ollama model blobs instead of re-downloading
- Deploying OpenAI-compatible local LLM API for SillyTavern or other clients
- Need one-click rollback without touching system CUDA or Ollama

## Supporting Files

- `references/cuda-architectures.md` — GPU compute capability table & VRAM estimation
- `references/ollama-blob-reuse.md` — Direct blob copy procedure (bypasses `ollama cp` WSL issue)
- `references/troubleshooting.md` — Failure matrix with fixes
- `templates/start_llama_server.bat` — Parameterized launcher with CUDA PATH
- `templates/cmake_cuda_flags.cmake` — Ready-to-use CMake flag block
- `templates/disable_cxx23.h` — STL version mismatch fix header

# llama.cpp CUDA Build & Deploy on Windows

Class-level skill for compiling llama.cpp with CUDA support on Windows (MSVC + CMake), deploying `llama-server` with OpenAI-compatible API, and reusing existing Ollama model blobs. Target: consumer GPUs (tested on GTX1060 Pascal sm_61, CUDA 11.8).

## Prerequisites

- **Visual Studio 2022** (BuildTools or Community) with "Desktop development with C++" workload
- **CUDA Toolkit 11.8** (not 12.x — Pascal architecture compatibility)
- **CMake 3.25+**
- **Python 3.10+** (for download scripts)
- **GPU**: NVIDIA with compute capability ≥ 5.0 (Pascal sm_61 tested)
- **RAM**: ≥ 8 GB system + GPU VRAM for model offload

## Build Procedure

### 1. Clone & Prepare

```bash
cd D:/Ai
# Use a fresh directory — rollback = delete this folder
git clone https://github.com/ggml-org/llama.cpp.git llama.cpp-new
cd llama.cpp-new
```

### 2. Configure CMake (Critical Flags)

```bash
cmake -B build \
  -G "Visual Studio 17 2022" \
  -DCMAKE_BUILD_TYPE=Release \
  -DGGML_CUDA=ON \
  -DGGML_CUDA_MMQ=ON \
  -DCMAKE_CUDA_ARCHITECTURES=61 \
  -DCMAKE_CUDA_COMPILER="C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v11.8/bin/nvcc.exe"
```

**Key flags explained:**
| Flag | Purpose |
|------|---------|
| `-DGGML_CUDA=ON` | Enable CUDA backend |
| `-DGGML_CUDA_MMQ=ON` | Enable MMQ (matrix multiplication quantization) — faster on Pascal+ |
| `-DCMAKE_CUDA_ARCHITECTURES=61` | Target sm_61 (GTX1060 Pascal). **Match your GPU exactly.** |
| `-DCMAKE_CUDA_COMPILER` | Explicit nvcc path — avoids detection failures |

### 3. Fix CMake CUDA Detection (Common Failure)

**Pitfall**: CMake's `cmake_nvcc_parse_implicit_info` fails on MSVC + CUDA 11.8 with "Implicit link extraction failed".

**Fix**: Patch `ggml/src/ggml-cuda/CMakeLists.txt` **before** building — pre-set the variables CMake fails to detect:

```cmake
# Insert near top of ggml/src/ggml-cuda/CMakeLists.txt
set(CMAKE_CUDA_COMPILER_ID "NVIDIA" CACHE INTERNAL "")
set(CMAKE_CUDA_COMPILER_VERSION "11.8" CACHE INTERNAL "")
set(CMAKE_CUDA_IMPLICIT_LINK_LIBRARIES "cudart" CACHE INTERNAL "")
set(CMAKE_CUDA_IMPLICIT_INCLUDE_DIRECTORIES "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v11.8/include" CACHE INTERNAL "")
set(CMAKE_CUDA_STANDARD_COMPUTED_DEFAULT "17" CACHE INTERNAL "")
set(CMAKE_CUDA_EXTENSIONS_COMPUTED_DEFAULT "ON" CACHE INTERNAL "")
set(CMAKE_CUDA_SIMULATE_VERSION "11.8" CACHE INTERNAL "")
```

**Why**: CMake's implicit link/introspection logic assumes CUDA 12+ MSVC integration. Hard-coding skips the broken detection.

### 4. Fix STL Version Mismatch (Common Failure)

**Pitfall**: MSVC STL header `yvals_core.h` emits `STL1002: Unexpected compiler version, expected CUDA 12.4 or newer` when compiling with CUDA 11.8.

**Fix**: Create `disable_cxx23.h` in project root and force-include via `CMAKE_CUDA_FLAGS` or `target_compile_options`:

```cpp
// disable_cxx23.h
#define _ALLOW_COMPILER_AND_STL_VERSION_MISMATCH 1
#define _HAS_CXX23 0
```

Add to CMake:
```cmake
add_compile_options("$<$<COMPILE_LANGUAGE:CUDA>:-include disable_cxx23.h>")
```

**Why**: MSVC 19.4x STL enforces CUDA version checks that reject 11.8. This macro disables the check.

### 5. Build

```bash
cmake --build build --config Release --target llama-server --parallel 4
```

**Expected artifacts in `build/bin/`:**
| File | Size | Notes |
|------|------|-------|
| `llama-server.exe` | ~10 KB | Stub launcher |
| `llama-server-impl.dll` | ~3-4 MB | Actual server logic |
| `ggml-cuda.dll` | ~90-100 MB | CUDA kernels (MMQ + sm_61) |
| `ggml-base.dll`, `llama.dll`, `llama-common.dll`, `mtmd.dll` | Various | Dependencies |

**Note**: `llama-server.exe` being small (10 KB) is normal — it's a thin entry point loading `llama-server-impl.dll`.

### 6. Runtime: CUDA DLL in PATH

**Pitfall**: `llama-server.exe` fails with Exit 127 / "cudart64_110.dll not found".

**Fix**: Ensure CUDA 11.8 `bin` directory is in PATH at runtime:
```bat
set PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin;%PATH%
```

### 7. Model: Reuse Ollama Blobs (Don't Re-download)

If the model exists in Ollama (`ollama list` shows it), **copy the blob directly** instead of exporting or re-downloading:

```bash
# 1. Find the model's blob via Ollama API
curl -X POST http://localhost:11434/api/show -H "Content-Type: application/json" -d "{\"model\":\"darkidol-rp:latest\"}"
# → returns "FROM D:\\Ai\\Ollama\\Models\\blobs\\sha256-<hash>"

# 2. Copy the blob to your models directory
copy D:\Ai\Ollama\Models\blobs\sha256-<hash> D:\Ai\models\DarkIdol-Qwen3.8-27B-v1.1.Q4_K_M.gguf
```

**Why `ollama cp` fails on Windows**: It writes to WSL/container filesystem; the file doesn't appear in Windows `D:\Ai\models\`. Direct blob copy is instant and reliable.

### 8. Run llama-server

```bat
set PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin;D:\Ai\llama.cpp-new\build\bin;%PATH%
cd /d D:\Ai\llama.cpp-new\build\bin
llama-server.exe --port 8080 --host 0.0.0.0 \
  --model D:\Ai\models\DarkIdol-Qwen3.8-27B-v1.1.Q4_K_M.gguf \
  --ctx-size 32768 --n-gpu-layers 6 --parallel 1 --api-prefix /v1
```

**Key runtime flags:**
| Flag | Value | Rationale |
|------|-------|-----------|
| `--n-gpu-layers 6` | 6 | GTX1060 6GB VRAM fits ~6 layers of 27B Q4_K_M |
| `--ctx-size 32768` | 32K | Model supports 262K; 32K balances VRAM/quality |
| `--api-prefix /v1` | /v1 | OpenAI-compatible endpoint at `/v1/*` |
| `--parallel 1` | 1 | Single slot — avoids VRAM OOM |

### 9. Verify

```bash
curl http://localhost:8080/v1/models
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"DarkIdol-Qwen3.8-27B-v1.1.Q4_K_M.gguf","messages":[{"role":"user","content":"Hello"}],"max_tokens":50}'
```

### 10. SillyTavern Integration

| Setting | Value |
|---------|-------|
| API Base URL | `http://localhost:8080/v1` |
| Model Name | `DarkIdol-Qwen3.8-27B-v1.1.Q4_K_M.gguf` |
| Format | OpenAI Compatible |

## Rollback

**One-click, zero side effects:**
```cmd
rmdir /s /q D:\Ai\llama.cpp-new\build
```

Ollama, system CUDA, and all other state untouched.

## GPU Architecture Reference

| GPU | Architecture | sm_ | CUDA Max |
|-----|--------------|-----|----------|
| GTX 1060 / 1070 / 1080 | Pascal | 61 | 11.8 |
| RTX 2060 / 2070 / 2080 | Turing | 75 | 12.x |
| RTX 3060 / 3070 / 3080 | Ampere | 86 | 12.x |
| RTX 4060 / 4070 / 4080 | Ada | 89 | 12.x |

**Rule**: Always match `CMAKE_CUDA_ARCHITECTURES` to your GPU's `sm_` exactly. Wrong value = silent fallback to CPU or build failure.

## Performance Expectations (GTX1060 6GB)

| Model | Quant | GPU Layers | tok/s (est.) |
|-------|-------|------------|--------------|
| Qwen2.5-7B | Q4_K_M | 6 (full) | ~9 |
| Qwen3.8-27B | Q4_K_M | 6 (partial) | ~2 |

27B exceeds 6GB VRAM — only partial offload. For full offload, need ≥24GB VRAM (RTX 3090/4090).

## Common Failure Matrix

| Symptom | Cause | Fix |
|---------|-------|-----|
| CMake: "Implicit link extraction failed" | CUDA 11.8 + MSVC detection broken | Pre-set CMake CUDA variables in ggml-cuda/CMakeLists.txt |
| Compile: `STL1002: expected CUDA 12.4+` | MSVC STL version check | `#define _ALLOW_COMPILER_AND_STL_VERSION_MISMATCH 1` |
| Runtime: Exit 127 / cudart64_110.dll missing | CUDA bin not in PATH | Add `CUDA/v11.8/bin` to PATH |
| `ollama cp` succeeds but file missing | WSL/Windows fs sync | Copy blob directly from `Ollama/Models/blobs/` |
| Build succeeds but llama-server.exe 10 KB | Normal — it's a stub | Real code in llama-server-impl.dll |
| Server returns 503 "Loading model" | Model still loading | Wait 30-60s for 27B model |
| OOM / CUDA out of memory | Too many GPU layers | Reduce `--n-gpu-layers` |

## Constraints from User Preferences

- **CUDA 11.8 only** — no 12.x (Pascal compatibility)
- **No re-download** if model exists in Ollama — reuse blob
- **Preserve Ollama** — never modify/remove Ollama models
- **One-click rollback** — build dir isolation
- **Verification-first** — test API endpoints before declaring done
- **Direct Chinese communication** — no AI fluff in outputs