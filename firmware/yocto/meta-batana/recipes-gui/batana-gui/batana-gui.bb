# batana-gui 配方（桩）

# GUI 应用本体来自 batana-gui 仓的 Qt6 嵌入式 Linux 构建（与 batana-gui 同源，
# 本仓只做系统集成）。SRC_URI 为占位，待 batana-gui 仓确定 tag/commit 后填充。
SUMMARY = "batana 嵌入式 GUI（Qt6 / eglfs）"
LICENSE = "CLOSED"

# TODO: batana-gui 仓发布后替换为 git://...;protocol=https;branch=main
# SRC_URI = "git://github.com/vinnie-luckfocus/batana-gui.git;protocol=https;branch=main"
# SRCREV = "${AUTOREV}"
SRC_URI = ""

S = "${WORKDIR}/git"

DEPENDS = "qtbase qtdeclarative"

inherit qt6-cmake

# eglfs 无窗口系统：依赖 qtbase 的 eglfs 平台插件，由镜像层
# DISTRO_FEATURES 去 x11/wayland、qtbase PACKAGECONFIG 加 eglfs 保证
