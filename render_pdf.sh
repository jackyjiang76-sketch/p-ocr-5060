#!/bin/bash
# Render a PDF page to PNG at 200 dpi using pymupdf venv.
# Args: <pdf_wsl_path> <page0> <out_png_wsl_path> [dpi]
set -e
PY=/root/.tools/pdfp/bin/python
SCRIPT=/mnt/c/Users/justin/Documents/工程量清单编制/pdf_to_png.py
"$PY" "$SCRIPT" "$1" "$2" "$3" "${4:-200}"
