# Gaming mode

ClipKontrast was built for talk: it reads a transcript and picks moments from it. A
gaming stream is mostly not talk — it is a game, a facecam, and a streamer
reacting. Three changes make it work on those streams.

## 1. It knows which game it is

`studio/games.py` reads the game from the stream's title, the video's title, the
channel name, or the game the creator set. Twenty-three games are known by name,
including GTA VI, GTA V, Fortnite, Minecraft, Valorant, Elden Ring, Palworld,
Helldivers 2, Cyberpunk 2077, Marvel Rivals, The Finals, Rocket League and more.

When the game is known, two things change.

**The AI is told what it is looking at** (`GAME_RULES` in `studio/brain.py`):

```
This stream is Grand Theft Auto VI. Pick the moments that only mean something with that
game in mind:
- A play, a death, a jump scare, a glitch, a discovery, or the streamer reacting to one.
- The hook is what was said at that moment, or, if nothing was said, the name of what
  happened in two or three words ("1 VS 3", "THE SHOT", "HE GOT ME", "CLUTCH"). Never a
  sentence that needs the game explained.
- The title names the game when the clip is about it.
- The hashtags include GTA6, GTA6Game, ViceCity, RockstarGames, GTA6Launch.
```

**Every post carries the game's tags** (`_tidy` in `studio/brain.py`), whatever
the AI wrote for itself: `#GTA6`, `#GTA6Game`, `#ViceCity`, `#RockstarGames`,
`#GTA6Launch` for GTA VI; `#GTA5`, `#GTAOnline`, `#GTA5RP` for GTA V. People
search for the game, not for "gaming".

The game is a hint for the copy, never a filter. A stream whose title says GTA 6
but which is really a chat stream still gets clips; they just carry GTA tags.

Where it is read from, in order:

| Where | What it looks at |
|---|---|
| the creator's Setup | the `game` field, if it is set |
| a live stream | the stream's own title — on launch night it says the game |
| a video | the video's title and the file's name |

The creator's own setting wins, so a GTA VI streamer can be pinned to GTA VI
even when a stream's title says nothing.

## 2. The crowd is counted as people

Twitch lets one person send fifty messages in a second. A wave of the same
emote is not a crowd getting excited, but it looked exactly like one to a
counter.

The chat reader now keeps the names as well as the count
(`studio/live.py`, `_chat`), and the two places that ask "did the chat react?"
use people instead of messages:

- the spike watcher (`_chat_spike`): a message jump now has to be backed by more
  different people than usual, or it is not a spike;
- the reaction judge (`judge_signals`): it is shown how many *people* were
  talking in each slice, so a bot storm does not look like a crowd.

If the names cannot be read, the old behaviour is kept — messages are counted
as messages.

## 3. The facecam is found, and the game fills the screen

A gaming stream is a 16:9 game with a small webcam picture in one corner. ClipKontrast's
"blur" layout puts the whole 16:9 frame into a band with blurred fill above and
below — fine for a talking head, poor for a game, where the play is a thin strip
of the picture.

The new **gameplay** layout fills the 1080x1920 frame with the game (centre
cropped, the same as "Fill screen") and puts the webcam in the top corner of it,
so the viewer sees the play and the face at once.

To do that, ClipKontrast has to know where the webcam is. `studio/facecam.py` finds it
by the one thing a webcam always has and a game almost never has: **a straight
border that stays in the same place in every frame**. A wall in the game moves, a
HUD bar changes, the edge of the webcam box does not move at all.

- frames spread through the video are looked at small (320x180)
- for every column and every row, how much the picture changes at that line is
  counted, and the median over the frames is taken, so one busy moment cannot
  invent a line
- the lines that stand out are the borders. Any rectangle they and the frame's own
  edges can make is a candidate: a webcam may sit in a corner, along one edge, or
  even with a margin all round. Square and upright pictures count too, because a
  vertical webcam is common.
- **the picture inside has to be still.** This is what tells a webcam from the
  game's own panels, which have straight borders too and are drawn over the game
  with the game showing through them. A person sits in a room and shifts a little;
  the game behind a panel keeps moving. On a real stream the webcam measured 4
  where the minimap, the chat column, the HUD panel and the scoreboard all measured
  33 to 50.
- the borders are then measured again on a full-size frame, to the pixel

**One frame is also shown to the AI.** Reading a picture of a person is something
a model does far better than any measurement, and it costs one call per stream, not
per clip. What it says is used in a way that cannot do harm: its box picks *which*
of the measured rectangles is the webcam, and if it matches none of them its own box
is put onto the real borders and checked like any other candidate. A model that
only reads text, a service that refuses pictures, or an answer that is nonsense all
leave the measurement alone. If the model looks and says there is no webcam, that is
believed: a stream with no webcam is cropped, which still looks right.

That one frame is a small JPEG of the stream, and it goes to the AI service you
configured, the same service the transcript already goes to. With no AI set, no
picture leaves the machine and the borders are measured on their own.

Only a sure answer is used. If the webcam is not found, the layout falls back to
"Fill screen", which is still the right shape for a game.

| | |
|---|---|
| found in the top-left of a real GTA V stream | 289x162 in a 1280x720 picture, high confidence |
| a game panel in the bottom-right corner of a real stream | refused: it moves with the game behind it |
| time | about 1-4 seconds, once per video or stream |

## 4. Ad breaks and static screens

Already covered: `studio/quality.py` finds the stretches of a video where
nothing moved and drops any clip that sits inside one. On a stream stitched with
commercials, this is the difference between a clip of the game and a clip of a
sponsor reading.

## What it does not do

- **It does not watch the stream.** ClipKontrast reads words, loudness and chat. One frame
  is looked at once, to find the webcam; it cannot tell that a headshot was good,
  only that the streamer said something.
- **It does not know the game's story.** "He got the polaroid photo" means
  nothing to it, unless the streamer says it.
- **The game list is hand-written.** A game that is not in `GAMES` gets no
  special tags. Adding one is a line in that file.

## Settings for launch night

A launch-night roster of game streamers uses:

```json
{ "style": "hype", "layout": "gameplay", "min_len": 15, "max_len": 60,
  "max_clips": 6, "min_score": 65, "auto_watch": false, "buffer_min": 10,
  "live_per_hour": 4, "ai_every_min": 3, "ai_only_on_spike": true }
```

`min_score` is 65 rather than the default 80: launch night is chaotic, and a
tighter bar means fewer clips.

One setting is not in that list because it is an environment variable:
**`CLIPKONTRAST_LIVE_AI_TIMEOUT`** (45 seconds by default) is how long one AI answer
may take on a live stream. It is short on purpose. The AI is asked on its own
thread, so while a model is thinking the speech is still being written and
"clip that" still works — a slow answer costs one check, not the stream.

## The tests

`tests/test_games.py` (17 checks) covers the game reading, the tags, and that
the game's tags are added to a post without losing the AI's own. It is in their
suite as *"knowing which game a stream is"*.
