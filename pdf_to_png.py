# -*- coding: utf-8 -*-
"""Render a PDF page to a PNG at 200 DPI for OCR input.

Usage: python pdf_to_png.py <pdf> [page0 = 0] [out.png] [dpi = 200]
"""
import os
import sys

def render(src, page0, out, dpi):
    # Preferred: PyMuPDF if available, else pdf2image (needs poppler).
    try:
        import fitz  # PyMuPDF
    except ImportError:
        fitz = None
    if fitz is not None:
        doc = fitz.open(src)
        page = doc[page0]
        pix = page.get_pixmap(dpi=dpi)
        pix.save(out)
        doc.close()
        return "pymupdf:%dxx%d" % (pix.width, pix.height)
    try:
        from pdf2image import convert_from_path
    except ImportError:
        raise SystemExit("no pdf renderer: install pymupdf or pdf2image+poppler")
    pages = convert_from_path(src, dpi=dpi, first_page=page0 + 1, last_page=page0 + 1)
    pages[0].save(out)
    return "pdf2image:%dx%d" % pages[0].size[0], pages[0].size[1]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: pdf_to_png.py <pdf> [page0] [out.png] [dpi]")
    src = sys.argv[1]
    page0 = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    base = os.path.splitext(os.path.basename(src))[0]
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(src), base + ".png")
    dpi = int(sys.argv[4]) if len(sys.argv) > 4 else 200
    info = render(src, page0, out, dpi)
    print("rendered %s -> %s (%s) at %d dpi" % (os.path.basename(src), out, info, dpi))
