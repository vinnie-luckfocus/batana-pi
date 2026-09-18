<p align="center">
  <img src="https://raw.githubusercontent.com/vinnie-luckfocus/batana/main/assets/logo.png" alt="batana" width="150">
</p>

# batana-pi — 双目边缘计算设备

batana-pi 是 batana 棒球打击动作捕捉/分析/评价生态系统中的**硬件设备仓库**：一款集**双目摄像头 + 边缘计算盒 + 显示屏**于一体的手持/桌面设备，独立完成"采集 → 推理 → 显示"的本地闭环，是 pro-stereo 与 max 档功能的硬件载体。

## 设备定位

- **双目摄像头**：双目全局快门相机模组，硬同步采集，为立体视觉管线提供原始帧
- **边缘计算盒**：本地运行推理管线与采集服务，无需依赖云端
- **显示屏**：5–7" 触控屏，运行嵌入式 GUI，现场即时查看分析结果
- **形态**：桌面支架形态优先，手持形态预留电池与结构空间（最终以 EVT 热实测数据冻结，见"散热与形态约束"）

## 硬件选型方向

| 部件 | 方向 | 说明 |
| --- | --- | --- |
| 主控 | RK3588（或 RK3576 降本版）——唯一目标 SoC | 选型矩阵结论（详见调研报告）：**RK3588 为 max/pro 档首选**；**RK3576（6 TOPS NPU 与 RK3588 同代，ISP 16M）为 OV9281 档降本版**；**RK3566（NPU 0.8 TOPS、ISP 8M@30 触顶）仅承担 standard 档或联调开发板，不承担 max 档 ≤8s**。RPi5 仅作为早期软件联调开发板：不出货、无 NPU、不承担任何性能指标 |
| 相机 | 双目全局快门模组：**EVT 双轨并行**——路线 A：OV9281 双目 USB3 无压缩整模组（零驱动）；路线 B：VEYE RAW-MIPI-SC132M × 2（SC132GS，MIPI 双模组） | 全局快门 + FSIN 外部触发硬同步（左右目同步误差 <1µs），避免卷帘快门在高速挥棒场景下的畸变。**EVT 并行采购两条路线实测对比后定案**：路线 A（USB 整模组，零驱动）——OV9281 双目 USB3 无压缩整模组、基线可调 60–120mm（Goobuy USB-OV9281-2 或淘宝同款，¥300–800 档，一次买 2–3 家样品），接 ROCK 5B+ 任一 USB3 口（Type-C 全功能口默认 host 可直插）；采购前三点书面确认：① 2560×800@120fps 无压缩 MONO8/YUY2 而非仅 MJPEG；② 真 USB3 5Gbps；③ 基线覆盖 80–120mm。避免 ELP USB3DGS800P（基线/USB 版本存疑）、微雪 52–62mm 固定基线款、OAK-D-Lite（分辨率不达标）；高端对照 OAK-D-S2（$329，基线 75mm 临界）。路线 B（MIPI 双模组，现方案转 plan B）——VEYE RAW-MIPI-SC132M × 2（31P→15P 排线直连双 CSI，J2 硬同步），画质上限更高（RAW10 无损）但有驱动/设备树工作量，EVT 预算 ≈¥1550–1650。**定案标准：挥棒场景 3D 重建精度实测（15mm@2.5m）**。详见 [docs/research/2026-09-17-usb-stereo-module.md](docs/research/2026-09-17-usb-stereo-module.md)、[docs/research/2026-09-17-stereo-camera-bom.md](docs/research/2026-09-17-stereo-camera-bom.md)、[docs/research/2026-09-17-camera-sensor-selection.md](docs/research/2026-09-17-camera-sensor-selection.md) |
| 屏幕 | 5–7" MIPI DSI 触控显示屏 | 调研确认：与双摄 CSI 为独立 PHY 无冲突（RK3588/3576/3566 均成立）；嵌入式 GUI 输出，触控交互 |

### 调研结论与待实测项

SoC/相机/显示屏接口调研已完成，完整测算与来源见 [docs/research/2026-09-17-soc-camera-display.md](docs/research/2026-09-17-soc-camera-display.md)。

**待实测项（三平台共性）**：

1. 120fps RAW 直通/VICAP 采集的官方支持确认
2. FSIN 硬同步帧配对精度（Rockchip V4L2 管线下）
3. RK3566 RKNN 对 BlazePose/MediaPipe 模型的算子覆盖率
4. BlazePose 各变体 GFLOPs 实测（M0 用 RKNN 模型分析工具）

### EVT 开发板选型

EVT 开发板确定为 **Radxa ROCK 5B+ 16GB LPDDR5**（无 12GB SKU）：真 RK3588（非 S 版）、原生双 4-lane CSI、MIPI DSI、板载 BT 5.2（RTL8852BE）可作 BLE Central、64-bit LPDDR5 内存带宽 4 倍余量。完整核对见 [docs/research/2026-09-17-rock5b-plus-eval.md](docs/research/2026-09-17-rock5b-plus-eval.md)。

**已知缺口（列入 EVT 任务）**：

1. 相机驱动（SC132GS）：BSP 6.1 树内自带 sc132gs.c（免移植），剩余工作为设备树 overlay（1–2 天）+ 120fps 寄存器表（SmartSens FAE/模组厂索取，EVT 第一天并行启动）+ FSIN slave 同步寄存器小改（3–5 天）；拿不到 120fps 模式表则切相机 Plan B OV9281（主线 ov9282.c 自带 120fps）
2. FSIN 硬同步：EVT 经 40-pin 硬件 PWM（如 PIN_32/PWM14_M0）杜邦线飞线接两模组 FSIN；产品化并入 CSI 转接板
3. 主动散热：官方 Heatsink 6240B 或铝合金外壳；被动散热会撞 5W sustainable-power 功耗墙导致 NPU 满载降频
4. 外接 IPEX 天线：RTL8852BE 仅 IPEX 座，结构需预留天线位
5. 排线 pinout 首件核对：Radxa 31P→15P 排线与 VEYE J1 逐脚核对（首件万用表核对后再上电）
6. 触发模式实际帧率实测：全局快门触发模式帧率 = 1/(曝光+读出)，短曝光估算 100–110fps，达不到流模式 120fps；备选主从同步模式（Strobe Out 级联）
7. 双 CSI 挂双 SC132M 的 dts 适配：两个 CSI 口各 2-lane、各自 I2C 地址
8. 路线 A 相机采购索证：书面确认 2560×800@120fps 无压缩 MONO8/YUY2、真 USB3 5Gbps、基线覆盖 80–120mm；一次买 2–3 家样品对比
9. UVC 长时 120fps 掉帧实测：RK3588 平台无公开案例，EVT 自测
10. UVC PTS 抖动实测：V4L2 SOF CLOCK_MONOTONIC 抖动分布与 UVC SCR/PTS 解析精度（对齐目标 ≤2ms）
11. 双轨定案实测：挥棒场景 3D 重建精度（15mm@2.5m）决定路线 A/B 取舍

**产品化路径**：EVT 先用 Joshua-Riek Ubuntu 验证全链路；量产转 Radxa CM5（同 RK3588 SoM）+ 自制底板，产品镜像自建 Yocto（meta-rockchip + meta-qt6 + 自定义 camera 层）。

**软件降级预案（plan B）**：**RPi5 8GB**。若 RK3588 侧 OV9281 驱动移植或 RKNN 模型转换受阻，切换 RPi5 8GB + 2× Arducam B0224 OV9281（直插双 CSI，FSIN 飞线）+ HDMI 触控屏 + Hailo-8L AI HAT+（13 TOPS）。已知接口妥协：双摄占用全部 MIPI 口后无 DSI 可用（屏走 HDMI）；Hailo-8L 抢唯一外露 PCIe（与 NVMe 互斥）；存储退守 microSD + RAM 环形缓冲。总价约 ¥2800–3500，高于 ROCK 5B+ 方案（~¥2300–2800），不可替代优势是软件风险最低（OV9281 主线驱动 + 120fps 官方确认 + Yocto/Qt6 生态成熟）。详见 [docs/research/2026-09-17-rpi5-eval.md](docs/research/2026-09-17-rpi5-eval.md)。

### 散热与形态约束

- **功耗**：RK3588 满载功耗约 6–10W，被动散热下手持形态（握持温度、续航）存疑
- **EVT 第一优先级实测**：满载 30 分钟温升曲线与降频（thermal throttling）曲线，用实测数据决定最终形态为手持还是桌面/三脚架
- **当前默认**：桌面支架形态优先，手持形态仅预留电池与结构空间，待 EVT 热实测后冻结

### 外观与外壳（ID/MD）

batana-pi 不只交付电路与固件，**外观设计与外壳制作在本仓正式立项**，随 EVT/DVT/PVT 阶段推进：

- **EVT（结构原型，无正式外壳）**：开发板 + 相机模组裸板验证，结构件只要求"能固定、能架设"——2020 铝型材 / 3D 打印相机条支架（保证基线刚性）+ 标准 1/4" 三脚架螺口 + 球场围栏挂钩，覆盖打击笼与球场现场架设场景
- **DVT（外观 ID + 外壳工程）**：外观工业设计（形态 / 材质 / 配色；桌面三脚架 vs 手持由 EVT 热实测冻结后定稿）；外壳结构与散热一体化设计（结构导热到外壳或风道、IPEX 天线外置位、DSI 屏装配与触控开窗、相机条基线刚性与标定保持、快拆 / 支架接口）；DFM 评估（3D 打印 → CNC 手板 → 模具决策）
- **PVT**：外壳模具 / 工艺与良率验证

结构硬约束（继承调研结论）：RK3588 满载 6–10W，外壳必须承担散热路径；RTL8852BE 仅 IPEX 座，天线必须外置；相机基线在运输 / 磕碰后须保持标定有效（刚性结构 + 软件侧标定失效检测）。

## 与生态其他仓库的关系

- **batana-core**：提供 batana-runtime 推理运行时（RKNN/NPU 后端），本仓库负责将其打包部署到设备；分析算法本身不在本仓库实现
- **batana-cap**：定义 BLE 通信协议（ble-protocol），cap 作为 GATT Server/Peripheral；本仓库在设备侧实现 BLE Central / GATT Client，连接 cap 并订阅 IMU Stream、读写控制命令特征
- **batana-gui**：GUI 应用本体来自 batana-gui 的 Qt6 嵌入式 Linux 构建（与 batana-gui 同源），本仓库只做系统集成

接口适配细节见 [docs/contracts/device-interfaces.md](docs/contracts/device-interfaces.md)。

## 硬件阶段管理（EVT / DVT / PVT）

硬件开发按标准三阶段推进，工程文件分目录管理：

- **EVT（工程验证）**（`hardware/evt/`）：验证原理图与核心功能，快速迭代，里程碑 P3 产出 EVT 样机 + 软件栈 v0.1；EVT 第一优先级完成满载 30 分钟热实测；**EVT 原型形态 = 开发板 + 相机模组 + 脚架/围栏挂钩支架（无正式外壳）**
- **DVT（设计验证）**（`hardware/dvt/`）：冻结设计、小批量试产验证，里程碑 P5 产出 DVT 小批量；**外观 ID 与外壳工程在 DVT 冻结**（散热一体化、DFM 评估，见"外观与外壳"）
- **PVT（生产验证）**（`hardware/pvt/`）：量产工艺与良率验证，面向正式投产

## 目录结构

```
batana-pi/
├── hardware/        # 原理图/PCB/结构·外壳（EVT→DVT→PVT 分目录；EVT=支架原型，DVT=外观ID+外壳）
├── firmware/        # U-Boot/内核/设备树/镜像构建
├── services/        # capture-service（双目同步）、calibration、ota、power
├── deploy/          # runtime 打包与系统集成
└── docs/contracts/  # 与 core/gui 的接口适配说明
```

## 变更记录

| 版本 | 日期 | 变更内容 | 同步 |
| --- | --- | --- | --- |
| 1.0-draft | 2026-09-18 | 新增「外观与外壳（ID/MD）」工作线：EVT 原型形态定为开发板 + 相机模组 + 脚架/围栏挂钩支架（无正式外壳，铝型材/3D 打印相机条保基线刚性 + 1/4" 三脚架螺口）；DVT 冻结外观 ID 与外壳工程（散热一体化、IPEX 天线位、DSI 屏装配、DFM：3D 打印→CNC→模具）；硬件阶段管理与目录结构同步更新 | 待同步司令塔 repos.yaml |
| 1.0-draft | 2026-09-17 | SoC 冻结为 RK3588（或 RK3576 降本版）为唯一目标，RPi5 仅作早期软件联调开发板（不出货、无 NPU、不承担性能指标）；BLE 角色纠正为 Central / GATT Client（cap 为 GATT Server/Peripheral）；UI 栈统一为 Qt6 嵌入式 Linux 构建（batana-gui 同源）；补充双目硬同步选型（OV9281/AR0234 全局快门 + FSIN 外部触发，<1µs 同步；EVT 可先用 USB3 全局快门模组）与散热/形态约束（RK3588 满载 6–10W，EVT 第一优先级实测满载 30 分钟温升/降频曲线） | 已同步司令塔 repos.yaml |
| 1.0-draft | 2026-09-17 | SoC/相机/显示调研完成：SoC 选型矩阵细化为 RK3588=max/pro 首选、RK3576=OV9281 档降本版、RK3566 仅 standard 档/联调开发板；确认 OV9281 双目 @120fps RAW10 带宽充足、AR0234 双目仅 RK3588 可行、MIPI DSI 5–7 寸触控屏与双摄 CSI 独立 PHY 无冲突；新增三平台共性待实测项（见 docs/research/2026-09-17-soc-camera-display.md） | 待同步司令塔 repos.yaml |
| 1.0-draft | 2026-09-17 | EVT 开发板确定为 Radxa ROCK 5B+ 16GB LPDDR5（无 12GB SKU；真 RK3588、原生双 4-lane CSI、MIPI DSI、板载 BT 5.2 作 BLE Central、64-bit LPDDR5）；已知缺口列入 EVT 任务（OV9281 驱动移植、FSIN 经 40-pin PWM 飞线→转接板、主动散热、外接 IPEX 天线）；产品化路径转 Radxa CM5 SoM + 自制底板（见 docs/research/2026-09-17-rock5b-plus-eval.md） | 待同步司令塔 repos.yaml |
| 1.0-draft | 2026-09-17 | 树莓派 5 适配调研完成：RPi5 8GB 定为软件降级预案（plan B），配置为 2× Arducam B0224 OV9281 直插双 CSI + FSIN 飞线 + HDMI 触控屏 + Hailo-8L AI HAT+（13 TOPS）；接口妥协为双摄后无 DSI、Hailo 抢唯一 PCIe、存储退守 microSD/RAM 缓冲；总价 ~¥2800–3500 高于 ROCK 5B+ 方案（见 docs/research/2026-09-17-rpi5-eval.md） | 待同步司令塔 repos.yaml |
| 1.0-draft | 2026-09-17 | 相机选型调研完成：双目相机首选改为 SC132GS（SmartSens mono 全局快门 1280×1080@120fps，BSP 6.1 树内自带驱动免移植），OV9281 降为相机 Plan B（主线 ov9282.c 自带 120fps）；残余工作量 overlay 1–2 天 + 120fps 寄存器表（SmartSens FAE，EVT 第一天并行索取）+ FSIN slave 同步小改 3–5 天；EVT 任务「OV9281 驱动移植」相应改为 SC132GS overlay/模式表/FSIN 同步（见 docs/research/2026-09-17-camera-sensor-selection.md） | 待同步司令塔 repos.yaml |
| 1.0-draft | 2026-09-17 | 双目相机落到具体采购决策：VEYE RAW-MIPI-SC132M × 2（15-pin RPi 兼容口，Radxa 31P→15P 排线直连 ROCK 5B+ 双 CSI，J2 引出 Trigger In/Strobe Out 硬同步）+ M12 f=2.8mm 镜头（备选 2.5mm）+ 80–120mm 可调基线支架；EVT 相机预算 ≈¥1550–1650；EVT 任务新增排线 pinout 首件核对、触发模式实际帧率实测、双 CSI 双模组 dts 适配（见 docs/research/2026-09-17-stereo-camera-bom.md） | 待同步司令塔 repos.yaml |
| 1.0-draft | 2026-09-17 | USB 双目整模组调研完成：相机选型改为 EVT 双轨并行——路线 A 为 OV9281 双目 USB3 无压缩整模组（零驱动，基线可调 60–120mm，¥300–800 档买 2–3 家样品，采购前书面确认无压缩 MONO8/YUY2、真 USB3、基线 80–120mm），路线 B 为 VEYE RAW-MIPI-SC132M ×2（转 plan B，RAW10 无损但有驱动/设备树工作量）；定案标准为挥棒场景 3D 重建精度实测（15mm@2.5m）；EVT 任务新增采购索证、UVC 长时 120fps 掉帧实测、UVC PTS 抖动实测与双轨定案实测（见 docs/research/2026-09-17-usb-stereo-module.md） | 待同步司令塔 repos.yaml |

## 许可证

见 [LICENSE](LICENSE)。
