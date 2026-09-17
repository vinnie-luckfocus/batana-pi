# batana-pi SoC 与相机/显示接口调研报告

> - **日期**：2026-09-17
> - **作者**：评审调研
> - **状态**：已结论

调研日期 2026-09-17。所有规格优先采用官方 datasheet/brief datasheet，其次为厂商 wiki 与社区实测。

## A. RK3588 相机子系统

### A.1 MIPI CSI-2 配置

来源：官方 datasheet V1.6（https://wiki.friendlyelec.com/wiki/images/e/ee/Rockchip_RK3588_Datasheet_V1.6-20231016.pdf ，镜像 https://www.hua-chips.com/news/3588_datasheet.html）

- 2× MIPI DCPHY combo：每个可用作 DPHY v2.0 4-lane @ 4.5Gbps/lane（合计 18Gbps），或 CPHY v1.1 3-trio @ 2.5Gsps
- 4× MIPI CSI DPHY v1.2：每个 2-lane @ 2.5Gbps/lane，支持两个合并为一个 4-lane
- 相机组合（官方明确列出）：2 DCPHY + 4× 2-lane DPHY = 最多 6 路相机；2 DCPHY + 1× 4-lane + 2× 2-lane = 5 路；2 DCPHY + 2× 4-lane = 4 路
- VICAP 支持 6 路 MIPI CSI/DSI 接口、每接口 4 个虚拟通道，RAW8/10/12/14

结论：双摄拆 2× 2-lane 是官方原生支持的配置，且完全不必动用 DCPHY。

### A.2 ISP 能力

| 模式 | 输入规格 | 折算像素吞吐 |
|---|---|---|
| 单 ISP | 16M：4672×3504@30 | ≈ 491 MPix/s |
| 双 ISP | 32M：6528×4898@30 | ≈ 959 MPix/s |
| 双 ISP | 48M：8064×6048@15 | ≈ 731 MPix/s |

即 ISP0/ISP1 各约 480–490 MPix/s，支持多 sensor 复用 ISP。第三方核心板规格书一致（https://www.tronlong.com/productinfo57.html 、https://xhwyzsd.com/products/rk3588/）。

### A.3 带宽测算验证

| 方案 | 单路码率 | 双路码率 | 双路像素流 | 结论 |
|---|---|---|---|---|
| OV9281 1280×800 RAW10 @120 | 1.23 Gbps | 2.46 Gbps | 245.8 MPix/s | ✅ 极轻松 |
| AR0234 1920×1200 RAW10 @120 | 2.77 Gbps | 5.53 Gbps | 553 MPix/s | ✅ 满足，需双 ISP |

- OV9281 双目：每路挂一个 2-lane DPHY（5 Gbps 物理容量 vs 1.23 Gbps 需求，利用率 25%）；像素流 245.8 MPix/s 远低于单 ISP 的 491 MPix/s，单 ISP 都够。
- AR0234 双目：每路 2.77 Gbps 仍可挂 2-lane DPHY（利用率 55%），也可走 DCPHY 4-lane（18 Gbps）；像素流 553 MPix/s 超单 ISP，需各占 ISP0/ISP1（各 276.5 < 491 MPix/s），余量 ~40%。
- 注意：ISP 官方只标到 30fps 高分辨率模式，120fps 小分辨率 RAW 直通（mono 无需 debayer，可走 VICAP RAW 采集绕开 ISP 大部分管线）未查到官方明确支持矩阵，需 M0 实测。

### A.4 显示并发与内存带宽

- 显示 PHY 与 CSI PHY 完全独立：2× MIPI DSI TX（4-lane @ 4.5Gbps，最高 4K@60）、2× HDMI 2.1/eDP combo、2× DP1.4a。双摄 CSI 与 DSI 触屏无接口冲突。
- 内存：4 通道 × 16bit LPDDR4/4x/5（64-bit）。LPDDR5-6400 → 51.2 GB/s，LPDDR4x-4266 → 34.1 GB/s。
- 并发负载粗算：双目写入 0.3–0.7 GB/s + ISP 读写放大 ×2–3（~2 GB/s）+ 1080p60 UI ~0.5 GB/s + NPU 推理 2–4 GB/s ≈ 总计 < 7 GB/s，占 LPDDR5 带宽 ~13%。三负载并发带宽充足。

### A.5 现货方案

- 开发板：Radxa ROCK 5B 有 1 个 4-lane CSI（可拆 2× 2-lane），ROCK 5B+ 有 2 个 4-lane CSI（https://docs.radxa.com/rock5/rock5b/getting-started/interface-usage/mipi-csi）；Orange Pi 5/5 Plus、Firefly ROC/AIO-3588 均有双 CSI。
- OV9281 驱动：Rockchip BSP 内核已含 CONFIG_VIDEO_OV9281（https://blog.csdn.net/wb4916/article/details/156025761）；Orange Pi 5 社区移植指南（https://github.com/Joshua-Riek/ubuntu-rockchip/issues/577）；mainline 参考 Arducam ov9281.c（https://github.com/ArduCAM/ov9281_driver/blob/main/ov9281.c）。
- 双目硬同步模组：现成 MIPI 双目 OV9281（FSIN 同步）主要面向树莓派/Jetson（https://www.arducam.com/arducam-1mp2-stereoscopic-camera-bundle-kit-for-raspberry-pi-nvidia-jetson-nano-xavier-nx-two-ov9281-global-shutter-monochrome-camera-modules-and-camarray-stereo-camera-hat.html），RK3588 侧无双目整模组现货，需自研转接板 + 设备树（FSIN 外部触发线拉到两模组即可，电气上无平台依赖）。

## B. RK3566 降级可行性

### B.1 关键规格

| 项目 | 规格 | 来源 |
|---|---|---|
| CPU | 4× Cortex-A55 @ ≤1.8GHz（22nm） | https://www.cnx-software.com/2021/05/17/roc-rk3566-pc-single-board-computer-supports-up-to-8gb-ram-nvme-ssd/ |
| NPU | 0.8 TOPS（INT8，RKNN 1.0/2.0 代） | 同上 |
| ISP | 8M ISP（ISP21 代），行业惯例 8M@30 ≈ 245 MPix/s | https://www.rock-chips.com/uploads/pdf/2022.8.26/192/RK3566%20Brief%20Datasheet.pdf |
| MIPI CSI-2 | 单个物理 DPHY，full 模式 4-lane @ 2.5Gbps/lane；split 模式拆 2× 2-lane 可同时双摄 | https://github.com/Firefly-docs/products-docs/blob/master/en/Motherboard/ROC-RK3568-PC%20SE/driver_camera.md 、https://www.yxzhi.cn/post/252409.html |
| 显示 | HDMI 2.0（4K@60）、eDP、MIPI DSI 单屏 1920×1080@60、LVDS | RK3566 Datasheet V1.1 |
| 内存 | LPDDR4 32-bit @ 3200MT/s → 12.8 GB/s，最大 8GB | Radxa ROCK 3C |

### B.2 带宽测算

- MIPI：split 模式每路 2-lane × 2.5Gbps = 5 Gbps vs 需求 1.23 Gbps → ✅ 利用率 25%。
- ISP 像素流：双目 @120fps = 245.8 MPix/s，ISP 标称上限 ≈ 245 MPix/s——恰好触顶，且 120fps sensor 模式未见官方支持。缓解：OV9281 单色 RAW 无需 ISP 管线，可 RKCIF/VICAP 直通 RAW 到内存（未查到官方文档确认，需实测）。
- 降档：2× OV9281@60 = 123 MPix/s（ISP 上限 50%）✅；720p@60 双目 = 110 MPix/s ✅。
- 内存：双目写入 307 MB/s + 显示 + NPU ≈ 2–3 GB/s vs 12.8 GB/s ✅。

### B.3 NPU 推理估算（≤8s 预算）

模型计算量参考：BlazePose lite 2.7 GFLOPs / full 6.9 GFLOPs（二手整理 https://www.emergentmind.com/topics/blazepose-pipeline；官方论文只给延迟 https://ar5iv.labs.arxiv.org/html/2206.11678）。RK3566 0.8 TOPS INT8，RKNN 实测效率按 30–40%（同平台 YOLOv5s 6.5 GFLOPs ~25ms/帧 https://www.e-eway.com/news/info-1000030-330085.html）估算：

| 模型 | 单帧估算 | 120 张（60 对）总耗时 | ≤8s？ |
|---|---|---|---|
| BlazePose-lite (2.7G) | ~10–13 ms | 1.2–1.6 s | ✅ 宽裕 |
| BlazePose-full (6.9G) | ~25–33 ms | 3–4 s | ✅ 可行 |
| BlazePose-heavy (~25G) | ~90–120 ms | 10.8–14.4 s | ❌ 超预算 |
| MoveNet-lightning 级 | ~5–8 ms | <1 s | ✅ |

风险：RK3566 属老一代 NPU，RKNN 转换可能有算子不支持 fallback CPU，转换可行性需 M0 验证。

### B.4 显示并发

DSI/HDMI TX 与 CSI RX 独立 PHY，无冲突；5–7 寸 DSI 触屏在能力内 ✅。Mali-G52 跑 Qt6 2D/骨骼叠加够用，3D 回放吃力。

### B.5 结论

RK3566 双目 @120fps 处于 ISP 名义极限 + 120fps 未验证的灰区，NPU 只能跑 lite/full 级模型。定位：最多 standard 档 + 联调开发板；pro-stereo 需降帧 60fps 且实测确认；max 档（≤8s 全量）不可承担。

## C. 中间选项 RK3576

| 项目 | 规格 | 来源 |
|---|---|---|
| CPU | 4× A72 @2.2GHz + 4× A53 @2.0GHz，8nm | https://www.rock-chips.com/uploads/pdf/2024.3.18/192/RK3576%20Brief%20Datasheet%20V1.2-20240311.pdf |
| NPU | 6 TOPS INT8（与 RK3588 同代 RKNN） | 同上 |
| ISP | 16M（≈480 MPix/s 级） | https://www.niucores.com/forum-post/44774.html |
| CSI | 4× 2-lane DPHY @2.4Gbps（可合 2× 4-lane）+ 1× DPHY v2.0 4-lane @4.5Gbps | https://www.topeetboard.com/sydymfl/Product/iTOP-3576kernel.html |
| 内存 | 32-bit LPDDR4/4x/5，最高 16GB | https://www.eet-china.com/mp/a372006.html |
| 显示 | HDMI 2.1/eDP（4K@120）、MIPI DSI（2560×1600@60）、DP | 同上 |
| 价格 | 核心板 ~¥359–500 起 vs RK3588 ¥800–1500 | https://www.myir.cn/shows/40/213.html |

评估：双目 OV9281@120 充裕；双目 AR0234@120（553 MPix/s）超 16M ISP 标称，需 RAW 直通绕 ISP（未验证）。NPU 与 RK3588 同算力，max 档推理侧等价。作为 RK3588 降本版成立，前提是相机只用 OV9281 档。

## 汇总测算表

| 需求 | 数值 | RK3588 | RK3576 | RK3566 |
|---|---|---|---|---|
| 双 OV9281@120 CSI 码率 | 2.46 Gbps | ✅ 2×2-lane (25%) | ✅ 2×2-lane (26%) | ✅ 2×2-lane split (25%) |
| 双 AR0234@120 CSI 码率 | 5.53 Gbps | ✅ | ✅ 2-lane 可行但 ISP 不行 | ⚠️ CSI 可行 ISP 不行 |
| 双 OV9281@120 像素流 | 245.8 MPix/s | ✅ 单 ISP 50% | ✅ ~50% | ⚠️ 恰触 ISP 顶 |
| 双 AR0234@120 像素流 | 553 MPix/s | ✅ 双 ISP | ❌ 超 16M ISP | ❌ |
| NPU 推理 120 帧 ≤8s | BlazePose-full 级 | ✅ | ✅ | ⚠️ lite/full ✅、heavy ❌ |
| 双摄+DSI 屏并发 | PHY 独立 | ✅ | ✅ | ✅ |
| 内存带宽余量 | 峰值 <7 GB/s | ✅ 51.2 GB/s | ✅ ~25 GB/s | ✅ 12.8 GB/s（紧张但够） |

## 最终选型矩阵

| SoC | max 档 ≤8s | 双摄+显示并发 | 主要风险 | 建议 |
|---|---|---|---|---|
| RK3588 | ✅ | ✅ 原生 6 摄 + 独立 DSI | 双目模组需自研转接/设备树；120fps RAW 直通需实测 | max/pro 档首选 |
| RK3576 | ✅（NPU 同算力） | ✅ | ISP 仅 16M，AR0234 双目超限；生态较薄 | 成本敏感时的 OV9281 档降本版 |
| RK3566 | ❌ heavy 超 8s | ✅ 硬件无冲突 | ISP 触顶 + 120fps 未验证；老 NPU 转换风险 | 仅 standard 档 / 联调开发板 |

## 待实测项（三平台共性）

1. 120fps RAW 直通/VICAP 采集的官方支持确认
2. FSIN 硬同步在 Rockchip V4L2 管线下的帧配对精度
3. RK3566 RKNN 对 BlazePose/MediaPipe 模型的算子覆盖率
4. BlazePose 各变体 GFLOPs 实测（建议 M0 用 RKNN 模型分析工具）
