#!/usr/bin/env python3
"""Measure or fix a clip's loudness. Target -13.8 LUFS integrated, -1.0 dBTP, the level a short has to sit at
next to everyone else's. Two-pass loudnorm: measure, then normalise with the measured values and linear=true,
video stream copied so nothing is re-encoded but the audio.

    python3 loudness.py clip.mp4              prints I, TP, LRA and PASS or FAIL
    python3 loudness.py --fix in.mp4 out.mp4  writes out.mp4 in spec, then measures it
"""
from __future__ import annotations
import json, math, re, subprocess, sys

TARGET_I, TARGET_TP, TARGET_LRA = -13.8, -1.0, 9.0
TOL_I, TOL_TP = 0.6, 0.5


def measure(path: str) -> dict:
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af",
           f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json", "-f", "null", "-"]
    out = subprocess.run(cmd, text=True, capture_output=True).stderr
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", out, re.S)
    if not m:
        sys.exit("ffmpeg gave no loudnorm block. Is there an audio track? " + out[-400:])
    d = json.loads(m.group(0))
    return {k: float(d[k]) for k in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")}


def is_silent(mm: dict) -> bool:
    """Silence measures as -inf, and loudnorm refuses measured_I=-inf. Catch it before it is passed back in."""
    return not math.isfinite(mm["input_i"]) or mm["input_i"] <= -70.0


def in_spec(mm: dict) -> bool:
    if is_silent(mm):
        return False
    return abs(mm["input_i"] - TARGET_I) <= TOL_I and mm["input_tp"] <= TARGET_TP + TOL_TP


def _run(inp: str, out: str, af: str) -> None:
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", inp, "-af", af,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out], check=True)


def fix(inp: str, out: str) -> dict:
    """Pass one: linear gain from the measured values, which keeps the dynamics. A peaky quiet track cannot be
    lifted that way without breaking the true-peak ceiling, so if the result is still off, pass two runs
    loudnorm in its dynamic mode, which limits peaks as it lifts. The measurement of the file written is what
    is returned, never the intent."""
    mm = measure(inp)
    if is_silent(mm):
        # nothing to lift. copy it through rather than lose a clip that has already been paid for.
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", inp,
                        "-c", "copy", out], check=True)
        res = dict(mm)
        res["silent"] = True
        return res
    af = (f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:measured_I={mm['input_i']}:"
          f"measured_TP={mm['input_tp']}:measured_LRA={mm['input_lra']}:measured_thresh={mm['input_thresh']}:"
          f"offset={mm['target_offset']}:linear=true")
    _run(inp, out, af)
    res = measure(out)
    if in_spec(res):
        return res
    _run(inp, out, f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:linear=false")
    res = measure(out)
    res["mode"] = "dynamic"
    return res


def report(mm: dict) -> str:
    if is_silent(mm):
        return "silent (no measurable audio), left as is"
    return f"I {mm['input_i']:.1f} LUFS  TP {mm['input_tp']:.1f} dBTP  LRA {mm['input_lra']:.1f}  " + \
           ("PASS" if in_spec(mm) else f"FAIL (target {TARGET_I} LUFS, {TARGET_TP} dBTP)")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "--fix":
        res = fix(a[1], a[2])
        print(report(res))
        sys.exit(0 if in_spec(res) else 1)
    res = measure(a[0])
    print(report(res))
    sys.exit(0 if in_spec(res) else 1)
