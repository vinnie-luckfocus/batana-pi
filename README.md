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
| 主控 | RK3588（或 RK3576 降本版）——唯一目标 SoC | RK3588 提供 NPU 加速，适配 RKNN 后端；RK3576 为降本备选。RPi5 仅作为早期软件联调开发板：不出货、无 NPU、不承担任何性能指标 |
| 相机 | 双目全局快门模组（OV9281 / AR0234 方向） | 全局快门 + FSIN 外部触发硬同步（左右目同步误差 <1µs），避免卷帘快门在高速挥棒场景下的畸变；EVT 阶段可先用 USB3 全局快门模组打通采集链路 |
| 屏幕 | 5–7" 触控显示屏 | 嵌入式 GUI 输出，触控交互 |

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

## 许可证

见 [LICENSE](LICENSE)。
