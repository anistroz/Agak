"""A model that is not careful writes a sentence in front of the JSON, a second object after it, or a
code fence around it. The answer is looked for inside the answer rather than demanded of it.

Runs against the code directly, with its own empty data folder."""
import os, sys, tempfile
os.environ["CLIPKONTRAST_DATA"] = tempfile.mkdtemp(prefix="pc-answer-")
sys.path.insert(0, ".")
from studio.ai import _parse
fails = []
def check(n, got, want=True):
    ok = want(got) if callable(want) else got == want
    print(("PASS " if ok else "FAIL ") + n + ("" if ok else f"   got {got!r}")); ok or fails.append(n)

check("plain JSON is read", _parse('{"items":[{"hook":"A"}]}'), [{"hook": "A"}])
check("a sentence in front is ignored", _parse('Here you go: {"items":[{"hook":"B"}]}'), [{"hook": "B"}])
check("a sentence after is ignored", _parse('{"items":[{"hook":"C"}]} Hope that helps!'), [{"hook": "C"}])
check("a second object after the first is ignored", _parse('{"items":[{"hook":"D"}]}\n{"items":[{"hook":"E"}]}'), [{"hook": "D"}])
check("a code fence around it is ignored", _parse('```json\n{"items":[{"hook":"F"}]}\n```'), [{"hook": "F"}])
check("two objects in one line: the first is read", _parse('{"items":[{"hook":"H"}]} and {"items":[{"hook":"I"}]}'), [{"hook": "H"}])
try:
    _parse('{"items":[{"hook":"G"}]')
    check("an answer with no closing bracket is refused", False, True)
except Exception:
    check("an answer with no closing bracket is refused", True, True)

# ---- a hand-picked clip: an empty answer is asked once more, and a clip is never lost to it
from unittest.mock import patch
from studio import brain
item = {"start": 0, "end": 0, "score": 70, "category": "funny", "hook": "WILD NIGHT", "title": "T",
        "description": "D", "hashtags": ["Gaming"], "highlight_words": []}
words = "Okay, I hope. You are all planning wild night out there. You can"
with patch.object(brain, "ask_ai", side_effect=[([], "m", 1), ([item], "m", 2)]) as ask:
    c = brain.describe(words, "GTA V #16", "Chan")
    check("an empty answer is asked again", ask.call_count, 2)
    check("the second answer is used", c["hook"], "WILD NIGHT")
with patch.object(brain, "ask_ai", side_effect=[([], "m", 1), ([], "m", 2)]):
    c = brain.describe(words, "GTA V #16", "Chan")
    check("two empty answers give a clip with no hook, not an error", c["hook"], "")
with patch.object(brain, "ask_ai", side_effect=RuntimeError("The AI did not answer")):
    c = brain.describe(words, "GTA V #16", "Chan")
    check("a failed call gives a clip with no hook, not an error", c["hook"], "")

print("ALL PASSED" if not fails else f"{len(fails)} FAILED")
sys.exit(1 if fails else 0)
