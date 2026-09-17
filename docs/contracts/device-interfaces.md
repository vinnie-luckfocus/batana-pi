# 设备接口契约（v1-draft）

> 状态：草案。本文档描述 batana-pi 设备侧与 batana 生态其他仓库之间的接口适配约定。

## 1. 采集服务 → batana-runtime：FrameSource 注入

设备的 `capture-service`（双目硬同步采集）以 **FrameSource** 形式向 batana-runtime（来自 batana-core）注入帧流：

- **角色**：capture-service 是生产者，runtime 是消费者；runtime 不直接访问相机驱动
- **帧单元**：一帧 = 左右目各一张图像 + 共享的硬件时间戳（硬同步触发，左右目时间戳一致）
- **注入方式**：进程间共享内存（零拷贝）传递图像缓冲，辅以事件通知；具体 ABI 随 runtime 的插件接口确定
- **参数**：分辨率、帧率、曝光等采集参数由 capture-service 管理，runtime 通过控制通道查询/请求调整
- **生命周期**：runtime 启动时请求 FrameSource，停止采集前需先解除引用，避免悬摆缓冲

## 2. 标定数据格式要点

双目标定数据由设备侧 `calibration` 服务产出，格式需登记进 session-schema（batana-core 侧）：

- **内容**：左右目内参（焦距、主点、畸变系数）+ 双目外参（旋转 R、平移 T）+ 图像分辨率
- **格式**：结构化 JSON（随 session 数据归档），字段命名与 session-schema 对齐
- **版本**：格式带版本号字段，设备出厂标定与现场重标定共用同一格式
- **存储**：设备本地持久化一份当前生效标定，runtime 启动时由 capture-service 一并提供

## 3. BLE 服务端角色

设备作为 **BLE 服务端（GATT Server）**，对接 batana-cap 采集配件：

- **协议引用**：BLE 通信协议（ble-protocol）由 **batana-cap 仓库定义**，本仓库仅按协议实现服务端角色，不在此处重复定义协议内容
- **职责**：广播与连接管理、按协议暴露服务/特征、透传 cap 侧传感器数据与状态
- **边界**：协议语义变更以 batana-cap 为准，设备侧实现跟随协议版本升级

## 4. 其他对外关系（简述）

- **消费**：batana-runtime（batana-core）、ble-protocol（batana-cap）、sync-api（云同步）
- **产出**：标定数据格式（登记进 session-schema）
