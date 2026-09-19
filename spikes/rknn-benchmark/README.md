# spikes/rknn-benchmark — RKNN 基准工具

M0 G0 阶段门验证工具：BlazePose（full/lite）→ RKNN 转换与板端 NPU 基准，
判定标准：**INT8 单帧 p95 ≤ 20ms**（EVT 任务 12②；max 档 ≤8s 全链路的单帧预算）。

## 环境要求

### 模型转换（convert_model.py）—— **x86 Linux 主机**，不能在 macOS 上跑

> **风险 R3 已实测关闭（2026-09-19，macOS arm64 / Apple Silicon）**：
> `pip install rknn-toolkit2` 在 macOS arm64 上**无可用 wheel**，确切报错：
>
> ```
> hint: Wheels are available for `rknn-toolkit2` (v2.2.0) on the following
>       platforms: `manylinux_2_17_x86_64`, `manylinux2014_x86_64`
> hint: You require CPython 3.12 (`cp312`), but we only found wheels for
>       `rknn-toolkit2` (v2.2.1) with the following Python ABI tag: `cp38`
> ```
>
> 即：v2.2.0 仅 manylinux x86_64；v2.2.1 仅 cp38 且同样面向 Linux x86_64。
> **结论：转换必须在 x86 Linux 上进行。**

Fallback 方案（任选一）：

1. **x86 Linux 云主机/容器**（推荐，可复现）：
   `docker run --rm -it -v $PWD:/work python:3.10 bash`，
   容器内 `pip install rknn-toolkit2`（Python 3.8–3.12 均有 cp 轮）；
2. 任何 x86 Linux 物理机（Ubuntu 20.04/22.04，Python 3.10）；
3. 板端 RK3588 上也能跑 toolkit2 完整版（arm64 Linux wheel 存在），
   但首次转换建议留在主机端，板端只装 lite2 跑推理。

### 板端基准（bench_npu.py）—— ROCK 5B+ / 泰山派3M

Joshua-Riek Ubuntu 24.04（BSP 6.1 内核，自带 NPU 驱动），
Python 3.x + `pip install rknn-toolkit2-lite2`（arm64 wheel 官方提供）。
需主动散热（被动散热会撞 5W 功耗墙导致 NPU 满载降频，基准结果失真）。

## 操作步骤

```bash
# 0. 拉参考模型（任意有网络的机器）
./download_blazepose.sh models/

# 1. 转换（x86 Linux 主机/容器，Python 3.10）
pip install rknn-toolkit2
python convert_model.py --input models/pose_landmark_lite.tflite \
    --platform rk3588 --int8 --dataset dataset.txt \
    --input-size 256 --mean 0,0,0 --std 255,255,255
# dataset.txt：每行一张校准图路径（100–500 张击球场景相近分布图）

# 2. 拷板 + 基准（板端）
scp *_rk3588_int8.rknn rock@<board>:~/bench/
python3 bench_npu.py --model pose_landmark_lite_rk3588_int8.rknn \
    --input-size 256 --runs 200 --threshold 20
```

判定：输出 p50/p95/max，**p95 ≤ 20ms 通过**（退出码 0）。同流程在
泰山派3M（RK3576，加 `--platform rk3576` 转换）复跑，完成 EVT 任务 12②。

## 备注

- BlazePose landmark 输入为 256×256×3（lite/full/heavy 同尺寸，区别在内部
  算力；以模型实际输入为准，`netron` 打开 .tflite 可确认）；
  `--input-size` 两侧保持一致仅为核对
- INT8 量化失败/精度塌掉时先用 FP16（去掉 `--int8`）跑通基准，量化问题单列
- 转换期算子不兼容报错直接记入 EVT 任务 3（RKNN 算子覆盖率实测）
