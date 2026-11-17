"""Ad breaks and static screens.

Twitch and YouTube stitch commercials into a stream, and a "be right back" slate
can sit where the good moment is. A clip taken from there is worthless, so those
seconds are found and left out.

Metric: mean absolute luma difference between consecutive frames
(tblend=difference + signalstats). Measured on real captures:

    ad slate         ~0.19
    gameplay clip    ~1.6 - 2.5

A flat 0-255 luma difference separates them with a wide margin, so no OCR, no
reference image and no model is needed. The frames are read once for the whole
video, and clips are then checked against that map.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from . import config

_FFMPEG = "ffmpeg"

_PTS = re.compile(r"pts_time:([0-9.]+)")
_YAVG = re.compile(r"lavfi\.signalstats\.YAVG=([0-9.]+)")


def motion_map(path: str | Path, bucket: float = 2.0) -> list[tuple[float, float]]:
    """(time, motion) for every bucket of the video, or nothing if it cannot be read.

    Motion is the mean luma difference between consecutive frames: near zero for a
    frozen screen, high for anything actually moving."""
    try:
        proc = subprocess.run(
            [_FFMPEG, "-hide_banner", "-loglevel", "error",
             "-i", str(path),
             "-vf", "tblend=all_mode=difference,signalstats,metadata=print:file=-",
             "-an", "-f", "null", "-"],
            capture_output=True, text=True, timeout=900,
        )
    except Exception:  # noqa: BLE001 - a missing ffmpeg must not stop a job
        return []
    times: list[float] = []
    vals: list[float] = []
    at = 0.0
    for line in (proc.stdout or "").splitlines():
        m = _PTS.search(line)
        if m:
            at = float(m.group(1))
            continue
        m = _YAVG.search(line)
        if m:
            times.append(at)
            vals.append(float(m.group(1)))
    if len(vals) > 1:
        times, vals = times[1:], vals[1:]      # the first blended frame is against black
    if not vals:
        return []
    buckets: dict[int, list[float]] = {}
    for t, v in zip(times, vals):
        buckets.setdefault(int(t / bucket), []).append(v)
    return [(i * bucket, sum(v) / len(v)) for i, v in sorted(buckets.items())]


def static_ranges(path: str | Path, bucket: float = 2.0, threshold: float | None = None,
                  min_seconds: float | None = None) -> list[tuple[float, float]]:
    """The stretches that look like an ad break, a slate or a frozen screen."""
    threshold = config.STATIC_THRESHOLD if threshold is None else threshold
    min_seconds = config.STATIC_MIN_SECONDS if min_seconds is None else min_seconds
    pairs = motion_map(path, bucket)
    if not pairs:
        return []
    runs: list[tuple[float, float]] = []
    start = None
    for t, v in pairs:
        if v < threshold:
            if start is None:
                start = t
        elif start is not None:
            runs.append((start, t))
            start = None
    if start is not None:
        runs.append((start, pairs[-1][0] + bucket))
    return [(a, b) for a, b in runs if b - a >= min_seconds]


def static_overlap(start: float, end: float, ranges: list[tuple[float, float]]) -> float:
    """How much of a clip (in seconds) sits inside a static stretch."""
    total = 0.0
    for a, b in ranges:
        lo, hi = max(a, start), min(b, end)
        if hi > lo:
            total += hi - lo
    return total
