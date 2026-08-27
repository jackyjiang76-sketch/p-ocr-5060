# -*- coding: utf-8 -*-
"""p-ocr-5060 输入路由：判定 PDF/图片类型，分流到正确工具。

- SCAN   (位图扫描件)          -> p-ocr 混合管线 (pocr_hybrid.py / run_40.py)
- VECTOR (纯矢量线图, 无文字层) -> cad-text-parser (DWG/DXF 源文件) —— PDF 本身无文字
- TEXT   (有文字层 PDF)        -> 直接文字提取 (pymupdf get_text, 无需 OCR)
- MIXED  (有图也有文字)        -> 文字层直接提 + 图片块 p-ocr

用法: python route.py <pdf或png路径>
输出: 判定结果 + 建议工具 + 关键指标 (textlen/imgs/drawings/red%)
"""
import os, sys
import pymupdf

THRESH_TEXT = 20      # 文字层长度阈值
THRESH_DRAW = 50      # 矢量线条数阈值（>50 视为矢量图）


def classify(path):
    """Return (kind, metrics) for a pdf/png file."""
    if path.lower().endswith((".pdf")):
        doc = pymupdf.open(path)
        page = doc[0]
        text = page.get_text().strip()
        nimg = len(page.get_image_info())
        # deep image scan (incl. nested)
        deep = 0
        for xref in range(1, doc.xref_length()):
            try:
                sub = doc.xref_get_key(xref, "Subtype")
                if sub and sub[1] == "/Image":
                    deep += 1
            except Exception:
                pass
        ndraw = len(page.get_drawings())
        doc.close()
        metrics = dict(textlen=len(text), imgs=nimg, deep_img=deep, drawings=ndraw)
        if len(text) >= THRESH_TEXT and nimg == 0:
            kind = "TEXT"
        elif len(text) >= THRESH_TEXT and nimg > 0:
            kind = "MIXED"
        elif nimg > 0:
            kind = "SCAN"
        elif ndraw > THRESH_DRAW:
            kind = "VECTOR"
        else:
            kind = "BLANK"
        return kind, metrics

    elif path.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".bmp")):
        return "SCAN", dict(textlen=0, imgs=0, deep_img=0, drawings=0)  # 位图文件->OCR

    else:
        return "UNKNOWN", dict(textlen=0, imgs=0, deep_img=0, drawings=0)


ROUTE = {
    "SCAN": "p-ocr 混合管线（pocr_hybrid.py / run_40.py）",
    "VECTOR": "cad-text-parser（DWG/DXF 源文件）—— PDF 无文字层，需 DWG 的 TEXT/MTEXT/块属性",
    "TEXT": "直接文字提取（pymupdf get_text）—— 无需 OCR",
    "MIXED": "文字层直接提取 + 图片块交 p-ocr",
    "BLANK": "无内容，检查源文件",
    "UNKNOWN": "无法识别的格式",
}


def main():
    if len(sys.argv) < 2:
        print("usage: python route.py <pdf|png|jpg>")
        sys.exit(2)
    for p in sys.argv[1:]:
        if not os.path.exists(p):
            print("not found:", p)
            continue
        kind, m = classify(p)
        print("%s" % os.path.basename(p))
        print("  kind    : %s" % kind)
        print("  metrics : textlen=%d imgs=%d deep_img=%d drawings=%d" % (
            m["textlen"], m["imgs"], m["deep_img"], m["drawings"]))
        print("  route   : %s" % ROUTE.get(kind, "?"))
        print()


if __name__ == "__main__":
    main()
