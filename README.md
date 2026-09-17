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
| 相机 | 双目全局快门模组（OV9281 / AR0234 方向） | 全局快门 + FSIN 外部触发硬同步（左右目同步误差 <1µs），避免卷帘快门在高速挥棒场景下的畸变。调研确认：OV9281 双目 @120fps RAW10 带宽充足（2× 2-lane，利用率 25%）；AR0234 双目仅在 RK3588（双 ISP）可行。EVT 阶段可先用 USB3 全局快门模组打通采集链路 |
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

1. OV9281 驱动移植：BSP 6.1 内核 + 双 CAM 口 DT overlay，走 VICAP 直出 RAW10 旁路 rkaiq（预计 1–2 周）
2. FSIN 硬同步：EVT 经 40-pin 硬件 PWM（如 PIN_32/PWM14_M0）杜邦线飞线接两模组 FSIN；产品化并入 CSI 转接板
3. 主动散热：官方 Heatsink 6240B 或铝合金外壳；被动散热会撞 5W sustainable-power 功耗墙导致 NPU 满载降频
4. 外接 IPEX 天线：RTL8852BE 仅 IPEX 座，结构需预留天线位

**产品化路径**：EVT 先用 Joshua-Riek Ubuntu 验证全链路；量产转 Radxa CM5（同 RK3588 SoM）+ 自制底板，产品镜像自建 Yocto（meta-rockchip + meta-qt6 + 自定义 camera 层）。

### 散热与形态约束

- **功耗**：RK3588 满载功耗约 6–10W，被动散热下手持形态（握持温度、续航）存疑
- **EVT 第一优先级实测**：满载 30 分钟温升曲线与降频（thermal throttling）曲线，用实测数据决定最终形态为手持还是桌面/三脚架
- **当前默认**：桌面支架形态优先，手持形态仅预留电池与结构空间，待 EVT 热实测后冻结

## 与生态其他仓库的关系

- **batana-core**：提供 batana-runtime 推理运行时（RKNN/NPU 后端），本仓库负责将其打包部署到设备；分析算法本身不在本仓库实现
- **batana-cap**：定义 BLE 通信协议（ble-protocol），cap 作为 GATT Server/Peripheral；本仓库在设备侧实现 BLE Central / GATT Client，连接 cap 并订阅 IMU Stream、读写控制命令特征
- **batana-gui**：GUI 应用本体来自 batana-gui 的 Qt6 嵌入式 Linux 构建（与 batana-gui 同源），本仓库只做系统集成

接口适配细节见 [docs/contracts/device-interfaces.md](docs/contracts/device-interfaces.md)。

## 硬件阶段管理（EVT / DVT / PVT）

硬件开发按标准三阶段推进，工程文件分目录管理：

- **EVT（工程验证）**（`hardware/evt/`）：验证原理图与核心功能，快速迭代，里程碑 P3 产出 EVT 样机 + 软件栈 v0.1；EVT 第一优先级完成满载 30 分钟热实测
- **DVT（设计验证）**（`hardware/dvt/`）：冻结设计、小批量试产验证，里程碑 P5 产出 DVT 小批量
- **PVT（生产验证）**（`hardware/pvt/`）：量产工艺与良率验证，面向正式投产

## 目录结构

```
batana-pi/
├── hardware/        # 原理图/PCB/结构（EVT→DVT→PVT 分目录）
├── firmware/        # U-Boot/内核/设备树/镜像构建
├── services/        # capture-service（双目同步）、calibration、ota、power
├── deploy/          # runtime 打包与系统集成
└── docs/contracts/  # 与 core/gui 的接口适配说明
```

## 变更记录

| 版本 | 日期 | 变更内容 | 同步 |
| --- | --- | --- | --- |
| 1.0-draft | 2026-09-17 | SoC 冻结为 RK3588（或 RK3576 降本版）为唯一目标，RPi5 仅作早期软件联调开发板（不出货、无 NPU、不承担性能指标）；BLE 角色纠正为 Central / GATT Client（cap 为 GATT Server/Peripheral）；UI 栈统一为 Qt6 嵌入式 Linux 构建（batana-gui 同源）；补充双目硬同步选型（OV9281/AR0234 全局快门 + FSIN 外部触发，<1µs 同步；EVT 可先用 USB3 全局快门模组）与散热/形态约束（RK3588 满载 6–10W，EVT 第一优先级实测满载 30 分钟温升/降频曲线） | 已同步司令塔 repos.yaml |
| 1.0-draft | 2026-09-17 | SoC/相机/显示调研完成：SoC 选型矩阵细化为 RK3588=max/pro 首选、RK3576=OV9281 档降本版、RK3566 仅 standard 档/联调开发板；确认 OV9281 双目 @120fps RAW10 带宽充足、AR0234 双目仅 RK3588 可行、MIPI DSI 5–7 寸触控屏与双摄 CSI 独立 PHY 无冲突；新增三平台共性待实测项（见 docs/research/2026-09-17-soc-camera-display.md） | 待同步司令塔 repos.yaml |
| 1.0-draft | 2026-09-17 | EVT 开发板确定为 Radxa ROCK 5B+ 16GB LPDDR5（无 12GB SKU；真 RK3588、原生双 4-lane CSI、MIPI DSI、板载 BT 5.2 作 BLE Central、64-bit LPDDR5）；已知缺口列入 EVT 任务（OV9281 驱动移植、FSIN 经 40-pin PWM 飞线→转接板、主动散热、外接 IPEX 天线）；产品化路径转 Radxa CM5 SoM + 自制底板（见 docs/research/2026-09-17-rock5b-plus-eval.md） | 待同步司令塔 repos.yaml |

## 许可证

见 [LICENSE](LICENSE)。
