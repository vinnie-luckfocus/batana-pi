# ROCK 5B+ 全局快门相机「免移植」调研报告

> - **日期**：2026-09-17
> - **作者**：评审调研
> - **状态**：已结论

调研日期 2026-09-17。问题：选用内核已支持的摄像头能否消除驱动移植风险？

**一句话结论：可以大幅降低但不能归零。** Rockchip 官方 BSP 6.1 内核自带 SC132GS 驱动（源码核实：https://raw.githubusercontent.com/rockchip-linux/kernel/develop-6.1/drivers/media/i2c/sc132gs.c），SC132GS 恰好是 mono 全局快门、1080×1280@60–120fps、模组现货充足——免移植首选。但 BSP 驱动有两个坑：只支持 30fps 模式、无 FSIN 触发控制，需小改。OV9281 保留为相机 Plan B。

## A. 候选传感器对比

| 传感器 | 分辨率/帧率 | Mono/Color | 主线内核驱动 | RK3588 BSP 6.1 | 模组现货 | FSIN/XVS |
|---|---|---|---|---|---|---|
| SC132GS | 1080×1280（竖幅原生），60–120fps | Mono | ❌ 无 | ✅ 有（BSP 6.1 树内 sc132gs.c；5.10 SDK 也有） | 丰富：VEYE RAW-MIPI-SC132M、Dogoozx、RDK X5 双目模组（Waveshare 在售） | 引脚支持，BSP 驱动未暴露 |
| SC235HGS | 2MP @130fps | 有 Mono | ❌ | ⚠️ 公开 6.1 仓库未确认（多见于 RV1106 SDK） | 较少 | 待查 |
| SC535HGS | 5MP（2448×2048）@80fps，BSI | Mono | ❌ | ⚠️ 同上不确定 | VEYE RAW-MIPI-SC535M | 待查 |
| IMX296（RPi GS Camera 同款） | 1456×1088，上限 60fps（不达标） | Mono/Color | ✅ imx296.c（6.3+，6.1 没有） | ❌ 无 | RPi GS Camera ~$50、InnoMaker 外触发版 €41 | XVS slave 成熟（RPi 生态验证） |
| AR0234 | 1920×1200 @120fps | Mono/Color | ⚠️ 2024 提交、2026-08 仍 v3 评审，未合入 | ❌ | 有（Arducam/Kurokesu，偏贵） | 支持 |
| OV7251 | 640×480，分辨率不达标，排除 | Mono | ✅ | — | 有 | — |
| OV9281/OV9282 | 1280×800 @120fps，完全达标 | OV9281=Mono | ✅ 主线 ov9282.c（2022 起兼容 OV9281） | ⚠️ BSP 有自研 ov9281.c（质量未验证），无 overlay | 极丰富（Arducam/Luxonis） | 支持（OAK 量产验证） |

## B. 「内核有驱动」后的剩余工作量（SC132GS on ROCK 5B+）

已消除：驱动编写、probe/出图、V4L2 链路调试——BSP 源码在树内，enable config 即可编译。

剩余：
1. 设备树 overlay（必做，1–2 天）：依赖 rockchip,camera-module-* 属性 + reset/pwdn GPIO + xvclk 24MHz + 三路电源，照 IMX415 overlay 仿写
2. 120fps 模式表（最大缺口，3–10 天+FAE 依赖）：BSP 驱动 supported_modes 的 max_fps 均为 30fps；120fps 需向 SmartSens/模组厂索取寄存器表（datasheet 在 NDA 下）；VEYE 模组在其平台只做到 1280×1080@45fps，说明 120fps 可能需 4-lane 或更高 lane rate，接线方式提前对齐
3. rkaiq tuning：mono 完全旁路，≈0 工作量——VICAP 直通 RAW 写 DDR，rkaiq 只对彩色 ISP 路径必需。「闭源 ISP 调谐」风险整体消除
4. 双目硬同步（驱动小改 + 连线，3–5 天）：BSP sc132gs.c 无 FSIN 控制；Rockchip VI 文档支持 internal master/external master/slave 三种同步模式，通用做法 sensor0 配 master、其余配 slave；给驱动加 slave 模式寄存器配置，FSIN 并接到主 sensor XVS 输出或定时 GPIO/PWM

与移植 OV9281 对比：

| 项目 | SC132GS（BSP 自带） | OV9281 |
|---|---|---|
| 驱动 | 在树，量产板验证 | BSP 自研质量未知；主线 ov9282.c 可替换 |
| Overlay | 需自写 | 需自写（工作量相同） |
| 120fps | 需补模式表（NDA 依赖） | 主线驱动自带 120fps 模式 |
| 同步触发 | 需小改驱动 | 同样需小改 |
| 生态参考 | Rockchip 官方在列、RDK X5 双目模组可参考 | RPi/OAK 生态最广、寄存器资料最开放 |

剩余风险评估：移植风险从「整个驱动从零移植（2–4 周，高不确定性）」降为「overlay + 120fps 模式表 + slave 同步寄存器（1–2 周，低不确定性）」。核心残余是 120fps 寄存器表获取（SmartSens NDA/FAE 响应速度）。

## C. 卷帘快门备选论证（量化否定）

120fps 下 IMX415 全帧读出仍需 ~8–16ms（2192 行 × 4–7µs/行）；棒尖 30–40m/s 时一帧读出期间位移 24–64cm，棒体横跨约 100 行即累积 30+ 像素剪切形变，且帧内曝光时刻逐行不等会破坏左右目同名点匹配。结论：卷帘快门对挥棒 3D 重建不可接受，全局快门维持硬需求。

## D. 最终推荐

1. 首选 SC132GS：BSP 6.1 驱动在树、mono 免 rkaiq、模组/双目模组供应链成熟。EVT 第一天并行：① 向 SmartSens FAE 或模组厂索取 120fps 寄存器表；② 确认 ROCK 5B+ 的 CSI 接线方案
2. OV9281 保留为相机 Plan B：拿不到 120fps 模式表立即切换——主线 ov9282.c 120fps 开箱即用，工作量相当，1280×800@120fps mono 零妥协
3. 不推荐 IMX296（60fps 不达标）和 AR0234（主线未合入）
