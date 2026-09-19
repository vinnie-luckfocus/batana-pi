# firmware/yocto — 产品镜像 Yocto 构建

产品镜像构建方案（EVT 阶段先用 Joshua-Riek Ubuntu 验证全链路，量产前切 Yocto）：

- **Yocto 分支**：scarthgap（LTS）
- **BSP 层**：[meta-rockchip](https://git.yoctoproject.org/meta-rockchip)（scarthgap 分支）
- **Qt6 层**：[meta-qt6](https://code.qt.io/cgit/yocto/meta-qt6.git/)（6.x 对应 scarthgap 的分支）
- **自定义层**：`meta-batana/`（本目录，batana-gui 配方 + 后续 camera/服务配方）
- **目标机**：Radxa ROCK 5B+（RK3588；meta-rockchip 机器名 `rock-5b`，
  5B+ 与 5B 的差异以设备树 overlay/dtb 实测修正）；降本线备选泰山派3M（RK3576）
- **GUI 显示**：Qt6 eglfs（无 X11/Wayland，DISTRO_FEATURES 移除 x11 wayland，
  qtbase PACKAGECONFIG 启用 eglfs + gbm/kms）

## 构建环境（macOS 注意）

Yocto 构建**只能在 Linux 上进行**。macOS 开发机需二选一：

1. **Linux 容器**（推荐）：Docker Desktop / OrbStack 跑 `crops/poky:ubuntu-22.04`
   或 ubuntu:22.04 自配依赖；构建目录挂卷（yocto 构建 I/O 重，卷挂载用
   delegated/cached 一致性或直接用容器内卷，避免 VirtioFS 瓶颈）
2. **Linux VM / 云主机**：x86_64 Ubuntu 22.04，≥8 核 16GB 内存 200GB 磁盘

参考构建步骤（Linux 内）：

```bash
git clone -b scarthgap https://git.yoctoproject.org/poky
git clone -b scarthgap https://git.yoctoproject.org/meta-rockchip
git clone -b 6.8 https://code.qt.io/cgit/yocto/meta-qt6.git
source poky/oe-init-build-env build-rock5b
# bblayers.conf 追加 meta-rockchip、meta-qt6、本仓 firmware/yocto/meta-batana
# local.conf: MACHINE = "rock-5b"，DISTRO_FEATURES 去 x11 wayland
bitbake core-image-minimal   # 冒烟；后续切 batana-image
```

## 当前状态

骨架阶段：`meta-batana` layer 骨架 + batana-gui 配方桩（SRC_URI 占位）。
尚未实际 bitbake 验证；首次构建属 DVT 前任务，EVT 全程用 Ubuntu。
