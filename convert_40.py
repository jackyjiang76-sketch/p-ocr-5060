# -*- coding: utf-8 -*-
"""Convert the 40 needs_ocr PDFs to 200dpi PNG (capped size) into an ascii dir."""
import json, os
import pymupdf

ROOT = r"C:\Users\justin\Documents\工程量清单编制"
NEO = os.path.join(ROOT, "_extracted", "needs_ocr.json")
OUT = r"C:\ocr_job\png"
os.makedirs(OUT, exist_ok=True)

data = json.load(open(NEO, encoding="utf-8"))
files = [f["file"] for f in data["files"]]
print("total files:", len(files), flush=True)

ok, fail = 0, 0
for i, rel in enumerate(files, 1):
    pdf = os.path.join(ROOT, rel)
    name = os.path.basename(rel)
    stem = os.path.splitext(name)[0]
    out = os.path.join(OUT, "%02d_%s.png" % (i, stem))
    if os.path.exists(out):
        print("skip exists", i, stem, flush=True)
        continue
    try:
        doc = pymupdf.open(pdf)
        base_dpi = 200
        pix0 = doc[0].get_pixmap(dpi=base_dpi)
        scale = min(1.0, 2600.0 / max(pix0.width, pix0.height))
        dpi = int(round(base_dpi * scale))
        if dpi < 72:
            dpi = 72
        pix = doc[0].get_pixmap(dpi=dpi)
        pix.save(out)
        doc.close()
        ok += 1
        print("%02d OK %s (%dx%d)" % (i, stem, pix.width, pix.height), flush=True)
    except Exception as e:
        fail += 1
        print("%02d FAIL %s: %s" % (i, stem, e), flush=True)

print("DONE ok=%d fail=%d" % (ok, fail), flush=True)
