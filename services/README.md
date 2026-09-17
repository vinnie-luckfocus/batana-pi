# services — 设备服务

运行在设备上的系统服务（C++/Python）：

- `capture-service`：双目硬同步采集、ISP 调优，向 batana-runtime 注入帧源
- `calibration`：双目标定流程与标定参数管理
- `ota`：系统与应用的 OTA 升级
- `power`：功耗与散热管理

接口约定见 `docs/contracts/device-interfaces.md`。
