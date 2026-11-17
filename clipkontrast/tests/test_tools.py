"""The errors people hit on a fresh install: ffmpeg not found ("[WinError 2]"), the speech model not downloaded,
and an AI model name the service does not know. Runs against the code directly; nothing is downloaded."""
import io, os, shutil, sys, tarfile, tempfile
from pathlib import Path
os.environ["CLIPKONTRAST_DATA"] = tempfile.mkdtemp(prefix="pc-tools-"); os.environ["DATABASE_URL"] = ""
os.environ.pop("CLIPKONTRAST_MODELS", None)          # this test makes and removes a model: only ever inside its own folder
os.environ.update(CLIPKONTRAST_AI_PROVIDER="gemini", CLIPKONTRAST_AI_MODELS="gemini-old", CLIPKONTRAST_AI_KEY="test-key-123456")
sys.path.insert(0, ".")
from studio import ai, config, fetch_model, safe, tools
fails = []
def check(n, got, want=True):
    ok = want(got) if callable(want) else got == want
    print(("PASS " if ok else "FAIL ") + n + ("" if ok else f"   got {got!r}")); ok or fails.append(n)

# ---- ffmpeg
real_path = os.environ.get("PATH", "")
exe = ".exe" if sys.platform == "win32" else ""
hidden = tempfile.mkdtemp(prefix="pc-ff-")
for name in tools.NEEDED:
    f = Path(hidden) / (name + exe); f.write_bytes(b"x"); f.chmod(0o755)
os.environ["PATH"] = tempfile.mkdtemp(prefix="pc-empty-")            # a PATH with no ffmpeg on it
real_places = tools._places
tools._places = lambda: []
check("with ffmpeg nowhere, both programs are reported missing", tools.setup(), ["ffmpeg", "ffprobe"])
err = FileNotFoundError(2, "The system cannot find the file specified")
check("the bare Windows error becomes what to do about it", "ffmpeg" in safe.friendly(err) and "install" in safe.friendly(err), True)
check("...also when it arrives as text", "ffmpeg" in safe.friendly(RuntimeError("[WinError 2] The system cannot find the file specified")), True)
check("an unrelated error is left as it is", safe.friendly(ValueError("That link is a playlist.")), "That link is a playlist.")
tools._places = lambda: [Path(hidden)]
check("installed but not on the PATH yet: found in its folder and used from there", (tools.setup(), bool(shutil.which("ffmpeg"))), ([], True))
os.environ["PATH"] = real_path
os.environ["CLIPKONTRAST_FFMPEG_DIR"] = hidden
tools._places = real_places
check("CLIPKONTRAST_FFMPEG_DIR is looked in first", tools._places()[0], Path(hidden))
tools.setup()

# ---- the speech model
d = config.ASR_MODEL_DIR
assert str(d).startswith(os.environ["CLIPKONTRAST_DATA"]), "the test must only touch its own folder"
check("no model to begin with", fetch_model.ready(), False)
d.mkdir(parents=True); (d / "tokens.txt").write_text("a 1")
check("half a model (a download that was cut off) does not count", fetch_model.ready(), False)
def fake_download(url, dest, hook=None):
    buf = tempfile.mkdtemp(prefix="pc-tar-")
    src = Path(buf) / config.ASR_MODEL_NAME; src.mkdir()
    for n in ("tokens.txt", "encoder.int8.onnx", "decoder.int8.onnx", "joiner.int8.onnx"):
        (src / n).write_bytes(b"model")
    with tarfile.open(dest, "w:bz2") as t:
        t.add(src, arcname=config.ASR_MODEL_NAME)
    if hook: hook(1, 100, 100)
fetch_model.urllib.request.urlretrieve = fake_download
fetch_model.ensure()
check("the model is downloaded by itself and put in place whole", (fetch_model.ready(), sorted(p.name for p in d.iterdir())),
      (True, ["decoder.int8.onnx", "encoder.int8.onnx", "joiner.int8.onnx", "tokens.txt"]))
check("nothing is left over from the download", sorted(p.name for p in config.MODELS_DIR.iterdir()), [config.ASR_MODEL_NAME])
shutil.rmtree(d)
def no_internet(url, dest, hook=None):
    raise OSError("getaddrinfo failed")
fetch_model.urllib.request.urlretrieve = no_internet
try:
    fetch_model.ensure(); said = ""
except RuntimeError as e:
    said = str(e)
check("no internet: said in plain words, and no half model left behind", ("internet" in said, fetch_model.ready(), d.exists()), (True, False, False))

# ---- the AI
check("an unknown model name", ai.explain("HTTP 404 models/gemini-old is not found for API version v1beta"), lambda s: "gemini-old" in s and "Find models" in s)
check("a refused key", ai.explain("HTTP 400 API key not valid. Please pass a valid API key."), lambda s: "refused the key" in s)
check("out of quota", ai.explain("HTTP 429 You exceeded your current quota"), lambda s: "limit" in s)
check("cannot be reached", ai.explain("[Errno 11001] getaddrinfo failed"), lambda s: "couldn't reach" in s)
check("anything else is not guessed at", ai.explain("something odd"), "")
ai.note_problem("HTTP 404 model not found")
check("the reason is kept for the dashboard, and cleared when the AI answers again", (bool(ai.problem["text"]), (ai.clear_problem(), ai.problem["text"])[1]), (True, ""))

print("ALL PASSED" if not fails else f"{len(fails)} failed")
shutil.rmtree(os.environ["CLIPKONTRAST_DATA"], ignore_errors=True); shutil.rmtree(hidden, ignore_errors=True)
sys.exit(1 if fails else 0)
