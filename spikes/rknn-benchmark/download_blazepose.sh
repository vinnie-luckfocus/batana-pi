#!/usr/bin/env bash
# download_blazepose.sh — 拉取 BlazePose TFLite 参考模型（MediaPipe 官方）
# 用法：./download_blazepose.sh [输出目录，缺省 ./models]
set -euo pipefail

OUT_DIR="${1:-models}"
mkdir -p "$OUT_DIR"

BASE="https://storage.googleapis.com/mediapipe-assets"

# 姿态关键点（landmark）模型：full 精度优先 / lite 速度优先，M0 两个都测
MODELS=(
  "pose_landmark_full.tflite"
  "pose_landmark_lite.tflite"
  "pose_detection.tflite"   # 检测前置模型（可选，供完整管线参考）
)

for m in "${MODELS[@]}"; do
  dest="$OUT_DIR/$m"
  echo "下载 $m → $dest"
  curl -fSL --retry 3 --connect-timeout 15 -o "$dest" "$BASE/$m"
  # 简单校验：文件非空且为 TFLite（magic：偏移 4 处为 'TFL3'）
  if [[ $(stat -f%z "$dest" 2>/dev/null || stat -c%s "$dest") -lt 100000 ]]; then
    echo "错误：$dest 文件过小，疑似下载失败" >&2
    exit 1
  fi
  if [[ $(dd if="$dest" bs=1 skip=4 count=4 2>/dev/null) != "TFL3" ]]; then
    echo "错误：$dest 不是合法 TFLite 文件" >&2
    exit 1
  fi
done

echo "全部完成，模型位于 $OUT_DIR/"
