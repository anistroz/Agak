"""Where ClipKontrast keeps everything: one folder, which the owner can see, open and move.

Everything ClipKontrast makes or downloads lives in one folder: the videos, the clips, the recordings, the list of
creators, the database and the speech model. By default that is the "data" folder inside ClipKontrast's own folder.
It can be moved (to a bigger drive, for instance) from Settings, Storage: the choice is written to storage.json,
and the next time ClipKontrast starts it moves what is there and carries on from the new place (see config.py; nothing
is moved while ClipKontrast is running, when files are open)."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from . import config, load

_used = {"at": 0.0, "bytes": 0}


def _size(folder: Path) -> int:
    total = 0
    for root, _dirs, files in os.walk(folder):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def used_bytes() -> int:
    """How much ClipKontrast's folder holds. Added up at most once a minute."""
    if time.time() - _used["at"] > 60:
        _used.update(at=time.time(), bytes=_size(config.DATA_DIR))
    return _used["bytes"]


def drive_of(path: Path) -> str:
    p = Path(path).resolve()
    return p.drive or p.anchor or str(p)


def full_message() -> str:
    """What to tell someone when there is no room for a new video: which drive, how much is left, what to do."""
    try:
        free = shutil_free(config.DATA_DIR)
    except OSError:
        free = 0.0
    return (f"The drive ClipKontrast saves to ({drive_of(config.DATA_DIR)}) is almost full: {free:.1f} GB free, and ClipKontrast needs "
            f"at least {load.MIN_FREE_DISK_GB:g} GB to make clips safely. Free up some space on that drive, or move "
            f"ClipKontrast's folder to a bigger drive in Settings, Storage.")


def shutil_free(path: Path) -> float:
    import shutil
    return shutil.disk_usage(path).free / 1e9


def pending() -> str:
    """A new folder that was chosen and takes effect at the next start, or ""."""
    try:
        d = json.loads(config.STORAGE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    p = str(d.get("path") or "")
    return p if p and Path(p).resolve() != config.DATA_DIR.resolve() else ""


def info(local: bool) -> dict:
    import shutil
    try:
        u = shutil.disk_usage(config.DATA_DIR)
        free, total = u.free / 1e9, u.total / 1e9
    except OSError:
        free, total = 0.0, 0.0
    return {"path": str(config.DATA_DIR.resolve()), "drive": drive_of(config.DATA_DIR), "free_gb": round(free, 1),
            "total_gb": round(total, 1), "used_gb": round(used_bytes() / 1e9, 2), "min_free_gb": load.MIN_FREE_DISK_GB,
            "full": free < load.MIN_FREE_DISK_GB, "fixed": config.DATA_FROM == "env", "pending": pending(),
            # opening a folder or showing a "choose folder" window only makes sense on the computer ClipKontrast runs on
            "local": bool(local)}


def open_folder():
    """Show ClipKontrast's folder in the computer's file manager."""
    p = str(config.DATA_DIR.resolve())
    if sys.platform == "win32":
        os.startfile(p)                                   # noqa: S606 - the owner's own folder, on their own computer
    elif sys.platform == "darwin":
        subprocess.Popen(["open", p])
    else:
        subprocess.Popen(["xdg-open", p])


_PICK = ("import tkinter as tk\nfrom tkinter import filedialog\nr = tk.Tk()\nr.withdraw()\nr.attributes('-topmost', True)\n"
         "print(filedialog.askdirectory(title='Choose where ClipKontrast keeps its videos and clips') or '')\n")


def pick_folder() -> str:
    """The computer's own "choose a folder" window. Returns the folder, or "" if it was closed or cannot be shown."""
    try:
        r = subprocess.run([sys.executable, "-c", _PICK], capture_output=True, text=True, timeout=600,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.TimeoutExpired):
        return ""
    out = (r.stdout or "").strip().splitlines()
    return str(Path(out[-1])) if r.returncode == 0 and out and out[-1].strip() else ""


def change(path: str, move: bool = True) -> dict:
    """Choose a new folder. It is checked now (it can be made, written to, and has room) and used from the next
    start; with `move`, what is in the current folder is moved there then."""
    if config.DATA_FROM == "env":
        raise ValueError("The folder is set with CLIPKONTRAST_DATA in the .env file. Change it there, or remove that line to choose it here.")
    raw = str(path or "").strip().strip('"')
    if not raw:
        raise ValueError("Choose a folder.")
    new = Path(os.path.expanduser(raw))
    if not new.is_absolute():
        raise ValueError("Give the whole path of the folder, for example D:\\ClipKontrast.")
    new, old = new.resolve(), config.DATA_DIR.resolve()
    if new == old:
        raise ValueError("That is the folder ClipKontrast already uses.")
    if old in new.parents or new in old.parents:
        raise ValueError("Choose a folder that is not inside ClipKontrast's current folder (or the other way round).")
    try:
        new.mkdir(parents=True, exist_ok=True)
        probe = new / ".clipkontrast-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError:
        raise ValueError("ClipKontrast can't write to that folder. Choose another one, or check the drive is connected.")
    need = used_bytes() / 1e9 if move and drive_of(new) != drive_of(old) else 0.0
    if shutil_free(new) < need + load.MIN_FREE_DISK_GB:
        raise ValueError(f"There isn't enough room there: {shutil_free(new):.1f} GB free, and ClipKontrast needs about "
                         f"{need + load.MIN_FREE_DISK_GB:.1f} GB.")
    data = {"path": str(new)}
    if move:
        data["move_from"] = str(old)
    tmp = config.STORAGE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
    tmp.replace(config.STORAGE_FILE)
    return {"path": str(new), "move": bool(move)}


def cancel_change():
    """Forget a chosen folder that has not taken effect yet."""
    if pending():
        if config.DATA_FROM == "chosen":
            config.STORAGE_FILE.write_text(json.dumps({"path": str(config.DATA_DIR.resolve())}, indent=1), encoding="utf-8")
        else:
            config.STORAGE_FILE.unlink(missing_ok=True)
