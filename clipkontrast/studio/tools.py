"""The two programs ClipKontrast runs to work on video: ffmpeg and ffprobe.

They are not part of ClipKontrast and have to be on the computer. On Windows a missing one shows up as the bare
"[WinError 2] The system cannot find the file specified", which tells nobody what to do. So ClipKontrast looks for them
itself (also in the places installers put them before Windows has told running programs), uses them from there,
and when they really are missing says so in plain words, before any video is started."""
import os
import shutil
import sys
import time
from pathlib import Path

NEEDED = ("ffmpeg", "ffprobe")
HELP = ("ClipKontrast needs ffmpeg to work on video, and it isn't installed on this computer yet. "
        + ("Open a terminal and run:  winget install Gyan.FFmpeg" if sys.platform == "win32" else
           "Run:  brew install ffmpeg" if sys.platform == "darwin" else "Run:  sudo apt install ffmpeg")
        + "  Then close ClipKontrast and start it again.")
_seen = {"at": 0.0, "missing": list(NEEDED)}


def _places() -> list:
    """Folders ffmpeg is usually installed into, for when it is not on the PATH of this running program."""
    root = Path(__file__).resolve().parent.parent
    out = [root / "ffmpeg" / "bin", root / "bin", root]
    env = os.environ.get
    if env("CLIPKONTRAST_FFMPEG_DIR"):                    # the folder that holds ffmpeg, if it lives somewhere unusual
        out.insert(0, Path(env("CLIPKONTRAST_FFMPEG_DIR")))
    if sys.platform == "win32":
        local = Path(env("LOCALAPPDATA") or "")
        if str(local) not in ("", "."):
            out.append(local / "Microsoft" / "WinGet" / "Links")
            pk = local / "Microsoft" / "WinGet" / "Packages"
            if pk.is_dir():
                for d in pk.glob("*FFmpeg*"):
                    out += [d / "bin", *d.glob("*/bin")]
        for base in (env("ProgramFiles"), env("ProgramFiles(x86)"), env("SystemDrive", "C:") + "\\"):
            if base:
                out += [Path(base) / "ffmpeg" / "bin", Path(base) / "ffmpeg"]
        if env("ProgramData"):
            out.append(Path(env("ProgramData")) / "chocolatey" / "bin")
        if env("USERPROFILE"):
            out += [Path(env("USERPROFILE")) / "scoop" / "shims", Path(env("USERPROFILE")) / "ffmpeg" / "bin"]
    else:
        out += [Path("/opt/homebrew/bin"), Path("/usr/local/bin"), Path("/usr/bin"), Path("/snap/bin")]
    return out


def setup() -> list:
    """Make ffmpeg and ffprobe reachable for everything ClipKontrast runs. Returns the ones that could not be found."""
    exe = ".exe" if sys.platform == "win32" else ""
    missing = []
    for name in NEEDED:
        if shutil.which(name):
            continue
        for d in _places():
            try:
                if (d / (name + exe)).is_file():
                    os.environ["PATH"] = str(d) + os.pathsep + os.environ.get("PATH", "")
                    break
            except OSError:
                pass
        if not shutil.which(name):
            missing.append(name)
    _seen.update(at=time.time(), missing=missing)
    return missing


def missing() -> list:
    """What is still missing. Looked at again every 20 seconds while something is, so installing ffmpeg is noticed
    without a restart whenever its folder is one of the usual ones."""
    if _seen["missing"] and time.time() - _seen["at"] > 20:
        setup()
    return list(_seen["missing"])


def explain(e) -> str:
    """The plain-words version of "the program could not be found", or "" if the error is something else."""
    text = str(e)
    not_found = isinstance(e, FileNotFoundError) or "WinError 2" in text or "No such file or directory: 'ff" in text
    return HELP if not_found and (missing() or "ffmpeg" in text or "ffprobe" in text or "WinError 2" in text) else ""


setup()
