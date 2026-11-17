# CUDA Compute Capability Quick Reference

| GPU Series | Architecture | Compute Capability (sm_) | Max CUDA Version |
|------------|--------------|--------------------------|------------------|
| GeForce 600/700 | Kepler | 30, 35, 37 | 11.x |
| GeForce 900 | Maxwell | 50, 52, 53 | 11.x |
| **GeForce 10 (GTX 1060/1070/1080)** | **Pascal** | **61** | **11.8** |
| GeForce 16 | Turing | 75 | 12.x |
| **GeForce 20 (RTX 2060/2070/2080)** | **Turing** | **75** | **12.x** |
| GeForce 30 (RTX 3060/3070/3080) | Ampere | 86 | 12.x |
| GeForce 40 (RTX 4060/4070/4080) | Ada | 89 | 12.x |
| GeForce 50 (RTX 50-series) | Blackwell | 120 | 12.x |
| Tesla V100 | Volta | 70 | 12.x |
| A100 | Ampere | 80 | 12.x |
| H100 | Hopper | 90 | 12.x |

**Rule for CMake**: `-DCMAKE_CUDA_ARCHITECTURES=<sm_>` must match exactly. Multiple values = fat binary (larger, slower to compile). Single value = optimal.

**Pascal (sm_61) Specifics**:
- Last architecture supported by CUDA 11.8
- MMQ (`GGML_CUDA_MMQ=ON`) supported and recommended
- No Tensor Cores — MMQ uses CUDA cores
- FP16 supported, BF16 not supported
- Max 6 GB VRAM on GTX1060 → limits model size for full offload

**VRAM Estimation for Q4_K_M (4-bit):**
- 7B model: ~4.5 GB → full offload on 6 GB
- 13B model: ~8 GB → partial offload on 6 GB
- 27B model: ~16 GB → partial offload (6 layers) on 6 GB
- 70B model: ~40 GB → needs 48+ GB (multi-GPU or CPU offload)