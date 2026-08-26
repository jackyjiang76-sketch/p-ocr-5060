# -*- coding: utf-8 -*-
"""Batch OCR a whole directory via native+vLLM hybrid pipeline (dir input)."""
import os, sys, time, glob
os.environ.setdefault("PADDLE_PDX_CACHE_HOME", r"C:\tmp\pocr_pd\models")
from paddleocr import PaddleOCRVL

pipe = PaddleOCRVL(
    pipeline_version="v1.6",
    use_doc_orientation_classify=True,
    use_doc_unwarping=True,
    use_layout_detection=True,
    use_chart_recognition=True,
    use_seal_recognition=True,
    use_ocr_for_image_block=True,
    format_block_content=True,
    merge_layout_blocks=True,
    vl_rec_backend="vllm-server",
    vl_rec_server_url="http://127.0.0.1:8001/v1",
    vl_rec_api_model_name="paddleocr-vl-1.6",
)

d = sys.argv[1] if len(sys.argv) > 1 else r"C:\ocr_job\batch5"
out = sys.argv[2] if len(sys.argv) > 2 else r"C:\ocr_job\out"
os.makedirs(out, exist_ok=True)
imgs = sorted(glob.glob(os.path.join(d, "*.png")))
print("input dir:", d, "count:", len(imgs), flush=True)

t0 = time.time()
output = pipe.predict(d, temperature=0.0, top_p=1.0, repetition_penalty=1.1, max_new_tokens=8192)
dt = time.time() - t0
n = len(imgs)
print("TOTAL %.1fs for %d imgs => %.2f s/img" % (dt, n, dt / n), flush=True)
for res in output:
    res.save_to_markdown(save_path=out)
print("saved to", out, flush=True)
