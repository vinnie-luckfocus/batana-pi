<p align="center">
  <img src="https://raw.githubusercontent.com/vinnie-luckfocus/batana/main/assets/logo.png" alt="batana" width="150">
</p>

# batana-pi — 双目边缘计算设备

batana-pi 是 batana 棒球打击动作捕捉/分析/评价生态系统中的**硬件设备仓库**：一款集**双目摄像头 + 边缘计算盒 + 显示屏**于一体的手持/桌面设备，独立完成"采集 → 推理 → 显示"的本地闭环，是 pro-stereo 与 max 档功能的硬件载体。

## 设备定位

- **双目摄像头**：双目全局快门相机模组，硬同步采集，为立体视觉管线提供原始帧
- **边缘计算盒**：本地运行推理管线与采集服务，无需依赖云端
- **显示屏**：5–7" 触控屏，运行嵌入式 GUI，现场即时查看分析结果
- **形态**：桌面支架形态优先，手持形态预留电池与结构空间

## 硬件选型方向

| 部件 | 方向 | 说明 |
| --- | --- | --- |
| 主控 | RK3588（首选）/ RPi5（起步验证） | RK3588 提供 NPU 加速，适配 RKNN 后端；RPi5 用于早期 EVT 快速验证 |
| 相机 | 双目全局快门模组 | 硬同步触发，避免卷帘快门在高速挥棒场景下的畸变 |
| 屏幕 | 5–7" 触控显示屏 | 嵌入式 GUI 输出，触控交互 |

## 与生态其他仓库的关系

- **batana-core**：提供 batana-runtime 推理运行时（RKNN/NPU 后端），本仓库负责将其打包部署到设备；分析算法本身不在本仓库实现
- **batana-cap**：定义 BLE 通信协议（ble-protocol），本仓库在设备侧实现 BLE 服务端，对接 cap 采集配件
- **batana-gui**：GUI 应用本体来自 batana-gui 的嵌入式构建（flutter-elinux），本仓库只做系统集成

接口适配细节见 [docs/contracts/device-interfaces.md](docs/contracts/device-interfaces.md)。

## 硬件阶段管理（EVT / DVT / PVT）

硬件开发按标准三阶段推进，工程文件分目录管理：

- **EVT（工程验证）**（`hardware/evt/`）：验证原理图与核心功能，快速迭代，里程碑 P3 产出 EVT 样机 + 软件栈 v0.1
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

## 许可证

见 [LICENSE](LICENSE)。
