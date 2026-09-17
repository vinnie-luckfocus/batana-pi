# batana-pi「USB 双目整模组」方案可行性调研报告

> - **日期**：2026-09-17
> - **作者**：评审调研
> - **状态**：已结论

调研日期 2026-09-17。

## A. ROCK 5B+ USB 能力核实

接口配置（https://www.radxa.com/products/rock5/5bp/）：
- 2× USB 2.0 HOST（480Mbps）
- 2× USB 3.1 Gen1 Type-A（各 5Gbps）：上 = 纯 HOST，下 = OTG
- 1× 全功能 USB Type-C：USB 3.1 Gen1 OTG（5Gbps）+ DP 4Kp60；另有独立 USB-C PD 供电口

Type-C 能否 host 接 UVC 相机：可以。Radxa 官方论坛确认 Type-C 接完整 OTG0 + TYPEC0 控制器，默认 host 模式（https://forum.radxa.com/t/two-usb-ports-as-gadget-device-mode/24728）。

带宽：USB3 HOST 与 OTG 是独立控制器，任一口独享 5Gbps（https://www.collabora.com/news-and-blog/blog/2023/05/31/usb-30-preliminary-support-uboot-radxa-rock-5b/）。整模组把双目合并为单条 UVC 流（2560×800 side-by-side）只占一个口：无压缩 mono8 = 1.97Gbps，余量充足。若模组只给 YUY2（3.93Gbps）则贴顶——选型必须确认 MONO8/GREY 无压缩输出。

双 /dev/video 并发问题不存在：此类模组内部单颗 USB3 桥接，主机只见一个 video 节点，左右目同帧对半裁切（Goobuy FAQ https://www.okgoobuy.com/ov9281-global-shutter-camera.html）。

时间戳：左右目同步在模组内共享晶振/FSIN 完成（µs 级），同帧到达主机，双目间零偏移。host 侧 PTS：V4L2 在 SOF 打 CLOCK_MONOTONIC，典型抖动 <1ms，UVC SCR/PTS 解析后亚毫秒——≤2ms 对齐目标可达成（固定曝光帧率 + 单调时钟 + 标定相机-IMU 固定时延偏置）。RK3588 平台长时实测无公开案例，EVT 自测。

## B. 市售产品核实

| 产品 | 传感器 | 帧率 | 基线 | 接口/格式 | 价格 | 渠道 |
|---|---|---|---|---|---|---|
| Goobuy USB-OV9281-2（深圳模组商代表） | 2×OV9281 mono GS | 1280×800@120 | 60–120mm 可调 | USB3 无压缩 RAW/YUV，单流 2560×800，硬同步+频闪脚 | 同类淘宝 ¥300–800 | okgoobuy.com |
| 淘宝白牌 OV9281 双目 USB3 | 2×OV9281 mono GS | 标称 120fps | 多固定 60mm，部分可调 | USB3 UVC | ¥298 起 | 淘宝 |
| ELP-USB3DGS800P | 2×OV9281 mono GS | 1280×800@120 | 固定约 60mm（待确认） | 标称 MJPEG；USB 版本信息矛盾需厂家确认 | ~¥450–650 | elpcctv.com |
| 微雪 AR0144-Stereo | AR0144 1.2MP GS | ~60fps 级 | 52/62mm 固定 | USB2 MJPEG | ~¥200–300 | 微雪商城 |
| 迈德威视 MV-MSU 工业双目 | GS 可选 | 依型号 | FPC 自由调 | USB3 非 UVC，专用 SDK（ARM Linux） | ¥1000–2000 | 淘宝 |
| Luxonis OAK-D-S2 | 2×OV9282 mono GS + IMX378 | 1280×800@120 | 75mm 固定 | USB-C 3.1 Gen2，自带 Myriad X 深度 + BNO086 IMU | $329（到手 ~¥3000） | shop.luxonis.com |

排除：OAK-D-Lite（OV7251 640×480 不达标）、大恒/海康（无双目整模组，自组 ¥2000+/台过重）。

## C. 深度精度核算（基线 vs 15mm@2.5m）

δz = z²·δd/(b·f)，f≈1000px，z=2500mm：

| 基线 | δd=0.1px | δd=0.15px |
|---|---|---|
| 60mm | 10.4mm | 15.6mm ❌ |
| 75mm | 8.3mm | 12.5mm |
| 80mm | 7.8mm | 11.7mm |
| 120mm | 5.2mm | 7.8mm ✅ |

60mm 固定基线临界/不达标，必须 ≥80mm 或可调。

## D. Type-C 整模组 vs MIPI 双模组对比

| 维度 | USB3 双目整模组 | MIPI VEYE SC132M×2 |
|---|---|---|
| 同步精度 | 模组内共享晶振 µs 级，左右同帧 | FSIN 飞线硬同步 µs 级 |
| 帧率 | 1280×800@120 无压缩可达 | 1280×1080@120 无损 |
| 画质 | 无压缩 mono8 = RAW 等效；避开 MJPEG-only 型号 | RAW10 无损 |
| 驱动工作量 | 零（UVC 免驱） | 驱动适配+双 CSI 设备树 |
| 结构/线缆 | 一根 Type-C 线，相机条与主机分离、即插即用 | 2× FPC 排线，短且脆弱 |
| 基线 | 可调款 60–120mm ✅ | 支架自由调 ✅ |
| ISP 占用 | 不占 ISP | 占双 ISP |
| 价格 | ¥300–800（白牌）~¥3000（OAK-D-S2） | ≈¥1550–1650 |
| 风险 | 白牌规格需采购前索证；USB 长线 EMI | 驱动移植（有 plan B） |

## E. 明确推荐

可行，建议作为 EVT 并行首选：零驱动、相机条与主机解耦、单流规避并发问题、价格更低。推荐：
1. 首选：OV9281 双目 USB3 无压缩整模组、基线可调 60–120mm 款（Goobuy 或淘宝同款，一次买 2–3 家样品）；采购前书面确认：① 2560×800@120fps 无压缩 MONO8/YUY2；② 真 USB3 5Gbps；③ 基线覆盖 80–120mm
2. 高端对照/兜底：OAK-D-S2（$329，基线 75mm 略临界，不作量产选型）
3. 避免：ELP USB3DGS800P、微雪固定基线款、OAK-D-Lite、工业双目（迈德威视仅在白牌验证失败时考虑）
4. 接线：任一 USB3 口均可；Type-C 全功能口默认 host 可直插 C-to-C；供电走独立 PD 口互不干扰

MIPI 方案保留为 plan B，EVT 并行采购对比，最终由挥棒场景 3D 重建精度实测定案。

## F. 未查实项

- 白牌模组精确售价与长期供货能力（需询价）
- ELP USB3DGS800P 基线值与 USB 版本（信息矛盾）
- RK3588 平台 120fps 长时掉帧实测、UVC PTS 抖动分布（EVT 自测）
