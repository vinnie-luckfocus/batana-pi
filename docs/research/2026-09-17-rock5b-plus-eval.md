# Radxa ROCK 5B+ 适配 batana-pi 需求调研报告

> - **日期**：2026-09-17
> - **作者**：评审调研
> - **状态**：已结论

调研日期 2026-09-17。**前提纠正：ROCK 5B+ 没有 12GB 内存版本**，官方 SKU 为 4/8/16/24/32GB LPDDR5（https://www.radxa.com/products/rock5/5bp/ 、https://docs.radxa.com/en/rock5/rock5b/getting-started/introduction）。以下以 16GB LPDDR5 版本为核对基准。

## 逐条核对表

| 需求 | 结论 | 证据 |
|---|---|---|
| SoC = RK3588（非 S 版） | ✅ | docs.radxa.com 参数表；设备树 compatible = "radxa,rock-5b-plus", "rockchip,rk3588"。双 ISP、6 TOPS NPU、完整 DCPHY/DPHY 保留 |
| 双目相机：2× 4-lane CSI 并发 | ✅ | 5B+ 有 2 个 4-lane MIPI CSI 连接器，支持 2×4-lane 或最多 4×2-lane（官方产品页与 MIPI CSI 文档）。OV9281 每路仅需 1.23Gbps，余量 8 倍 |
| OV9281 驱动现成可用 | ⚠️ | 官方相机列表只有 OV5647/IMX415/IMX219，无 OV9281；Radxa 论坛帖子证实需自行编译驱动+overlay。可参考 Arducam mainline ov9281.c 移植；黑白 RAW sensor 可走 VICAP 直取 RAW10 旁路 ISP/rkaiq |
| FSIN 硬同步触发输出 | ⚠️（可行需飞线） | CSI FPC 只引出电源使能 GPIO/RESET/MCLK/I2C，无 FSIN。40-pin 排针有多路硬件 PWM（PIN_32=PWM14_M0 等），120Hz FSIN 用硬件 PWM 无抖动，EVT 杜邦线接两模组 FSIN |
| MIPI DSI 接 5–7 寸触控屏 | ✅ | 板载 1× 4-lane MIPI DSI，官方支持 Radxa Display 8 HD（8 寸 800×1280 触控）与 Display 10 FHD；也可第三方 5/7 寸 DSI 屏 |
| DSI 与双 CSI 并发 PHY 冲突 | ✅ 无冲突 | 两路 CSI 走独立 CSI DPHY（csi_dphy0/dphy1）；DSI TX 走 DCPHY TX 侧，物理分离 |
| BLE Central 收 200Hz IMU | ✅ | 板载 RTL8852BE WiFi 6 + BT 5.2，蓝牙走 USB HCI，BlueZ Central 成熟；200Hz IMU 流 ~32kbps 无压力。注意必须接 IPEX 外置天线 |
| 内存 | ✅（无 12GB，买 16GB） | 64-bit LPDDR5，理论 44GB/s，实测 30+GB/s，对 <7GB/s 峰值需求余量 >4 倍 |
| 供电 | ✅ | USB-C PD（5V/3A、9V/3A、12V/3A）+ 40-pin 5V 供电 |
| 散热 | ⚠️ | idle ~2–4W，CPU 满载 ~8–11W，NPU 满载约 12–15W；dts sustainable-power=5W，被动散热 NPU 满载 30 分钟大概率降频，需官方 Heatsink 6240B 主动风扇或铝合金外壳。尺寸 100×75mm |
| 存储 | ✅ | 焊接 eMMC（32–256GB）+ 2× M.2 M Key（PCIe 3.0 x2，NVMe 2280）+ microSD；双路 ~310MB/s 裸流写盘够用 |
| 软件生态 | ✅/⚠️ | NPU/RKNN：Joshua-Riek ubuntu-rockchip 已支持 5B+（RKNPU 0.9.6 + librknnrt）；Yocto：Radxa 官方 Yocto 文档 + meta-rockchip（scarthgap）+ meta-qt6。相机：OV9281 需自行移植 |
| 价格与供货 | ✅ | 16GB 淘宝约 ¥1300–1600；供货充足 |

## 缺口与弥补方案

1. OV9281 不在官方支持列表（最大软件缺口）：移植 Arducam/树莓派 ov9281.c 到 BSP 6.1 内核 + 两个 CAM 口 DT overlay；走 VICAP 直出 RAW10 旁路 rkaiq（无 OV9281 tuning 文件）；预计 1–2 周内核/DT 工作量
2. FSIN 硬同步无板载走线：EVT 用 40-pin PWM 飞线；产品化做 CSI 转接板并入 FSIN
3. 散热：必须主动散热（6240B ~¥40–80）或铝合金外壳；被动撞 5W 功耗墙
4. 无 12GB SKU：直接 16GB（¥1300–1600）
5. 天线：RTL8852BE 只有 IPEX 座，必须外接胶棒天线，结构预留天线位

## 结论

ROCK 5B+（16GB LPDDR5）可作为 batana-pi 的 EVT 开发板，是目前 RK3588 系最贴合需求的现成板：真 RK3588 全接口、原生双 4-lane CSI 无 PHY 冲突地并发 DSI 触控屏、板载 BT 5.2 做 BLE Central、内存带宽 4 倍余量、eMMC+NVMe 齐备、RKNN/Yocto 生态成熟。硬性缺口只有 OV9281 驱动移植和 FSIN 飞线两项，EVT 阶段可接受。

离产品形态的差距清单：
- SBC 形态（100×75mm、IPEX 天线、USB-C PD）非产品形态——量产转 Radxa CM5（同 RK3588 SoM）+ 自制底板
- 定制双目相机 FPC/转接板（合并 FSIN、固定基线）
- 定制结构散热（封闭结构风扇噪声/寿命问题，建议结构导热到外壳）
- 产品镜像需自建 Yocto（meta-rockchip + meta-qt6 + 自定义 camera 层）；EVT 先用 Joshua-Riek Ubuntu 验证全链路
