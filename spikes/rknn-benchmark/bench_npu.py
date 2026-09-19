#!/usr/bin/env python3
"""bench_npu.py — RKNN 板端推理基准（rknn-toolkit2-lite2，ROCK 5B+ / 泰山派3M 上运行）。

加载 .rknn 模型，预热后跑 N 次推理，输出单帧耗时 p50/p95/max（ms），
并按 M0 验收标准（单帧 ≤ 20ms）给出判定。

示例：
  python3 bench_npu.py --model pose_landmark_lite_rk3588_int8.rknn \
      --input-size 256 --runs 200 --threshold 20
"""

import argparse
import sys
import time


def main():
    ap = argparse.ArgumentParser(description="RKNN 板端推理基准（p50/p95/max）")
    ap.add_argument("--model", required=True, help=".rknn 模型路径")
    ap.add_argument("--runs", type=int, default=200, help="计次推理次数，默认 200")
    ap.add_argument("--warmup", type=int, default=20, help="预热次数，默认 20")
    ap.add_argument("--input-size", type=int, default=256,
                    help="方形输入边长（BlazePose full/lite 为 256/192 等），默认 256")
    ap.add_argument("--threshold", type=float, default=20.0,
                    help="通过阈值（单帧 ms），默认 20")
    args = ap.parse_args()

    import numpy as np  # 延迟导入，--help 不依赖 numpy

    try:
        from rknnlite.api import RKNNLite
    except ImportError:
        print("错误：未安装 rknn-toolkit2-lite2。请在目标板（ROCK 5B+ /\n"
              "泰山派3M）上 pip install rknn-toolkit2-lite2。", file=sys.stderr)
        sys.exit(2)

    rknn = RKNNLite()
    print(f"加载模型：{args.model}")
    ret = rknn.load_rknn(args.model)
    if ret != 0:
        print("load_rknn 失败", file=sys.stderr)
        sys.exit(1)

    ret = rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_AUTO)
    if ret != 0:
        print("init_runtime 失败（检查 NPU 驱动/固件）", file=sys.stderr)
        sys.exit(1)

    # 构造随机输入（基准只测算力，不测精度）
    img = np.random.randint(0, 256, size=(1, args.input_size, args.input_size, 3),
                            dtype=np.uint8)

    print(f"预热 {args.warmup} 次…")
    for _ in range(args.warmup):
        rknn.inference(inputs=[img])

    print(f"计次 {args.runs} 次…")
    lat_ms = []
    for _ in range(args.runs):
        t0 = time.perf_counter()
        rknn.inference(inputs=[img])
        lat_ms.append((time.perf_counter() - t0) * 1000.0)

    rknn.release()

    arr = np.asarray(lat_ms)
    p50 = float(np.percentile(arr, 50))
    p95 = float(np.percentile(arr, 95))
    pmax = float(arr.max())
    passed = p95 <= args.threshold  # 以 p95 判定，避免偶发抖动误杀

    print("\n===== NPU 基准结果 =====")
    print(f"模型             ：{args.model}")
    print(f"单帧耗时(ms)     ：p50={p50:.2f}  p95={p95:.2f}  max={pmax:.2f}")
    print(f"通过标准         ：p95 ≤ {args.threshold:g}ms")
    print(f"判定             ：{'通过 ✅' if passed else '不通过 ❌'}")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
