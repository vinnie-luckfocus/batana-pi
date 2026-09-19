# spikes/uvc-probe — UVC 相机冒烟探针

M0 G0 阶段门验证工具：OV9281 双目 USB3 模组（合并单流 2560×800 side-by-side，
目标 120fps 无压缩 MONO8/YUY2，UVC 免驱）到货后即插即测。macOS（开发机）
与 Linux（ROCK 5B+ / 泰山派3M）通用。

## 环境准备

```bash
cd spikes/uvc-probe
uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt
# 或：python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

依赖：

- macOS：ffmpeg（`brew install ffmpeg`）+ Python venv 内的 opencv-python-headless、numpy
- Linux：`v4l2-ctl`（`apt install v4l-utils`）+ 同上 Python 依赖

## 用法

### 1. 枚举格式（先确认模组宣传参数为真）

```bash
# macOS（--device 为 avfoundation 序号，缺省枚举全部相机）
.venv/bin/python list_formats.py

# Linux（--device 为 /dev/videoN）
.venv/bin/python list_formats.py --device /dev/video0 --json formats.json
```

输出：每台设备的分辨率/帧率/像素格式表格 + JSON，并对目标模式
2560×800@120 给出判定（可用 `--width/--height/--fps` 改目标）。

注意：macOS 的 avfoundation 无法给出「分辨率 ↔ 像素格式」对应关系，
只能分别列出全局模式表与全局像素格式表；精确对应关系以 Linux
`v4l2-ctl --list-formats-ext` 或 capture_smoke 实测协商结果为准。

### 2. 抓帧冒烟（默认 10 分钟）

```bash
# MONO8 2560×800@120（双目合并流，会定时把左右目切开存样张）
.venv/bin/python capture_smoke.py --device /dev/video0 \
    --width 2560 --height 800 --fps 120 --format GREY \
    --duration 10 --out-dir out/run1

# 快速冒烟（10 秒）
.venv/bin/python capture_smoke.py --device 0 --width 1280 --height 720 \
    --fps 30 --format YUY2 --duration 0.167
```

输出：

- `out/run1/frames.csv`：逐帧记录（帧号、时间戳、帧间隔、读取是否成功、该间隔估算掉帧数）
- `out/run1/samples/`：MONO8 模式下按 `--sample-interval`（默认 60s）保存的左右目样张 PNG
- 终端摘要：实际帧率、掉帧率、帧间隔抖动 p50/p95/max、判定

## 判读标准

| 指标 | 通过标准 |
| --- | --- |
| 掉帧率 | < 0.1%（帧间隔 > 1.5× 标称间隔即估算掉帧） |
| 实际帧率 | ≥ 标称 × 99%（120fps 档即 ≥118.8fps） |
| 帧间隔 p95 | 与 p50 同量级；max 无系统性长尾（偶发尖峰可接受） |
| 像素格式 | 协商结果为 GREY/YUY2 无压缩，而非回退 MJPG |
| 双目样张 | 左右目画面内容一致（同一时刻、各自半幅），无撕裂/错位 |

脚本退出码：掉帧率 < 0.1% 为 0（通过），否则为 1。

## 到货后操作步骤

1. 模组接 ROCK 5B+ 任一 USB3 口（Type-C 全功能口默认 host 可直插），
   `lsusb` 确认枚举为 **SuperSpeed**（5000M 及以上；480M = USB2 假 USB3，直接退货）
2. `list_formats.py --device /dev/video0 --json formats.json`：确认含
   2560×800@120 且该模式挂在 GREY/YUYV（无压缩）而非仅 MJPG
3. `capture_smoke.py` 跑满 10 分钟 MONO8 120fps：掉帧率 < 0.1% 为 G0 通过
4. 样张目检：左右目各半幅、无错位；帧间隔 p95 纳入 EVT 任务 10（PTS 抖动）的旁证
5. 同一流程在泰山派3M（RK3576）上复跑一遍，完成 EVT 任务 12①

## 已知限制

- OpenCV 在 macOS/AVFoundation 下对 FOURCC 与帧率的设置可能被系统覆盖，
  以脚本打印的「协商结果」为准；精确模式控制以 Linux/V4L2 为准
- 掉帧为估算值（按间隔推算），UVC PTS 精确分析属 EVT 任务 10
