# -*- coding: utf-8 -*-
"""p-ocr-skill client: PaddleOCR-VL-1.6 (0.9B) via vLLM 0.22.1 OpenAI chat API in WSL2.

Official accelerated path per PaddleOCR-VL-1.6 README ("Optimized Inference Servers").
Service: systemd unit p-ocr-serve, port 8001, endpoint POST /v1/chat/completions.
"""
import base64, json, re, subprocess, sys, time, urllib.request

# PaddleOCR-VL emits coordinate-regression tokens like <|LOC_311|><|LOC_118|>...
# which are layout metadata, not readable text. Strip them before returning.
LOC_RE = re.compile(r"<\|LOC_\d+\|>")

PORT = 8001
SERVICE = "p-ocr-serve"

PROMPT = ("请按自然阅读顺序提取图片中的所有可读内容，输出为一份 Markdown 文档。"
          "表格用 HTML 表格表示，公式用 LaTeX 表示。不要翻译，保持原文。")


def to_wsl(p):
    if p.startswith("/"):
        return p
    r = subprocess.run(["wslpath", "-u", p], capture_output=True, text=True)
    return r.stdout.strip()


def health():
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/health" % PORT, timeout=3) as r:
            return r.getcode() == 200
    except Exception:
        return False


def ensure_up(max_wait=300):
    if health():
        return
    subprocess.run(["systemctl", "restart", SERVICE], check=False)
    t0 = time.time()
    while time.time() - t0 < max_wait:
        if health():
            return
        time.sleep(5)
    raise RuntimeError("%s not healthy within %ds" % (SERVICE, max_wait))


def ocr(img, out=None):
    ensure_up()
    img = to_wsl(img)
    b64 = base64.b64encode(open(img, "rb").read()).decode()
    payload = {
        "model": "paddleocr-vl-1.6",
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}},
            {"type": "text", "text": PROMPT},
        ]}],
        "max_tokens": 8192,
        "temperature": 0.0,
        "repetition_penalty": 1.1,
    }
    req = urllib.request.Request(
        "http://127.0.0.1:%d/v1/chat/completions" % PORT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    j = json.load(urllib.request.urlopen(req, timeout=900))
    raw = j["choices"][0]["message"]["content"]
    # Clean: drop coordinate tokens and collapse the stray blank lines they leave.
    md = LOC_RE.sub("", raw)
    md = re.sub(r"[ \t]+\n", "\n", md)
    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    if out:
        open(to_wsl(out), "w", encoding="utf-8").write(md)
    return md


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: p_ocr_client.py <image> [out.md]")
        sys.exit(2)
    md = ocr(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print(md)
