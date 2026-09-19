#!/usr/bin/env python3
"""convert_model.py — TFLite → RKNN 模型转换（rknn-toolkit2，x86 Linux 主机端）。

用于 M0 G0：把 BlazePose 等 TFLite 模型转为 RK3588/RK3576 可用的 .rknn，
支持 INT8 量化（需提供校准数据集列表文件）。

环境要求见 README（**macOS arm64 无 rknn-toolkit2 wheel，须在 x86 Linux
或云主机上运行**，风险 R3 已实测确认）。

示例：
  python convert_model.py --input pose_landmark_lite.tflite \
      --platform rk3588 --int8 --dataset dataset.txt \
      --output pose_landmark_lite_rk3588_int8.rknn
"""

import argparse
import sys


def main():
    ap = argparse.ArgumentParser(description="TFLite → RKNN 转换（rknn-toolkit2）")
    ap.add_argument("--input", required=True, help="输入 .tflite 模型路径")
    ap.add_argument("--output", default=None,
                    help="输出 .rknn 路径（缺省在输入名后加平台/量化后缀）")
    ap.add_argument("--platform", default="rk3588",
                    choices=["rk3588", "rk3576"], help="目标平台，默认 rk3588")
    ap.add_argument("--int8", action="store_true",
                    help="启用 INT8 量化（需 --dataset）")
    ap.add_argument("--dataset", default=None,
                    help="INT8 校准数据集列表文件（每行一张图片路径）")
    ap.add_argument("--input-size", type=int, default=None,
                    help="输入边长（方形，如 256）。TFLite 自带输入形状，"
                         "此参数仅记录进日志用于核对（与 bench_npu 的 "
                         "--input-size 保持一致）")
    ap.add_argument("--mean", default="0,0,0",
                    help="量化均值，逗号分隔，默认 0,0,0")
    ap.add_argument("--std", default="255,255,255",
                    help="量化方差，逗号分隔，默认 255,255,255（即 [0,255]→[0,1]）")
    args = ap.parse_args()

    if args.int8 and not args.dataset:
        ap.error("--int8 需要同时提供 --dataset 校准数据集列表文件")

    mean_values = [float(v) for v in args.mean.split(",")]
    std_values = [float(v) for v in args.std.split(",")]

    if args.output is None:
        stem = args.input.rsplit(".tflite", 1)[0]
        suffix = "int8" if args.int8 else "fp16"
        args.output = f"{stem}_{args.platform}_{suffix}.rknn"

    try:
        from rknn.api import RKNN
    except ImportError:
        print("错误：未安装 rknn-toolkit2。本脚本只能在 x86 Linux 上运行\n"
              "（macOS arm64 无官方 wheel，见 README「环境要求」）。", file=sys.stderr)
        sys.exit(2)

    rknn = RKNN(verbose=True)

    print(f"[1/3] 配置：target={args.platform} int8={args.int8} "
          f"mean={mean_values} std={std_values}"
          + (f" input_size={args.input_size}（仅记录核对）"
             if args.input_size else ""))
    ret = rknn.config(mean_values=[mean_values], std_values=[std_values],
                      target_platform=args.platform)
    if ret != 0:
        print("rknn.config 失败", file=sys.stderr)
        sys.exit(1)

    print(f"[2/3] 加载 TFLite：{args.input}")
    ret = rknn.load_tflite(model=args.input)
    if ret != 0:
        print("load_tflite 失败（算子不兼容时见此报错，"
              "记入 EVT 任务 3 算子覆盖率）", file=sys.stderr)
        sys.exit(1)

    print(f"[3/3] 构建 RKNN（do_quantization={args.int8}）→ {args.output}")
    ret = rknn.build(do_quantization=args.int8,
                     dataset=args.dataset if args.int8 else None)
    if ret != 0:
        print("build 失败", file=sys.stderr)
        sys.exit(1)

    ret = rknn.export_rknn(args.output)
    if ret != 0:
        print("export_rknn 失败", file=sys.stderr)
        sys.exit(1)

    rknn.release()
    print(f"完成：{args.output}")


if __name__ == "__main__":
    main()
