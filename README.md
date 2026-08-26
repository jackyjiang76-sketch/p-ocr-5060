# p-ocr-5060

针对 **NVIDIA RTX 5060 (Blackwell, sm_120)** 配置好的 **PaddleOCR-VL-1.6** 文档解析技能。

一张文档图片 → 一份 Markdown。百度 PaddlePaddle 生态，中文文档/工程图纸识别表现优秀。

## 背景与定位

- 模型：PaddlePaddle/PaddleOCR-VL-1.6-0.9B（0.9B 视觉-语言模型，OmniDocBench v1.6 官方评测 96.34 分第二名，Apache-2.0）
- 硬件：RTX 5060（sm_120）——**RTX 50 系（sm_120）需要 CUDA 12.9 的 Paddle**，否则报 `Mismatched GPU Architecture`
- 部署：**native 预处理 + vLLM 混合管线**（保留截图全套 use_* 能力，同时用 vLLM 加速 VL 生成）

## 目录结构

```
├── SKILL.md                  # 技能定义（agent 用）
├── scripts/p_ocr_client.py   # vLLM 客户端（含 LOC token 清洗）
├── 配置说明.md                # 完整配置与排障速查（含踩坑记录）
├── pocr_hybrid.py            # 单张入口：native+vLLM 混合管线
├── run_40.py                 # 批量入口（默认 8 张/批）
├── batch_ocr_dir.py          # 目录批量入口
├── convert_40.py             # PDF → 200dpi PNG（批）
├── pdf_to_png.py             # PDF → PNG 单张
├── patch_flashinfer.sh       # flashinfer JIT 编译补丁（cu13/lib64 链接）
├── render_pdf.sh / run_pocr.sh  # WSL 侧辅助脚本
└── README.md
```

## 关键结论（实测）

| 项 | 值 |
|----|----|
| 显存参数 | `--gpu-memory-utilization 0.55` |
| 批量大小 | **8 张/批（最优）** |
| 均摊速度 | **~12.7 s/张**（确定性 temperature=0） |
| 确定性 | temperature=0 贪心解码，可复现 |

## 使用前提

1. WSL2 + systemd，p-ocr-serve(vLLM 0.22.1, 端口 8001) 运行中，served-model-name `paddleocr-vl-1.6`
2. Windows venv：`paddlepaddle-gpu 3.3.1`（**cu129 源**，支持 sm_120）+ `paddleocr 3.7.0` + `paddlex 3.7.2`

## 快速开始

```bash
# 单张
python pocr_hybrid.py <图.png> [输出目录]

# 目录批量（8张/批）
python run_40.py 8

# 目录批量（自定义批）
python batch_ocr_dir.py <图片目录> [输出目录]
```

## 重要坑（详见 配置说明.md）

- 混合管线必须传 `temperature=0.0`，否则 vLLM 随机采样导致结果不可复现
- flashinfer JIT 编译需 `nvidia/cu13/lib64` 下有 `libcudart.so`/`libcuda.so` 符号链接
- 纯矢量 CAD 导出 PDF（无文字层）OCR 拿不到文字，需回 DWG 走 cad-text-parser
