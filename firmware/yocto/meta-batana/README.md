# meta-batana

batana 设备自定义 Yocto layer（骨架）。层结构与构建方案见上级
[../README.md](../README.md)。

## 结构

```
meta-batana/
├── conf/layer.conf                          # 层声明（scarthgap 兼容，优先级 10）
└── recipes-gui/batana-gui/batana-gui.bb     # batana-gui（Qt6/eglfs）配方桩，SRC_URI 占位
```

后续增量：camera 采集服务、calibration、ota、power 等配方（对应本仓
`services/` 各模块）随 EVT 推进逐个落入 `recipes-*/`。
