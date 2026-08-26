# -*- coding: utf-8 -*-
"""Run all 40 PNGs through the hybrid pipeline in batches of N, collecting markdown."""
import os, sys, time, glob, shutil
os.environ.setdefault("PADDLE_PDX_CACHE_HOME", r"C:\tmp\pocr_pd\models")
from paddleocr import PaddleOCRVL

PNG = r"C:\ocr_job\png"
OUTROOT = r"C:\ocr_job\out40"
BATCH = int(sys.argv[1]) if len(sys.argv) > 1 else 36
os.makedirs(OUTROOT, exist_ok=True)

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

imgs = sorted(glob.glob(os.path.join(PNG, "*.png")))
print("total imgs:", len(imgs), flush=True)

# collect markdown outputs into OUTROOT by copying from per-batch temp dirs
all_t0 = time.time()
for bi in range(0, len(imgs), BATCH):
    chunk = imgs[bi:bi + BATCH]
    tmpdir = os.path.join(OUTROOT, "_tmp%d" % bi)
    os.makedirs(tmpdir, exist_ok=True)
    for p in chunk:
        shutil.copy(p, tmpdir)
    t0 = time.time()
    try:
        # Deterministic decoding for high-confidence, reproducible output.
        output = pipe.predict(
            tmpdir,
            temperature=0.0,
            top_p=1.0,
            repetition_penalty=1.1,
            max_new_tokens=8192,
        )
        dt = time.time() - t0
        print("batch %d-%d: %d imgs in %.1fs (%.2f s/img)" % (bi + 1, bi + len(chunk), len(chunk), dt, dt / len(chunk)), flush=True)
        for res in output:
            res.save_to_markdown(save_path=OUTROOT)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("batch %d FAILED: %s" % (bi, e), flush=True)
    # cleanup tmp images
    for p in glob.glob(os.path.join(tmpdir, "*.png")):
        os.remove(p)

print("ALL DONE in %.1fs for %d imgs (%.2f s/img)" % (time.time() - all_t0, len(imgs), (time.time() - all_t0) / len(imgs)), flush=True)
