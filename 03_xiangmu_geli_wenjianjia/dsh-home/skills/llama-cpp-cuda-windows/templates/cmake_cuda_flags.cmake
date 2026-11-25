# llama.cpp CUDA CMake flags for Windows + MSVC + CUDA 11.8
# Include this in your CMake command or CMakeLists.txt

# Core CUDA enablement
-DGGML_CUDA=ON \
-DGGML_CUDA_MMQ=ON \

# Target architecture — CHANGE FOR YOUR GPU
# GTX 1060/1070/1080 (Pascal) = 61
# RTX 2060/2070/2080 (Turing) = 75
# RTX 3060/3070/3080 (Ampere) = 86
# RTX 4060/4070/4080 (Ada) = 89
-DCMAKE_CUDA_ARCHITECTURES=61 \

# Explicit compiler (avoids detection issues)
-DCMAKE_CUDA_COMPILER="C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v11.8/bin/nvcc.exe" \

# Build type
-DCMAKE_BUILD_TYPE=Release \

# Generator
-G "Visual Studio 17 2022"