# llama.cpp Windows CUDA Build — Troubleshooting Quick Reference

## CMake Configuration Failures

### "Implicit link extraction failed" / cmake_nvcc_parse_implicit_info
**Context**: CMake tries to detect CUDA compiler implicit link flags by compiling a test program and parsing nvcc output. Fails on CUDA 11.8 + MSVC 2022.

**Fix**: Pre-set these variables in `ggml/src/ggml-cuda/CMakeLists.txt` before `project()` or `enable_language(CUDA)`:
```cmake
set(CMAKE_CUDA_COMPILER_ID "NVIDIA" CACHE INTERNAL "")
set(CMAKE_CUDA_COMPILER_VERSION "11.8" CACHE INTERNAL "")
set(CMAKE_CUDA_IMPLICIT_LINK_LIBRARIES "cudart" CACHE INTERNAL "")
set(CMAKE_CUDA_IMPLICIT_INCLUDE_DIRECTORIES "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v11.8/include" CACHE INTERNAL "")
set(CMAKE_CUDA_STANDARD_COMPUTED_DEFAULT "17" CACHE INTERNAL "")
set(CMAKE_CUDA_EXTENSIONS_COMPUTED_DEFAULT "ON" CACHE INTERNAL "")
set(CMAKE_CUDA_SIMULATE_VERSION "11.8" CACHE INTERNAL "")
```

### "CUDA compiler not found" / nvcc missing
**Fix**: Explicit `-DCMAKE_CUDA_COMPILER="C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v11.8/bin/nvcc.exe"`

## Compilation Failures

### `STL1002: Unexpected compiler version, expected CUDA 12.4 or newer`
**File**: `yvals_core.h` (MSVC STL)
**Cause**: MSVC 19.4x STL has hardcoded CUDA version check that rejects CUDA < 12.4.
**Fix**: Force-include header with `#define _ALLOW_COMPILER_AND_STL_VERSION_MISMATCH 1`
```cmake
add_compile_options("$<$<COMPILE_LANGUAGE:CUDA>:-include disable_cxx23.h>")
```

### `ggml-cuda.cu` errors about `__half` / `__nv_bfloat16`
**Cause**: CUDA 11.8 headers + newer MSVC STL conflicts.
**Fix**: Same as above — `_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH` disables the version gate.

## Link Failures

### LNK2019 / unresolved external symbols from ggml-cuda
**Cause**: CUDA libraries not linked.
**Fix**: Ensure `cudart.lib` in link libraries (handled by pre-set `CMAKE_CUDA_IMPLICIT_LINK_LIBRARIES`).

## Runtime Failures

### Exit 127 / "The application was unable to start correctly"
**Cause**: Missing `cudart64_110.dll` or other CUDA runtime DLLs in PATH.
**Fix**: `set PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin;%PATH%`

### `llama-server.exe` runs but returns 503 "Loading model" indefinitely
**Cause**: Large model (27B) takes 30-60s to load into VRAM+RAM.
**Fix**: Wait. Check logs for `load_model: initializing` → `model loaded`.

### CUDA_OUT_OF_MEMORY / `ggml_cuda_malloc` failed
**Cause**: `--n-gpu-layers` too high for VRAM.
**Fix**: Reduce `--n-gpu-layers`. GTX1060 6GB: max ~6 layers for 27B Q4_K_M.

### Model loads but inference is extremely slow (< 0.5 tok/s)
**Cause**: Model running on CPU (GPU layers not actually offloaded).
**Fix**: Verify `ggml-cuda.dll` loaded (check logs for `ggml_cuda_init: Found N GPU devices`). Ensure `--n-gpu-layers > 0`.

## Model Loading Failures

### `tensor 'blk.XX.ffn_up.weight' data is not within the file bounds`
**Cause**: Corrupted/incomplete GGUF download.
**Fix**: Re-download or verify file size matches expected (27B Q4_K_M ≈ 16 GB).

### `ollama cp` succeeds but file not found
**Cause**: WSL/Windows filesystem isolation.
**Fix**: Use direct blob copy (see `references/ollama-blob-reuse.md`).

## Verification Checklist

After build, before declaring success:
- [ ] `llama-server.exe --help` runs (shows usage, not DLL error)
- [ ] `dumpbin /dependents build/bin/llama-server-impl.dll` shows `cudart64_110.dll`
- [ ] `curl /v1/models` returns 200 with model list
- [ ] `curl /v1/chat/completions` returns valid completion
- [ ] Response includes `timings.predicted_per_second` > 0
- [ ] GPU utilization visible in `nvidia-smi` during inference