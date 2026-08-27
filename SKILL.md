---
name: p-ocr-5060
description: 端到端文档解析 OCR，基于 PaddleOCR-VL-1.6（百度，0.9B，OmniDocBench v1.6 官方评测 96.34 分第二名，Apache-2.0）。输入图片/截图/扫描件，输出自然阅读顺序的 Markdown。本地 WSL2 + vLLM 0.22.1 部署（官方 README 推荐的"优化推理服务器"加速路径），走 OpenAI 兼容接口 POST /v1/chat/completions。Use when the user asks to OCR a document image with PaddleOCR-VL, mentions "p-ocr", "PaddleOCR-VL", "PP-OCRv6", or wants Paddle ecosystem document parsing to Markdown (图片转markdown, 文档解析, PaddleOCR). Triggers include "p-ocr", "PaddleOCR-VL", "PaddleOCR-VL-1.6".
---

# p-ocr-skill（PaddleOCR-VL-1.6 端到端文档解析）

离线本地推理：**一张文档图片 → 一份 Markdown**。百度 PaddlePaddle 生态，中文文档识别表现优秀。

## 输入分流（重要：先判类型再选工具）

**本 skill（p-ocr）只对"位图/扫描型"输入有效。** 拿到 PDF/图片后，**必须先判定类型**，否则会白跑或得到空结果：

| 类型判定 (metrics) | 含义 | 应走工具 |
|---|---|---|
| `SCAN`：imgs>0 且 textlen<20 | 位图扫描件（真扫描/照片） | **本 skill（p-ocr 混合管线）** |
| `VECTOR`：imgs=0, textlen=0, drawings>50 | 纯矢量 CAD 线图，无文字层 | **不用 p-ocr**，转 `cad-text-parser`（DWG/DXF 源文件） |
| `TEXT`：textlen>=20 且 imgs=0 | 有文字层的 PDF | **直接 pymupdf get_text**，无需 OCR |
| `MIXED`：textlen>=20 且 imgs>0 | 文字+图片混合 | 文字层直接提，图片块交 p-ocr |

路由脚本：`python route.py <pdf|png|jpg>`（输出 kind + metrics + 建议工具）。**注意**：p-ocr 是"单图→Markdown"，输入须先渲染成 PNG（`convert_40.py` / `pdf_to_png.py`），且只处理 SCAN/MIXED 的图片块。

**已实测（40 张人防图纸）**：16 张真扫描（OCR 有效），24 张矢量 CAD 导出（`textlen=0,imgs=0,deep_img=0,red≈0`——无文字层、无内嵌图片、无红章；OCR 拿不到任何内容，须回 DWG 走 cad-text-parser）。**对 VECTOR 输入，OCR 没有就是没有，不要硬跑。**

## 快速使用

在 Windows 侧（Git Bash / PowerShell）执行：

```bash
MSYS_NO_PATHCONV=1 wsl -d Ubuntu -- /root/.tools/p-ocr/.venv/bin/python /mnt/c/Users/justin/.tools/p-ocr/p_ocr_client.py "C:\path\to\image.jpg" "C:\path\to\out.md"
```

- 客户端用 **p-ocr 自己的独立 venv**（`/root/.tools/p-ocr/.venv`），完全不依赖 o-ocr 环境。

- 第一个参数：图片路径（Windows 风格或 /mnt/c 风格均可）
- 第二个参数（可选）：Markdown 输出路径；不传则只打印到 stdout
- 脚本自带服务自愈：health 不通时自动 `systemctl restart p-ocr-serve` 并等待就绪（最长 300s）

## 架构（官方部署路径）

| 组件 | 说明 |
|------|------|
| 模型 | PaddlePaddle/PaddleOCR-VL-1.6-0.9B（官方完整版，Apache-2.0） |
| 权重位置 | WSL 内 /root/.tools/p-ocr/model（ModelScope 官方源下载的 bf16 原始权重） |
| 推理引擎 | vLLM 0.22.1（vLLM 内置 paddleocr_vl 模型支持，官方 README "Optimized Inference Servers" 路线） |
| 服务 | systemd 单元 p-ocr-serve，端口 8001，API：POST /v1/chat/completions（OpenAI 兼容） |
| 提示词 | 客户端内置文档解析提示词（Extract all readable content...Markdown/LaTeX/HTML 表格） |

## 备选路径（Windows 原生 PaddleX，官方基础用法）

Windows 侧另有官方 venv：`C:\Users\justin\.tools\p-ocr\.venv`（paddlepaddle-gpu 3.2.1 cu126 + paddleocr[doc-parser]，按官方 README 安装）。
基础用法（官方 README 原文）：

```python
from paddleocr import PaddleOCRVL
pipeline = PaddleOCRVL(pipeline_version="v1.6")
output = pipeline.predict("image.png")
for res in output:
    res.save_to_markdown(save_path="output")
```

注意：本机 RTX 5060（sm_120）不被 paddle-inference 静态图支持（报 Unsupported GPU architecture），原生路径需 `device="cpu"` 或走本 skill 的 vLLM 服务器路径（推荐）。

## 排障速查

- 服务状态：`wsl -d Ubuntu -- systemctl status p-ocr-serve`
- 日志：`wsl -d Ubuntu -- journalctl -u p-ocr-serve -n 50 --no-pager`
- 健康检查：`curl http://127.0.0.1:8001/health`

## 已踩坑清单（环境部署时按官方文档逐一解决，勿重复踩）

1. **PaddlePaddle 版本必须 ≥ 3.2.1 + 特殊版 safetensors**（官方 README 原文）；3.0.0.dev 会报 bf16 权重无法加载、fused_rms_norm_ext 内核缺失。
2. **Windows 原生 Paddle 不支持 bf16 张量**：vLLM 服务器路径（本 skill 默认）无此问题，不要自行转 fp16。
3. **WSL 实例 15 秒自动终止**：.wslconfig 必须含 `[general] instanceIdleTimeout=-1`。
4. **vLLM 编译 PaddleOCR-VL 内核需要完整工具链**：build-essential（gcc）+ ninja-build + CUDA_HOME（指向 pip 版 nvidia/cu13，含 nvcc）。
5. **flashinfer 0.6.11 JIT 编译两处本地补丁**（环境已打好，重装 venv 需重打）：
   - flashinfer/data/cccl/libcudacxx/include/cuda/std/__cccl/cuda_toolkit.h 第 41 行兼容性 #error 已注释（nvcc 13.3 vs 头文件 13.0 的版本检查）；
   - nvidia/cu13/lib 下已建 libcudart.so、libcuda.so 无版本号符号链接（链接 -lcudart/-lcuda 用）。
6. **显存独占（重要）**：本机 8GB 显卡**不能**同时跑 p-ocr(8001) 和 o-ocr(8000)。两者各占 0.4 gpu-memory-utilization 会 OOM（`No available memory for the cache blocks`），p-ocr 冷启动失败。→ **只跑 p-ocr，独占显卡**；o-ocr 相关服务/进程需彻底停掉（仅 `systemctl disable` 不够，还要 `kill` 孤儿进程），首次冷启动约 40-90 秒。
7. vLLM 0.22.1 对 PaddleOCR-VL 挂载的是标准 OpenAI API（/v1/chat/completions），不是 /ocr 路由。
