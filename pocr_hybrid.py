# -*- coding: utf-8 -*-
"""p-ocr native + vLLM 混合管线（推荐）：native 预处理全套 use_* + VL 识别走 vLLM(8001)。

速度：约 22s/张（vs native 纯跑 ~126s）。保留截图全套 use_* 能力（方向/畸变/版面PP-DocLayoutV3/印章/图表）。
前提：WSL 里的 p-ocr-serve(vLLM, 8001) 运行中，模型名 paddleocr-vl-1.6。
"""
import os, sys, time
os.environ.setdefault("PADDLE_PDX_CACHE_HOME", r"C:\tmp\pocr_pd\models")
from paddleocr import PaddleOCRVL

VLLM_URL = "http://127.0.0.1:8001/v1"
VLLM_MODEL = "paddleocr-vl-1.6"

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
    vl_rec_server_url=VLLM_URL,
    vl_rec_api_model_name=VLLM_MODEL,
)


def ocr(image, outdir):
    """OCR one image, save markdown under outdir, return elapsed seconds."""
    os.makedirs(outdir, exist_ok=True)
    t0 = time.time()
    # Deterministic decoding for high-confidence, reproducible output.
    output = pipe.predict(
        image,
        temperature=0.0,
        top_p=1.0,
        repetition_penalty=1.1,
        max_new_tokens=8192,
    )
    dt = time.time() - t0
    for res in output:
        res.save_to_markdown(save_path=outdir)
    return dt


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: pocr_hybrid.py <image.png> [outdir]")
        sys.exit(2)
    img = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else r"C:\temp\A_out"
    dt = ocr(img, outdir)
    print("done in %.1fs -> %s" % (dt, outdir))
