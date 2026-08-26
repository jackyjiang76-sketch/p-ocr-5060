#!/bin/bash
# Run the p-ocr client on an image. Args: <image_windows_path> [out_md_windows_path]
# The client script lives on the Windows side, reachable via /mnt/c from WSL.
# Uses p-ocr's own independent venv (no dependency on o-ocr environment).
set -e
PY=/root/.tools/p-ocr/.venv/bin/python
CLIENT=/mnt/c/Users/justin/.tools/p-ocr/p_ocr_client.py
"$PY" "$CLIENT" "$1" "${2:-}"
