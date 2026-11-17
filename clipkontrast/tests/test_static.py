"""Commercials and "be right back" screens are stitched into streams. A clip taken from one is
worthless, so those seconds must be found and left out.

Runs against the code directly, with its own empty data folder."""
import os, subprocess, sys, tempfile
os.environ["CLIPKONTRAST_DATA"] = tempfile.mkdtemp(prefix="pc-static-")
sys.path.insert(0, ".")
from studio import quality
fails = []
def check(n, got, want=True):
    ok = want(got) if callable(want) else got == want
    print(("PASS " if ok else "FAIL ") + n + ("" if ok else f"   got {got!r}")); ok or fails.append(n)

# ---- a short video: moving picture for four seconds, then a frozen screen
path = os.path.join(os.environ["CLIPKONTRAST_DATA"], "with_slate.mp4")
subprocess.run(["ffmpeg", "-y", "-v", "error",
                "-f", "lavfi", "-i", "testsrc2=size=320x568:rate=15:d=4",
                "-f", "lavfi", "-i", "color=c=gray:size=320x568:rate=15:d=10",
                "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]", "-map", "[v]",
                "-c:v", "libx264", "-preset", "ultrafast", path], check=True)
ranges = quality.static_ranges(path, bucket=1.0)
check("the frozen screen is found", any(b - a >= 6 for a, b in ranges), True)
check("the moving picture is not", any(a < 2 and b > 3 for a, b in ranges), False)

# ---- how much of a clip sits inside a static stretch
check("a clip inside the slate is mostly static", quality.static_overlap(5.0, 14.0, ranges) > 8.0)
check("a clip on the gameplay is not", quality.static_overlap(0.0, 3.0, ranges) < 1.0)

# ---- a video that never moves is one long static stretch
still = os.path.join(os.environ["CLIPKONTRAST_DATA"], "still.mp4")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=gray:size=320x568:rate=15:d=12",
                "-c:v", "libx264", "-preset", "ultrafast", still], check=True)
check("a video that never moves is one long stretch", len(quality.static_ranges(still, bucket=1.0)) == 1)

# ---- a missing file must not stop a job
check("a file that cannot be read gives nothing, not an error", quality.static_ranges(os.path.join(os.environ["CLIPKONTRAST_DATA"], "nope.mp4")), [])

# ---- it is offered, but it is off until asked for
from studio import config
check("the static skip is off by default", config.SKIP_STATIC, False)
check("the threshold can still be set", config.STATIC_THRESHOLD > 0, True)

print("ALL PASSED" if not fails else f"{len(fails)} FAILED")
sys.exit(1 if fails else 0)
