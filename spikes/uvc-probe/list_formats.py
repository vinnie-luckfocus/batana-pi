#!/usr/bin/env python3
"""list_formats.py — 枚举 UVC 相机支持的分辨率 / 像素格式 / 帧率。

macOS 通过 ffmpeg avfoundation 探针解析（ffmpeg 不支持直接列出格式，
本脚本用「请求非法参数触发 ffmpeg 打印支持列表」的方式获取）：
  - 分辨率/帧率：ffmpeg -f avfoundation -framerate 999 -i "<dev>"
  - 像素格式：  ffmpeg -f avfoundation -pixel_format gray -framerate 30 -i "<dev>"
Linux 通过 v4l2-ctl --list-formats-ext 解析。

输出人类可读表格 + JSON，并标注目标模式（默认 2560x800@120）是否可达、
以及可达模式下是无压缩（MONO8/GREY/YUY2）还是仅 MJPEG。
"""

import argparse
import json
import platform
import re
import subprocess
import sys

# 无压缩像素格式关键字（用于「无压缩 vs 仅 MJPEG」判定）
UNCOMPRESSED_FORMATS = {
    "grey", "gray", "y800", "mono8", "y8",          # 单通道灰度
    "yuyv", "yuy2", "yuyv422", "uyvy", "uyvy422",   # YUV 4:2:2 无压缩
    "nv12", "nv21",                                  # YUV 4:2:0 无压缩
}
COMPRESSED_FORMATS = {"mjpg", "mjpeg", "jpeg", "h264", "h265", "hevc"}


def run(cmd, timeout=30):
    """运行命令并返回合并后的 stdout+stderr 文本。"""
    proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout
    )
    return (proc.stdout or "") + (proc.stderr or "")


# ---------------------------------------------------------------- macOS ----

def macos_list_devices():
    """解析 avfoundation 设备列表，返回 [(index, name), ...]（仅视频设备）。"""
    out = run(["ffmpeg", "-hide_banner", "-f", "avfoundation",
               "-list_devices", "true", "-i", ""])
    devices = []
    in_video = False
    for line in out.splitlines():
        if "AVFoundation video devices" in line:
            in_video = True
            continue
        if "AVFoundation audio devices" in line:
            in_video = False
            continue
        m = re.search(r"\[(\d+)\]\s+(.+)$", line)
        if in_video and m:
            name = m.group(2).strip()
            # 屏幕采集不是相机，跳过
            if name.lower().startswith("capture screen"):
                continue
            devices.append((int(m.group(1)), name))
    return devices


def macos_probe_modes(dev_index):
    """用非法帧率触发 ffmpeg 打印 Supported modes，解析分辨率与帧率范围。"""
    out = run(["ffmpeg", "-hide_banner", "-f", "avfoundation",
               "-framerate", "999", "-i", str(dev_index),
               "-t", "0.1", "-f", "null", "-"])
    modes = []
    for m in re.finditer(r"(\d+)x(\d+)@\[([\d.]+)\s+([\d.]+)\]fps", out):
        modes.append({
            "width": int(m.group(1)),
            "height": int(m.group(2)),
            "fps_min": float(m.group(3)),
            "fps_max": float(m.group(4)),
        })
    return modes


def macos_probe_pixel_formats(dev_index):
    """用相机不支持的 gray 触发 ffmpeg 打印 Supported pixel formats。"""
    out = run(["ffmpeg", "-hide_banner", "-f", "avfoundation",
               "-pixel_format", "gray", "-framerate", "30",
               "-i", str(dev_index), "-t", "0.1", "-f", "null", "-"])
    formats = []
    m = re.search(r"Supported pixel formats:", out)
    if m:
        # 后续每行形如 "[avfoundation @ 0x...]   uyvy422"，直到空行/其他内容
        for ln in out[m.end():].splitlines()[1:]:
            lm = re.search(r"\]\s+(\S+)\s*$", ln)
            if lm:
                formats.append(lm.group(1))
            elif ln.strip():
                break
    return formats


def collect_macos(device_filter=None):
    results = []
    for index, name in macos_list_devices():
        if device_filter is not None and str(index) != str(device_filter):
            continue
        results.append({
            "device": str(index),
            "name": name,
            "modes": macos_probe_modes(index),
            "pixel_formats": macos_probe_pixel_formats(index),
        })
    return results


# ---------------------------------------------------------------- Linux ----

def linux_list_devices():
    """解析 v4l2-ctl --list-devices，返回 [(path, name), ...]。"""
    out = run(["v4l2-ctl", "--list-devices"])
    devices = []
    cur_name = None
    for line in out.splitlines():
        if line and not line.startswith(("\t", " ")):
            cur_name = line.strip().rstrip(":")
        else:
            m = re.search(r"(/dev/video\d+)", line)
            if m and cur_name:
                devices.append((m.group(1), cur_name))
    return devices


def linux_probe(dev_path):
    """解析 v4l2-ctl -d <dev> --list-formats-ext。

    输出结构：
      [0]: 'YUYV' (YUYV 4:2:2)
          Size: Discrete 2560x800
              Interval: Discrete 0.008s (120.000 fps)
    """
    out = run(["v4l2-ctl", "-d", dev_path, "--list-formats-ext"])
    formats = []          # 像素格式 fourcc 列表
    modes = []            # {width, height, fps_list, pixel_format}
    cur_fmt = None
    cur_size = None
    for line in out.splitlines():
        m = re.search(r"\[\d+\]:\s+'(\w+)'", line)
        if m:
            cur_fmt = m.group(1)
            formats.append(cur_fmt)
            cur_size = None
            continue
        m = re.search(r"Size:\s+Discrete\s+(\d+)x(\d+)", line)
        if m:
            cur_size = (int(m.group(1)), int(m.group(2)))
            modes.append({"width": cur_size[0], "height": cur_size[1],
                          "fps_list": [], "pixel_format": cur_fmt})
            continue
        m = re.search(r"Interval:\s+Discrete\s+[\d.]+s\s+\(([\d.]+)\s*fps\)", line)
        if m and cur_size and modes:
            fps = float(m.group(1))
            if fps not in modes[-1]["fps_list"]:
                modes[-1]["fps_list"].append(fps)
    return formats, modes


def collect_linux(device_filter=None):
    results = []
    for path, name in linux_list_devices():
        if device_filter is not None and path != str(device_filter):
            continue
        formats, modes = linux_probe(path)
        results.append({"device": path, "name": name,
                        "modes": modes, "pixel_formats": formats})
    return results


# ---------------------------------------------------------------- 报告 ----

def classify_format(fmt):
    """像素格式分类：uncompressed / compressed / unknown。"""
    f = fmt.lower().strip("'\"")
    if f in UNCOMPRESSED_FORMATS:
        return "uncompressed"
    if f in COMPRESSED_FORMATS:
        return "compressed"
    return "unknown"


def annotate(results, target_w, target_h, target_fps):
    """为每台设备计算目标模式可达性与无压缩判定，返回注释字典。"""
    notes = []
    for dev in results:
        hit_modes = [
            m for m in dev["modes"]
            if m["width"] == target_w and m["height"] == target_h
            and m.get("fps_max", max(m.get("fps_list", [0])) or 0) >= target_fps
        ]
        fmts = dev["pixel_formats"]
        uncompressed = [f for f in fmts if classify_format(f) == "uncompressed"]
        compressed_only = fmts and not uncompressed

        # Linux 下帧率挂在「格式+分辨率」上，可精确判定；
        # macOS 只拿到全局像素格式列表，分辨率-格式对应关系无法从 avfoundation 获得
        exact = bool(dev["modes"]) and any("fps_list" in m for m in dev["modes"])
        if hit_modes:
            if exact:
                hit_fmts = sorted({m.get("pixel_format") or "?" for m in hit_modes})
                uncomp_hit = [f for f in hit_fmts if classify_format(f) == "uncompressed"]
                verdict = ("目标模式可达且含无压缩格式 " + "/".join(uncomp_hit)) \
                    if uncomp_hit else "目标模式仅 MJPEG/压缩格式可达 ⚠"
            else:
                verdict = ("目标模式可达（macOS 无法区分每分辨率的像素格式，"
                           "需在 capture_smoke 实测确认无压缩）")
        else:
            verdict = "未见目标模式 ⚠"
        notes.append({
            "device": dev["device"], "name": dev["name"],
            "target": f"{target_w}x{target_h}@{target_fps}",
            "target_reachable": bool(hit_modes),
            "uncompressed_formats": uncompressed,
            "compressed_only": bool(compressed_only),
            "verdict": verdict,
        })
    return notes


def print_table(results, notes, target_w, target_h, target_fps):
    for dev, note in zip(results, notes):
        print(f"\n=== 设备 {dev['device']}：{dev['name']} ===")
        if not dev["modes"]:
            print("  （未探测到任何模式）")
        else:
            header = f"  {'分辨率':<12}{'帧率':<22}{'像素格式':<10}备注"
            print(header)
            print("  " + "-" * (len(header) + 20))
            for m in sorted(dev["modes"], key=lambda x: (-x["width"], -x["height"])):
                if "fps_list" in m:  # Linux：精确帧率列表
                    fps_s = "/".join(f"{v:g}" for v in sorted(m["fps_list"]))
                    fmt = m.get("pixel_format") or "?"
                else:                  # macOS：帧率范围
                    fps_s = f"{m['fps_min']:g}–{m['fps_max']:g}"
                    fmt = "-"
                mark = ""
                if (m["width"] == target_w and m["height"] == target_h):
                    top = max(m.get("fps_list", [m.get("fps_max", 0)]) or [0])
                    mark = "★ 目标模式" if top >= target_fps else "（目标分辨率但帧率不足）"
                res_s = f"{m['width']}x{m['height']}"
                print(f"  {res_s:<13}{fps_s:<22}{fmt:<10}{mark}")
        if dev["pixel_formats"]:
            tags = "、".join(
                f"{f}({'无压缩' if classify_format(f) == 'uncompressed' else '压缩' if classify_format(f) == 'compressed' else '未知'})"
                for f in dev["pixel_formats"])
            print(f"  像素格式：{tags}")
        print(f"  判定：{note['verdict']}")


def main():
    ap = argparse.ArgumentParser(
        description="枚举 UVC 相机支持的分辨率/像素格式/帧率（macOS+Linux）")
    ap.add_argument("--device", default=None,
                    help="只探测指定设备（macOS 为序号如 0；Linux 为 /dev/video0）")
    ap.add_argument("--platform", default="auto", choices=["auto", "macos", "linux"])
    ap.add_argument("--width", type=int, default=2560, help="目标宽（默认 2560）")
    ap.add_argument("--height", type=int, default=800, help="目标高（默认 800）")
    ap.add_argument("--fps", type=float, default=120, help="目标帧率（默认 120）")
    ap.add_argument("--json", default=None, help="JSON 结果输出路径（缺省打印到 stdout）")
    args = ap.parse_args()

    plat = args.platform
    if plat == "auto":
        plat = "macos" if platform.system() == "Darwin" else "linux"

    if plat == "macos":
        results = collect_macos(args.device)
    else:
        results = collect_linux(args.device)

    if not results:
        print("未发现任何视频设备。", file=sys.stderr)
        sys.exit(2)

    notes = annotate(results, args.width, args.height, args.fps)
    print(f"目标模式：{args.width}x{args.height}@{args.fps:g}（无压缩 MONO8/YUY2 为通过）")
    print_table(results, notes, args.width, args.height, args.fps)

    payload = {"target": {"width": args.width, "height": args.height,
                          "fps": args.fps},
               "platform": plat, "devices": results, "verdicts": notes}
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"\nJSON 已写入 {args.json}")
    else:
        print("\n--- JSON ---")
        print(text)

    # 退出码：任一设备目标模式可达且无压缩 → 0，否则 → 1
    ok = any(n["target_reachable"] and not n["compressed_only"] for n in notes)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
