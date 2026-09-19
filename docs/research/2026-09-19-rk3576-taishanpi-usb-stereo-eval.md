# RK3576（立创泰山派3M）+ USB3 双目整模组 EVT 可行性调研报告

> - **日期**：2026-09-19
> - **作者**：评审调研
> - **状态**：已结论

调研日期 2026-09-19。目的：评估 RK3576 平台（重点：立创泰山派）+ USB3 双目成品摄像头作为 batana-pi EVT 低成本方案的可实现性，并与 RK3588（ROCK 5B+）横向对比。价格为查询当日网页快照价，下单前需复核。

## 1. 泰山派有 RK3576 版本：泰山派3M，在售

| 项目 | 泰山派3M（TaishanPi-3M-RK3576） | 来源 |
|---|---|---|
| 型号 | LCKFB-TSPI3M-RK3576-4G-64G（立创商城 C54110287） | [立创商城](https://item.szlcsc.com/57330947.html) |
| SoC / 内存 | RK3576（4×A72+4×A53 @2.2GHz，8nm），4GB **LPDDR5** + 64GB eMMC；SoC 支持 2–16GB | 同上 |
| 价格 | 立创商城 **¥899**；2026-03 首发 BOM 价 ¥699（限时）。淘宝第三方 ¥159/¥1498 标价含义不明，**以立创商城为准** | [OSHWHub 首发帖](https://oshwhub.com/li-chuang-kai-fa-ban/project_gzzvrwqn) |
| USB | **1× USB3.0 Type-A + 3× USB2.0** | [立创 wiki](https://wiki.lckfb.com/zh-hans/tspi-3-rk3576/system-development-compilation/opencv/usb-camera-verification.html) |
| 显示 | HDMI + DP（4K@120）；**MIPI-DSI 最高 2560×1600@60，带触摸接口**；三屏异显 | [立创商城](https://item.szlcsc.com/57330947.html) |
| 无线 | 板载双频 WiFi + **蓝牙 5.2** | 同上 |
| 系统 | 出厂 Android 14；官方 Ubuntu 24.04 / Debian 12 / Buildroot | [立创 wiki 系统指南](https://wiki.lckfb.com/zh-hans/tspi-3-rk3576/system-usage/) |
| 开放性 | 10 层 PCB 全开源；官方 wiki 含 UVC 摄像头 OpenCV 验证（Ubuntu24）、RKNN、Qt5.15 指南 | [立创 wiki](https://wiki.lckfb.com/zh-hans/tspi-3-rk3576/system-development-compilation/opencv/) |

注意：老款泰山派是 RK3566，与泰山派3M（RK3576）同时在售，采购时认准型号。

**其他在售 RK3576 板（备选）**：

| 板卡 | 价格 | 特点 | 来源 |
|---|---|---|---|
| Radxa ROCK 4D | 淘宝 ¥244–650（2–16GB LPDDR5x） | 1×USB3 Host + 1×USB3 OTG，HDMI 4K@120 + MIPI DSI，WiFi6+BT5.4，Radxa 生态 | [Liliputing](https://liliputing.com/two-new-single-board-pcs-with-rk3576-chips-radxa-rock-4d-and-friendlyelec-nanopi-m5/)、[Evelta](https://evelta.com/radxa-rock-4d-industrial-ai-sbc-for-edge-ai-and-4k-multimedia/) |
| Firefly ROC-RK3576-PC | $139 起（4G+32G） | 工业定位，文档全 | [Firefly Store](https://www.firefly.store/products/roc-rk3576-pc-octa-core-6t-aiot-mini-computer) |
| 飞凌 OK3576-C | ¥388 起（活动价） | 核心板+底板，工业级，供货 10–15 年 | [EE Times](https://www.eet-china.com/mp/a458627.html) |

## 2. RK3576 SoC 关键规格

| 项 | 规格 | 来源 |
|---|---|---|
| CPU/GPU | 4×A72 @2.2GHz + 4×A53；Mali-G52 MC3 | [立创商城](https://item.szlcsc.com/57330947.html) |
| NPU | 6 TOPS@INT8（双核），INT4/8/16、FP16/BF16；**rknn-toolkit2 v2.0.0 起官方支持 RK3576**，rknn_model_zoo 有独立性能列 | [rknn-toolkit2](https://github.com/airockchip/rknn-toolkit2)、[rknn_model_zoo](https://github.com/airockchip/rknn_model_zoo/blob/main/README_CN.md) |
| 内存 | LPDDR4x-4266 / LPDDR5-5500，**双通道总 32-bit**，理论带宽上限 ≈22GB/s——与 RK3588（64-bit，34–44GB/s）的最大硬件差距 | [TechApple](https://techapple.com/archives/61023) |
| USB | SoC 级 2× USB3.2 Gen1（5Gbps）：1 个常与 Type-C OTG 复用，1 个与 PCIe2.1/SATA 三合一复用；板厂不一定全引出 | 同上、[RK3576M datasheet](https://rockchip.fr/RK3576M%20datasheet%20V1.0.pdf) |
| MIPI | CSI-2（D-PHY 4×1/2×2 + C/D-PHY）；DSI-2；HDMI2.1/eDP1.3 combo | 同上 |
| 编解码 | 解码 8K@30 / 4K@120；编码 4K@60 H.265/H.264 | [米尔 MYC-LR3576](https://www.elecfans.com/p/v124620.html) |

## 3. USB3 UVC 双目在 RK3576 上的可行性

**结论：纸面可行，余量 1.6×；唯一未查实的关键项是高带宽无压缩 UVC 长时稳定性，列为 M0 第一冒烟测试。**

- 需求：2560×800×1B×120fps ≈ 1.97Gbps ≈ 246MB/s。RK3576 USB3（DWC3）实测顺序吞吐 **385–401MB/s**（[RK3576 USB 性能调优实战，2026-06](https://m.elecfans.com/article/7988774.html)）
- 同文给出直接相关的已知坑清单：
  - **协商掉速 480M**（线材/PHY 未初始化/DTS 缺 phys 引用）——先查 `/sys/bus/usb/devices/*-*/speed`
  - **SUSPHY 唤醒延迟**致等时传输卡顿——需 `snps,dis_u3_susphy_quirk`
  - **IMOD 中断合并**：UVC 等时传输需设 0 或 10，否则帧间隔抖动（文中 4K UVC 案例优化后丢帧率 3–5% → <0.1%）
  - IMOD=0 时中断风暴 48500 次/s 吃 CPU，120fps 高带宽流下需平衡
- 立创官方 wiki 已有泰山派3M + Ubuntu24 + UVC 摄像头验证文档（常规摄像头开箱可用），但未覆盖高带宽无压缩流
- 结构限制：泰山派3M 只引出 1 个 USB3，双目模组独占，其余外设走 USB2（EVT 可接受）；要 2 个独立 USB3 选 ROCK 4D 或米尔 MYD-LR3576

## 4. NPU 推理能力（BlazePose 级）

rknn_model_zoo 官方性能表（INT8、单核 NPU、纯推理，FPS，[来源](https://github.com/airockchip/rknn_model_zoo/blob/main/README_CN.md)）：

| 模型 | RK3588 单核 | RK3576 单核 |
|---|---|---|
| yolov8n (640×640) | 73.5 | **90.2** |
| **yolov8n-pose（姿态类直接参照）** | 55.9（≈17.9ms） | **66.8（≈15.0ms）** |
| resnet50 | 110.1 | 99.0 |

- BlazePose full/lite 输入仅 256×256（~2.7–6.9 GFLOPs），推算 RK3576 上 **5–15ms/帧**（推算值非实测），M0 标准 ≤20ms 大概率达成
- 与 RK3588 的真实差距：① 三核 NPU 并行上限（双目×2 模型并行时 RK3588 余量大）；② 内存带宽 22 vs 34–44GB/s（本案 USB 流 246MB/s 仅占 1%，推理主导消耗，风险低）
- 工具链同代（RKNPU2 + rknn-toolkit2），TFLite→RKNN 路径与 RK3588 一致，模型工件可直接复用

## 5. 显示与 BLE

- 显示：MIPI-DSI 带触摸（官方设计场景），走 USB 双目后 DSI 完全空闲，无冲突
- BLE：板载 BT5.2 做 Central 收 200Hz IMU（~32kbps）无压力（模块型号未查实，低风险项）

## 6. 软件生态

- 泰山派3M 官方：Ubuntu 24.04 / Debian 12 / Buildroot，开箱即用——**比押注 ubuntu-rockchip 更稳**（该项目维护者 2024-11 公开倦怠，[Jeff Geerling 报道](https://www.jeffgeerling.com/blog/2024/popular-rockchip-sbc-distro-limbo-after-maintainer-burns-out/)）
- 主线内核 6.12 起有 RK3576 初始支持（Collabora 主导，仍在推进）；**NPU/MPP/RGA 依赖 BSP 内核，量产前留在 BSP 线**
- Qt：官方 wiki 仅 Qt 5.15 指南；**Qt6 eglfs 在 RK3576 无官方文档（未查实）**——按 RK3588 经验（libmali GBM）大概率可行，或 Ubuntu 24.04 系统 Qt6 + wayland/xcb 兜底

## 7. 与 RK3588（ROCK 5B+ 16GB）横向对比

| 维度 | RK3576（泰山派3M / ROCK 4D） | RK3588（ROCK 5B+） | 对本案影响 |
|---|---|---|---|
| CPU | 4×A72+4×A53 @2.2GHz | 4×A76+4×A55 @2.4GHz | RK3588 单核强 1.5–2×；立体匹配/前后处理 CPU 余量差距明显 |
| NPU | 6 TOPS 双核，单核 ≥ RK3588 单核 | 6 TOPS 三核，并行上限高 | 单模型两者都够；双目双模型并行 RK3588 余量大 |
| 内存带宽 | 32-bit ≈22GB/s | 64-bit ≈34–44GB/s | 本案负载不构成瓶颈 |
| USB3 | SoC 2×5Gbps；泰山派只出 1 口 | 2×USB3 + Type-C 全功能 + PCIe 3.0 | 单模组都够；泰山派无冗余 |
| 显示 | HDMI/DP + MIPI-DSI 带触摸 | HDMI/DP + DSI | 打平 |
| BLE | 板载 BT5.2 | 板载 BT5.2（RTL8852BE，需 IPEX 天线） | 打平 |
| 生态 | 2025 起快速成熟，官方 Ubuntu24 | 非常成熟，社区案例最多 | RK3588 胜 |
| MIPI 双 CSI | 有（本案走 USB 不用） | 原生双 4-lane（VEYE 路线 B 依赖） | 路线 B 仍需要 RK3588 板 |
| 价格 | 泰山派3M ¥899 / ROCK 4D ¥244–650 | ¥1300–1600 | **省 ¥400–900/台** |

## 8. 明确结论

1. **RK3576 + USB3 双目纸面可行**，泰山派3M（¥899）是合格的低成本并行验证板：官方文档直接覆盖本案三个关键动作（UVC 接入、Ubuntu 24.04、RKNN 部署）
2. **不替代、做并行**：ROCK 5B+ 保留为主线 EVT 板（路线 B MIPI 双 CSI、max 档基准、生态成熟度）；增购 1 块泰山派3M 验证降本线
3. **泰山派3M 两个 M0 验收项**：① 2560×800@120 MONO8 抓帧 10 分钟掉帧率 <0.1%（含 IMOD/SUSPHY 调优）；② 姿态模型 RKNN INT8 单帧 ≤20ms。双达标 → standard/pro 档硬件路线切 RK3576，单板省 ~¥400–900
4. 能力档定位：RK3576 = standard/pro 档候选与量产 BOM 优化方向；**max 档基准板仍锁定 RK3588**（SoC 冻结决策不变）

## 9. 未查实项

- 2560×800@120fps 无压缩 UVC 在任意 RK3576 板上的公开实测案例：未查到（M0 实测）
- BlazePose 原模型在 RK3576 的实测耗时：未查到（仅有 yolov8n-pose 官方数据与推算）
- 泰山派3M 板载蓝牙模块型号及 BLE Central 实测：未查实（低风险）
- Qt6 eglfs 在 RK3576 的可行性：无官方文档（Qt5.15 官方指南兜底，或系统 Qt6 + wayland）
