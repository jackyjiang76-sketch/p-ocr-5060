#!/bin/bash
# Patch flashinfer CUDA toolchain for the p-ocr independent venv.
# Run after creating the venv and installing vllm/flashinfer, BEFORE first `vllm serve`.
# Fixes two JIT-compile/link pitfalls on RTX 5060 (sm_120):
#   1) cuda_toolkit.h #error for nvcc 13.3 vs headers 13.0.
#   2) nvidia/cu13 has `lib` but no `lib64`; flashinfer's ninja link uses -L.../lib64
#      and requires `-lcudart`/`-lcuda` symlinks there.
set -e
VENV=/root/.tools/p-ocr/.venv
SP="$VENV/lib/python3.13/site-packages"
TK="$SP/flashinfer/data/cccl/libcudacxx/include/cuda/std/__cccl/cuda_toolkit.h"
CU="$SP/nvidia/cu13"

# --- patch1: comment out the compatibility #error ---
echo "[patch1] comment out CTK-compat #error in cuda_toolkit.h"
if grep -q '// #      error "CUDA compiler and CUDA toolkit' "$TK"; then
  echo "  already patched"
else
  python3 - "$TK" <<'PY'
import sys
p = sys.argv[1]
lines = open(p, encoding="utf-8").read().splitlines()
out = []
for ln in lines:
    if 'error "CUDA compiler and CUDA toolkit headers are incompatible' in ln:
        ln = "// " + ln
    out.append(ln)
open(p, "w", encoding="utf-8").write("\n".join(out) + "\n")
PY
  echo "  patched #error -> // #error"
fi

# --- patch2: create cu13/lib64 with cudart/cuda symlinks ---
echo "[patch2] create nvidia/cu13/lib64 symlinks"
L64="$CU/lib64"
mkdir -p "$L64"
# libcuda.so must point to the WSL-provided libcuda; libcudart.so to the .so.13 body.
if [ ! -e "$L64/libcuda.so" ]; then
  ln -s /usr/lib/wsl/lib/libcuda.so.1 "$L64/libcuda.so"
  echo "  created lib64/libcuda.so -> /usr/lib/wsl/lib/libcuda.so.1"
fi
if [ ! -e "$L64/libcudart.so" ]; then
  ln -s "$CU/lib/libcudart.so.13" "$L64/libcudart.so"
  echo "  created lib64/libcudart.so -> $CU/lib/libcudart.so.13"
fi

echo "=== verify patch1 ==="
grep -n '// #      error "CUDA compiler' "$TK" || echo "WARN: #error not found/commented"
echo "=== verify patch2 ==="
ls -la "$L64" | grep -iE 'libcudart.so|libcuda.so'
echo "--- done ---"
