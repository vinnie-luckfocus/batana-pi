#!/usr/bin/env python3
"""capture_smoke.py — UVC 相机抓帧冒烟测试（macOS + Linux 通用）。

按指定模式（分辨率/像素格式/帧率）抓帧 N 分钟，统计：
  - 实际帧率（总帧数 / 实际时长）
  - 掉帧率（帧间隔 > 1.5× 标称间隔 → 估算掉帧数 = round(间隔/标称) - 1）
  - 帧间隔抖动 p50 / p95 / max
  - MONO8 模式（--format GREY）下把合并帧左右切开，定时保存抽帧样张

输出逐帧 CSV + 终端摘要。通过标准：掉帧率 < 0.1%。

依赖：opencv-python（或 opencv-python-headless）、numpy。
"""

import argparse
import csv
import os
import platform
import sys
import time

import numpy as np


def open_capture(device, width, height, fps, fourcc_str):
    """按平台选择后端打开相机并设置采集模式，返回 cv2.VideoCapture。"""
    import cv2

    if platform.system() == "Darwin":
        backend = cv2.CAP_AVFOUNDATION
        dev = int(device)
    else:
        backend = cv2.CAP_V4L2
        # Linux 下允许传 /dev/videoN 或纯序号
        dev = device if str(device).startswith("/dev/") else int(device)

    cap = cv2.VideoCapture(dev, backend)
    if not cap.isOpened():
        print(f"错误：无法打开设备 {device}", file=sys.stderr)
        sys.exit(2)

    if fourcc_str:
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fourcc_str))
    if width:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    if height:
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    if fps:
        cap.set(cv2.CAP_PROP_FPS, fps)

    # 读回协商结果（部分平台/驱动不支持回读，尽力而为）
    got_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    got_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    got_fps = cap.get(cv2.CAP_PROP_FPS)
    got_fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
    fourcc_s = "".join(chr((got_fourcc >> 8 * i) & 0xFF) for i in range(4))
    print(f"协商结果：{got_w}x{got_h} @ {got_fps:.2f}fps，FOURCC={fourcc_s!r}")
    return cap, got_w, got_h, got_fps


def percentile(sorted_vals, q):
    """有序数组取分位数（线性插值），空数组返回 0。"""
    if not sorted_vals:
        return 0.0
    return float(np.percentile(np.asarray(sorted_vals), q))


def main():
    ap = argparse.ArgumentParser(description="UVC 相机抓帧冒烟测试（掉帧/抖动统计）")
    ap.add_argument("--device", default="0",
                    help="设备：macOS 为序号（默认 0），Linux 为 /dev/video0 或序号")
    ap.add_argument("--width", type=int, default=2560)
    ap.add_argument("--height", type=int, default=800)
    ap.add_argument("--fps", type=float, default=120)
    ap.add_argument("--format", default="GREY",
                    help="像素格式 FOURCC：GREY（MONO8）/ YUY2 / MJPG，默认 GREY")
    ap.add_argument("--duration", type=float, default=10.0,
                    help="抓帧时长（分钟），默认 10")
    ap.add_argument("--out-dir", default="capture_out", help="输出目录")
    ap.add_argument("--sample-interval", type=float, default=60.0,
                    help="MONO8 双目样张保存间隔（秒），0 关闭，默认 60")
    args = ap.parse_args()

    import cv2  # 延迟导入，--help 不依赖 cv2

    os.makedirs(args.out_dir, exist_ok=True)
    csv_path = os.path.join(args.out_dir, "frames.csv")
    sample_dir = os.path.join(args.out_dir, "samples")
    os.makedirs(sample_dir, exist_ok=True)

    cap, got_w, got_h, got_fps = open_capture(
        args.device, args.width, args.height, args.fps, args.format)

    nominal_fps = got_fps if got_fps and got_fps > 1 else args.fps
    nominal_interval = 1.0 / nominal_fps
    drop_threshold = 1.5 * nominal_interval

    duration_s = args.duration * 60.0
    is_mono = args.format.upper() in ("GREY", "Y800", "MONO8")

    print(f"开始抓帧：标称 {nominal_fps:.2f}fps，时长 {args.duration:g} 分钟，"
          f"掉帧阈值 {drop_threshold*1000:.2f}ms")

    intervals = []        # 帧间隔（秒）
    est_dropped = 0       # 估算掉帧数
    n_frames = 0
    n_read_fail = 0
    next_sample_at = 0.0  # 下一张样张的相对时间

    t_start = time.perf_counter()
    t_prev = None
    deadline = t_start + duration_s

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["frame_index", "timestamp_s", "interval_ms",
                         "read_ok", "est_dropped_at_gap"])

        while time.perf_counter() < deadline:
            ok = cap.grab()
            t_now = time.perf_counter()
            if not ok:
                n_read_fail += 1
                writer.writerow([n_frames, f"{t_now - t_start:.6f}", "", 0, 0])
                continue
            ret, frame = cap.retrieve()
            if not ret or frame is None:
                n_read_fail += 1
                writer.writerow([n_frames, f"{t_now - t_start:.6f}", "", 0, 0])
                continue

            interval = t_now - t_prev if t_prev is not None else 0.0
            gap_dropped = 0
            if t_prev is not None and interval > drop_threshold:
                gap_dropped = max(1, round(interval / nominal_interval) - 1)
                est_dropped += gap_dropped
            if t_prev is not None:
                intervals.append(interval)
            t_prev = t_now
            n_frames += 1

            writer.writerow([n_frames, f"{t_now - t_start:.6f}",
                             f"{interval * 1000:.3f}", 1, gap_dropped])

            # MONO8 双目：按时抽帧，左右目切开保存
            rel = t_now - t_start
            if (is_mono and args.sample_interval > 0
                    and rel >= next_sample_at and frame.ndim == 2
                    and frame.shape[1] % 2 == 0):
                half = frame.shape[1] // 2
                stem = f"sample_{n_frames:06d}"
                cv2.imwrite(os.path.join(sample_dir, f"{stem}_left.png"),
                            frame[:, :half])
                cv2.imwrite(os.path.join(sample_dir, f"{stem}_right.png"),
                            frame[:, half:])
                next_sample_at = rel + args.sample_interval

    cap.release()
    t_end = time.perf_counter()
    elapsed = t_end - t_start

    # ---------------------------------------------------------------- 统计
    actual_fps = n_frames / elapsed if elapsed > 0 else 0.0
    total_expected = n_frames + est_dropped
    drop_rate = est_dropped / total_expected if total_expected else 0.0
    iv_ms = sorted(v * 1000.0 for v in intervals)
    p50 = percentile(iv_ms, 50)
    p95 = percentile(iv_ms, 95)
    pmax = iv_ms[-1] if iv_ms else 0.0

    verdict = "通过 ✅" if drop_rate < 0.001 else "不通过 ❌"

    print("\n===== 冒烟测试摘要 =====")
    print(f"设备/模式        ：{args.device}  {got_w}x{got_h}@{nominal_fps:.2f}  "
          f"{args.format}")
    print(f"实际时长         ：{elapsed:.2f} s")
    print(f"收到帧数         ：{n_frames}（读取失败 {n_read_fail} 次）")
    print(f"实际帧率         ：{actual_fps:.2f} fps（标称 {nominal_fps:.2f}）")
    print(f"估算掉帧         ：{est_dropped} 帧，掉帧率 {drop_rate * 100:.4f}%"
          f"（阈值 <0.1%）")
    print(f"帧间隔抖动(ms)   ：p50={p50:.3f}  p95={p95:.3f}  max={pmax:.3f}")
    print(f"逐帧 CSV         ：{csv_path}")
    if is_mono:
        print(f"双目样张目录     ：{sample_dir}")
    print(f"判定             ：{verdict}")

    sys.exit(0 if drop_rate < 0.001 else 1)


if __name__ == "__main__":
    main()
