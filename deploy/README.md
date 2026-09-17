# deploy — 部署与系统集成

负责把生态组件打包集成进设备系统镜像：

- batana-runtime（来自 batana-core，RKNN/NPU 后端）的设备端打包
- 嵌入式 batana-gui（flutter-elinux 构建产物）的集成
- 系统服务（services/）的安装、自启动与守护配置
- Wi-Fi 云同步等运行环境配置
