# 设备接口契约（Device Interfaces）

> - **版本**：1.0-draft
> - **归属（Owner）**：batana-pi（本仓库）
> - **消费方**：batana-core、batana-gui
> - **状态**：草案。本文档描述 batana-pi 设备侧与 batana 生态其他仓库之间的接口适配约定。

## 1. 采集服务 → batana-runtime：FrameSource 注入

设备的 `capture-service`（双目硬同步采集）以 **FrameSource** 形式向 batana-runtime（来自 batana-core）注入帧流：

- **角色**：capture-service 是生产者，runtime 是消费者；runtime 不直接访问相机驱动
- **帧单元**：一帧 = 左右目各一张图像 + 共享的硬件时间戳（硬同步触发，左右目时间戳一致）
- **注入方式**：进程间共享内存（零拷贝）传递图像缓冲，辅以事件通知；具体 ABI 随 runtime 的插件接口确定
- **参数**：分辨率、帧率、曝光等采集参数由 capture-service 管理，runtime 通过控制通道查询/请求调整
- **生命周期**：runtime 启动时请求 FrameSource，停止采集前需先解除引用，避免悬摆缓冲

## 2. 标定数据契约（calibration-data）

双目标定数据由设备侧 `calibration` 服务产出。**本仓库（batana-pi）是标定数据契约（calibration-data）的 owner**：格式定义与版本演进以本文件为准；batana-core 作为消费方，将该格式引用进 session-schema 的 `calibration` 字段，不在 core 侧重复定义格式。

- **内容**：左右目内参（焦距、主点、畸变系数）+ 双目外参（旋转 R、平移 T）+ 图像分辨率
- **格式**：结构化 JSON（随 session 数据归档），字段命名与 session-schema 对齐
- **版本**：格式带版本号字段，设备出厂标定与现场重标定共用同一格式
- **存储**：设备本地持久化一份当前生效标定，runtime 启动时由 capture-service 一并提供

## 3. BLE 角色：设备作为 Central / GATT Client

ble-protocol（由 **batana-cap 仓库定义**）规定：**batana-cap 是 GATT Server / Peripheral，本设备（batana-pi）是 BLE Central / GATT Client**：

- **角色**：设备作为 Central 主动扫描并连接 cap 配件；cap 作为 Peripheral 广播并暴露 GATT 服务/特征
- **数据通道**：设备订阅 cap 的 IMU Stream 特征（Notify），持续接收 IMU 数据流
- **控制通道**：设备通过读/写控制命令特征，向 cap 下发采集控制与配置命令
- **协议引用**：协议语义（服务/特征 UUID、帧格式、时序）以 batana-cap 的 ble-protocol 为准，本仓库仅按协议实现 Central 侧角色，不在此处重复定义协议内容
- **边界**：协议语义变更以 batana-cap 为准，设备侧实现跟随协议版本升级

## 4. 其他对外关系（简述）

- **消费**：batana-runtime（batana-core）、ble-protocol（batana-cap）、sync-api（云同步）
- **产出/持有**：标定数据契约（calibration-data，本仓库 owner，由 batana-core 引用进 session-schema 的 `calibration` 字段）
- **集成**：batana-gui 的 Qt6 嵌入式 Linux 构建产物由本仓库做系统集成

## 5. 变更记录

| 版本 | 日期 | 变更内容 | 同步 |
| --- | --- | --- | --- |
| 1.0-draft | 2026-09-17 | 初版定稿：补充治理头部（版本/归属/消费方/变更记录）；纠正 BLE 角色为 Central / GATT Client（cap 为 GATT Server/Peripheral，订阅 IMU Stream、读写控制命令特征）；明确本仓库为 calibration-data 契约 owner，core 消费并将格式引用进 session-schema 的 calibration 字段 | 已同步司令塔 repos.yaml |
