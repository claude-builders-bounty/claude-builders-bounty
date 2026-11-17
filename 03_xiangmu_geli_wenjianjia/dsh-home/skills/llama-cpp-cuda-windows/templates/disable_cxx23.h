// Disable C++23 and STL version checks for CUDA 11.8 + MSVC compatibility
// Place in project root, force-include via CMAKE_CUDA_FLAGS

#define _ALLOW_COMPILER_AND_STL_VERSION_MISMATCH 1
#define _HAS_CXX23 0