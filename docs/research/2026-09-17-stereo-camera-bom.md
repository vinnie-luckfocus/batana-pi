# batana-pi 双目相机选型调研报告（EVT 采购决策版）

> - **日期**：2026-09-17
> - **作者**：评审调研
> - **状态**：已结论

调研日期 2026-09-17。

## 1. 接口匹配结论

ROCK 5B+ 板载 CSI 连接器：**31-pin、0.3mm 间距 FPC（Hirose FH35C-31S-0.3SHW），2 个口各 4-lane**（来源：Radxa ROCK 5C 硬件接口文档 https://docs.radxa.com/en/rock5/rock5c/hardware-design/hardware-interface 、Radxa 论坛确认 https://forum.radxa.com/t/connect-arducam-hq-camera-to-rock5b/12325）。与树莓派 15-pin 不直接兼容，需转接排线。

现货转接排线：

| 排线 | 用途 | 来源 |
|---|---|---|
| 31P 0.3mm → 15P 1.0mm（同面） | 接 2-lane 15-pin 树莓派接口模组（VEYE、Arducam B0224） | Radxa Camera 8M 219 标配线 https://docs.radxa.com/en/accessories/camera/camera-8m-219 |
| Radxa AC020：31P 0.3mm → 22P 0.5mm | 接 22-pin 4-lane 模组 | https://www.radxa.com/products/accessories/fpc-adapter-cable-ac020/ |

利好：VEYE 官方 GitHub 提供 RK3566/RK3588 + Radxa 板卡驱动与示例（https://github.com/veyeimaging），与 ROCK 5B+ 软件栈直接对口。

## 2. 模组对比

| 模组 | lane/接口 | 满幅帧率 | 黑白 | 触发脚 | 镜头座 | 价格 | 渠道 |
|---|---|---|---|---|---|---|---|
| VEYE RAW-MIPI-SC132M | 2-lane，15-pin 1.0mm（RPi pinout 兼容），1.188Gbps/lane | 1280×1080@120fps（流模式） | 是 | J2：Trigger In + Strobe Out（3.3V） | 无，另配 M12/CS 座 | ~¥600 | veye.cc、淘宝 VEYE 企业店、AliExpress；手册 https://wiki.veye.cc/index.php/RAW-MIPI-SC132M_Data_Sheet/zh |
| VEYE CS-MIPI-SC132(V2) | 2-lane 15-pin | 满幅仅 45fps（ISP 瓶颈） | 是 | J7 Trigger In | 板载 M12/CS | ~¥200–300 | 同上 |
| Dogoozx AS-DGSG8A231M1-60 | MIPI（pinout 未公开） | 标称 120fps | 是 | 未见引出 | 镜头可选 | ~¥210 | dgzx.hk |
| GS130W 双目整模组（RDK X5） | 每目 2-lane，双 22-pin RDK 线序 | 120fps | 否（彩色） | 支持外部触发 | 固定 1.75mm 鱼眼 157°D 不可换，基线固定 80mm | ~¥373–400 | 微雪/spotpear |

GS130W 排除：彩色、鱼眼大畸变不适合 15mm 级 3D 重建、基线不可调、22-pin RDK 专用线序接 ROCK 5B+ 风险高。Dogoozx：无公开 pinout/触发文档，作备胎。

## 3. 明确推荐

**VEYE RAW-MIPI-SC132M × 2**（15-pin RPi 兼容口 + 31P→15P 排线直连 ROCK 5B+ 两个 CSI 口；2-lane 带宽 2×1.188Gbps > 满幅 120fps 所需 ~1.66Gbps；两模组 Trigger In 并联到 40-pin GPIO 做硬同步）。

### 镜头焦距（SC132GS 靶面 1280×2.7µm=3.456mm × 1080×2.7µm=2.916mm，对角 4.52mm）

- 2.5m 距离覆盖 2m 宽 → 水平 FoV ≥ 43.6°；含挥棒余量 → 焦距 2.3–2.8mm
- 推荐 M12 低畸变 f=2.8mm：H 63°/V 55°/D 78°，2.5m 覆盖约 3.1m×2.6m；SC132GS 原生竖幅，模组旋转 90° 安装，竖向用长边覆盖全身+球棒
- 备选 f=2.5mm（H 69°/D 84°）对比；不推荐 1.75mm 鱼眼

### 基线（ΔZ = Z²·Δd/(f_px·B)，f=2.8mm → f_px=1037，亚像素 Δd=0.15px）

| 基线 | Z=2.5m | Z=3.0m |
|---|---|---|
| 60mm | 15.1mm | 21.7mm ✗ |
| 80mm | 11.3mm ✓ | 16.3mm（临界） |
| 120mm | 7.5mm ✓ | 10.8mm ✓ |

推荐：两独立模组 + 2020 铝型材可调支架，基线 80–120mm 可调（EVT 按实测拍摄距离标定；固定则取 100mm）

> 澄清（2026-09-19）：**基线方向为水平（左右并排）**，双目的视差在水平方向；"模组旋转 90°" 仅指传感器竖幅安装（1280px 长边覆盖竖向包络），不改变基线方向。相机条安装时严格调平，否则引入垂直视差损失。路线 A 整模组同理：条身水平，左右镜头中心距即基线。

## 4. EVT 采购清单

| 项 | 数量 | 单价 | 小计 |
|---|---|---|---|
| VEYE RAW-MIPI-SC132M | 2 | ~¥600 | ¥1200 |
| VEYE S-MOUNT01 M12 镜头座 | 2 | ~¥30 | ¥60 |
| M12 低畸变镜头 2.8mm（+2.5mm 各 1 对比） | 2+2 | ~¥25–50 | ~¥150 |
| Radxa 31P→15P 排线（150mm） | 2（+2 备） | ~¥20 | ¥80 |
| 杜邦线/触发并连线 | 1 批 | ~¥10 | ¥10 |
| 2020 铝型材 + 角码滑块 | 1 套 | ~¥60 | ¥60 |
| 合计 | | | ≈¥1550–1650 |

备胎：Dogoozx ×1（~¥210）低成本对照。

## 5. Plan B 对照（简要）

- Arducam B0224（OV9281，15-pin，~$26）：同一 31P→15P 排线可接，主线驱动；但单板未引出 FSIN，需换带触发引出的型号；1MP 2-lane 满幅通常 60fps 级，120fps 需降分辨率，整体弱于 SC132GS 方案
- Luxonis OAK-D-S2（¥4190）：自带深度算力但与本架构重复，EVT 不值得，仅作整机兜底

## 6. 需 EVT 实测确认项

1. 触发模式实际帧率：VEYE 手册注明全局快门触发模式帧率 = 1/(曝光+读出)，达不到流模式 120fps；短曝光估算 100–110fps，需实测；备选主从同步模式（Strobe Out 级联）
2. ROCK 5B+ 双 CSI 口同时挂两颗 SC132M 的 dts 适配（2-lane、各自 I2C 地址）
3. 31P→15P 排线与 VEYE J1 逐脚核对（首件万用表核对后再上电）
4. 镜头畸变与覆盖范围：2.8mm/2.5mm 各买一颗对比定版
