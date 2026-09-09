# Snake Battle — MANUAL

> Language: [ไทย](MANUAL.md) · **English** · [日本語](MANUAL.ja.md)

A local snake game written in pure `turtle` (no pygame for drawing). Two modes:
**1 Player** and **2 Player Battle**. Pick a character and a power before each match.

The only entry point is **`main.py`**.

---

## 1. Install & run

**Required**

- Python 3.8+ with `tkinter` (turtle uses tkinter underneath)
  - Windows / macOS: the python.org installer already includes it
  - Ubuntu / Debian: `sudo apt install python3-tk`
- **Nothing else to install** — the game is `turtle` + the standard library.
  The sprites in `assets/*.gif` ship with the repo.
- Optional
  - `pip install pillow` — only to regenerate sprites with `make_sprites.py`
    (e.g. after adding a character)

> **pygame is not required.** Graphics and sound both work on turtle + stdlib alone
> (sound: see section 6).

**Run**

```bash
python main.py            # play
python make_sprites.py    # regenerate every GIF sprite (needs Pillow)
```

Startup prints one sound-status line, e.g. `SOUND: 8 events via winsound`, or an
explanation of why there is no sound yet and what to do about it.

The font and the window icon are configurable in `config.py` — see 9.4 and 9.5.

---

## 2. File layout

Organised to the **baseline kit format** (Sections 1-5). No file exceeds 500 lines.

```
Code/snake_battle_2P/
├── main.py            26   ← entry point, run this
│
├── config.py         197   Section 3  every constant + character and power registries
├── engine.py         443   Section 1  the one Screen, sprites, scenes, drawing helpers
├── entity.py         263   Section 2  the Snake both modes use + the power runtime
├── audio.py          281              non-blocking sound (silent when no files exist)
│
├── screens.py        421              Main Menu, Character Select, result screens
├── solo.py           209              1 Player mode      Sections 2, 3, 4, 5
├── battle.py         476              2 Player Battle     Sections 2, 3, 4, 5
│
├── make_sprites.py   138              sprite generator (a tool, not runtime; needs Pillow)
└── assets/                            sprite *.gif (+ sounds/ if you add .wav)
```

**Where Sections 1-5 live**

| Section | Where |
|---|---|
| 1 Screen Setup | `engine.py` — turtle allows one Screen per process, so it is centralised |
| 2 Game Entities | `entity.py` (Snake) + a Section 2 heading in each mode file and `screens.py` |
| 3 Parameters & Physics | `config.py` project-wide + a Section 3 heading in each mode file for its own layout |
| 4 Input Handling | a Section 4 heading in each mode file and `screens.py` |
| 5 Main Game Loop | a Section 5 heading in `solo.py` / `battle.py` (`wn.ontimer(game_loop, 16)`) |

**Import direction** — `config` imports nothing → `engine` creates the Screen →
`audio` / `entity` build on it → `screens` / `solo` / `battle` → nothing imports `main`.

> **Which file calls which, at what line** — see [CODE_REVIEW.md](CODE_REVIEW.md):
> the import graph both ways (imports / imported by) with line numbers, plus the review findings.

`snake_battle_2P.py` (the original 633-line single file) **has been deleted**; nothing
imported it. To read it back: `git show 33d5b4c:Code/snake_battle_2P/snake_battle_2P.py`

---

## 3. Controls

**Main Menu** — click a button, or press `1` / `2`

**Character Select** — one big card per player with **◀ ▶** arrows above it to flip
through the roster (clicking the card itself also steps forward). Power icons are
clickable across the whole box. The dots under the card show your position in the
roster. Keyboard works too:

| | Character | Power |
|---|---|---|
| P1 | `A` / `D` | `W` / `S` |
| P2 | `←` / `→` | `↑` / `↓` |

`Enter` starts · `Esc` back to the menu

**In game**

| | 1 Player | 2 Player |
|---|---|---|
| Move | Arrows | P1 `W A S D` · P2 Arrows |
| Use power | `SPACE` | P1 `Q` (or `E`) · P2 `O` (or `P`) |
| Sound on/off | `X` | `X` |
| Restart | `R` (after game over) | `R` (on ROUND OVER = **next round**, tally + MVP ledger carried over) |
| Back to menu | `M` | `M` |

> **One power key per player**, whatever power they picked, because each player picks
> exactly one. That is why the registry can grow past two powers without running out
> of keys to bind.

**Reading the 2P HUD**

| What you see | Where | Means |
|---|---|---|
| hearts + name + score | top left / top right | HP and this round's score |
| your coloured bar | under the name | the power meter, full at 100 |
| **the power icon** | **beside the bar** | the power you picked — what `Q` / `O` will fire |
| `P1  1 - 0  P2` | centre, gold | the round tally for the match |
| `STUN` / `BOOST` / `CLOAK` | **floating over the snake** | that snake's state right now |

> `STUN` used to sit beside the power bar, where it read as a state of the *skill* —
> which is what made it confusing. It now floats over the snake's head, where you are
> actually looking, and the icon of the power you chose took its place beside the bar.
> The label flips to **below** the head automatically when the snake is near the top
> wall, so it never collides with the HUD strip.

---

## 4. Characters (4)

| Character | Colour |
|---|---|
| AQUA | cyan |
| EMBER | orange |
| VENOM | green |
| ROYAL | violet |

**All four play identically** — colour only. None is tougher or faster. A character is
a skin, and in 2P it is also how you tell the snakes apart. That is why **the two
players cannot pick the same one** — the arrows skip whatever the other player holds.
Powers may be duplicated freely.

**Adding a character** — append an entry to `config.py` (Section 3F) and run
`python make_sprites.py`. Character Select reads the count from the registry itself
(the dots grow with it); no UI code to change.

To supply your own `.gif` instead of generating — see section 9.

> The card portrait is drawn with turtle only (a compound shape tinted per character),
> not from an image file, and a sprite `.gif` cannot be used for it: **turtle cannot
> scale an image shape**, so a 20x20 head stays 20x20 whatever `shapesize()` says.

---

## 5. Powers (5)

| Power | Effect | Cost | Duration |
|---|---|---|---|
| **SPEED** | move twice as fast | 50 | 180 frames |
| **STEALTH** | body vanishes, head goes ghost (**still solid to everything**) | 50 | 180 frames |
| **SHIELD** | take no damage at all | 50 | 150 frames |
| **PHASE** | slip through boxes and your own tail | 50 | 150 frames |
| **FEAST** | fruit is worth double | 40 | 240 frames |

The bar caps at 100 and gains +25 per fruit (2P) / +20 (1P). A power cannot be
re-triggered while it is still running.

**Adding a power** — `config.py` (Section 3G) writes each `effect` as EFFECT KINDS the
game already applies:

```python
speed_mult   float   head speed multiplier
score_mult   float   fruit score multiplier
cloak        bool    hide the body, swap the head for the ghost sprite
invincible   bool    ignore incoming damage
noclip       bool    obstacles and your own body stop hurting
```

> `cloak` only hides the body — it does **not** let you pass through anything. Only
> `noclip` (PHASE) and `invincible` (SHIELD) exempt you from collisions. 1P used to
> exempt `cloak` as well while 2P did not, which made STEALTH a strictly better PHASE
> in 1P. That is fixed; both modes agree now.

If a new power reuses existing kinds → **append an entry, give it an icon, done — no
game code changes at all.** If it needs a genuinely new kind, add the key here and read
it with `powers_flag()` / `powers_effect()` from `entity.py` at the one place that
should honour it. Nothing in the game hardcodes a power name.

---

## 6. Sound — step by step

**No audio is generated and no package is required.** With no audio files present
every `sfx.play()` returns immediately and the game runs exactly as it would with the
sound code absent.

### Step 1 — know which sounds the game asks for

Nine events, called from these places:

| event | plays when | called from |
|---|---|---|
| `eat` | fruit collected | `solo.py` · `battle.py` |
| `hit` | HP lost (enemy hit or self hit) | `battle.py` |
| `bump` | hit a wall or a box | `battle.py` |
| `power` | a power actually fired | `solo.py` · `battle.py` |
| `win` | the RESULT screen with a winner | `battle.py` |
| `lose` | GAME OVER in 1P | `solo.py` |
| `select` | character / power picked | `screens.py` |
| `start` | a match begins | `screens.py` · `solo.py` · `battle.py` |
| `score` | not used yet — reserved | – |

### Step 2 — where the files go (**two folders, your choice**)

The repo already has a `sound_effect/` folder at its root (12 `.mp3` files today).
The game searches **both** folders and takes the first hit, in this order:

```
BattleofSnake/
├── sound_effect/                          ← option 2  (where your pack already lives)
│   ├── eat.wav                                  ← the event name (beats eat_fruit.wav)
│   ├── eat_fruit.wav                            ← convert in place, no renaming needed
│   └── eat_fruit.mp3                            ← the original mp3 (pygame only)
└── Code/snake_battle_2P/
    └── assets/sounds/                     ← option 1, beats everything
        └── eat.wav
```

| Order | The game looks for | Notes |
|---|---|---|
| 1 | `assets/sounds/<event>.wav` | wins over everything; the "official" spot |
| 2 | `sound_effect/<event>.wav` | e.g. `sound_effect/eat.wav` — **easiest: just drop it in** |
| 3 | `sound_effect/<pack name>.wav` | e.g. `sound_effect/eat_fruit.wav` — convert the mp3s in place, keep their names |
| 4 | `sound_effect/<pack name>.mp3` | only with pygame installed · **no pygame = skipped** |

**`.wav` is tried before `.mp3` in every folder**, because `.wav` plays on the standard
library alone.

The extra folders are configurable in `config.py`:

```python
EXTRA_SOUND_DIRS = ['../../sound_effect']   # relative to Code/snake_battle_2P/
```

### Step 3 — name the files after the events

```
eat.wav    hit.wav    bump.wav    power.wav
win.wav    lose.wav   select.wav  start.wav
```

Or keep the pack's own names (option 3 above) — the mapping already exists:

| event | pack names accepted |
|---|---|
| `eat` | `eat_fruit` · `motion_eating` |
| `hit` | `bomb` |
| `bump` | `impact_wall` |
| `power` | `increase_speed` · `skill_selection` |
| `win` | `result_fanfare` |
| `lose` | `bomb` |
| `select` | `setting` · `skill_selection` |
| `start` | `start_1` · `start_2` · `start_3` |
| `score` | `score` (not called by the game yet) |

**Partial sets are fine** — an event with no file is simply silent, never an error.
`eat`, `hit`, `bump`, `power` and `win` are enough to make the game feel complete.

> **Why `.wav`** — on Windows these play through `winsound`, which is in the standard
> library, so there is nothing to install. `.mp3` **cannot** be played by `winsound`
> or by the CLI players. Only pygame reads mp3, and pygame is strictly optional.
>
> Convert the whole folder at once (this writes the `.wav` files next to the `.mp3`
> files, where the game already looks):
>
> ```bash
> cd sound_effect
> for f in *.mp3; do ffmpeg -i "$f" -c:a pcm_s16le -ac 1 -ar 22050 "${f%.mp3}.wav"; done
> ```
>
> PowerShell:
> ```powershell
> cd sound_effect
> Get-ChildItem *.mp3 | ForEach-Object {
>   ffmpeg -i $_.Name -c:a pcm_s16le -ac 1 -ar 22050 ($_.BaseName + ".wav") }
> ```
>
> **`-c:a pcm_s16le` is the part that matters** — without it you get 32-bit float,
> which `winsound` refuses.

### Step 4 — run the game and read the status line

```bash
python main.py
```

```
SOUND: 8 events via winsound          ← working
SOUND: off - no audio files found...  ← no files yet; it says what to do
SOUND: off - only .mp3 files were found, and .mp3 needs pygame...
```

Press **`X`** in game to mute / unmute.

### Files are found but nothing plays — fix it here

**By far the most common cause: the file is not 16-bit PCM.** `winsound` plays only
PCM WAV at 8 or 16 bits. Online converters and Audacity often export **32-bit float**,
which still has a `.wav` extension but `winsound` cannot play it.

The game checks this for you. At startup you will see:

```
SOUND: 2 events via winsound  (4 file(s) skipped as unplayable - see sfx.diagnose())
```

followed by a per-file table:

```
event    status     file / reason
eat      ready      eat.wav  [1 ch, 16-bit, 22050 Hz]
bump     UNUSABLE   bump.wav  <-- not a playable PCM wav: unknown extended format...
power    UNUSABLE   power.wav <-- not a playable PCM wav: unknown format: 2
win      UNUSABLE   win.wav   <-- not a playable PCM wav: file does not start with RIFF id
lose     UNUSABLE   lose.wav  <-- 1 ch, 24-bit - winsound needs 8 or 16-bit, not 24
```

| Message | Means | Fix |
|---|---|---|
| `unknown extended format` | it is 32-bit float | re-encode as 16-bit PCM |
| `unknown format: 2` | it is ADPCM (compressed) | re-encode as 16-bit PCM |
| `does not start with RIFF id` | it is an mp3 renamed `.wav` | actually convert it, do not rename |
| `winsound needs 8 or 16-bit, not 24` | it is 24-bit | re-encode as 16-bit PCM |

**Re-encoding correctly**

```bash
ffmpeg -i broken.wav -c:a pcm_s16le -ac 1 -ar 22050 fixed.wav
```

**In Audacity** — File > Export > Export as WAV, then choose
**"WAV (Microsoft) signed 16-bit PCM"**. Do not pick 32-bit float.

**For live detail** set `SOUND_DEBUG = True` in `config.py`; every failed playback
prints with its reason.

**Check any time**

```python
from audio import sfx
print(sfx.diagnose())
```

### Converting the bundled mp3s to wav

The repo already ships `sound_effect/*.mp3`. Convert them with anything — Audacity, an
online converter, or ffmpeg:

```bash
ffmpeg -i sound_effect/eat_fruit.mp3      -c:a pcm_s16le -ac 1 -ar 22050 assets/sounds/eat.wav
ffmpeg -i sound_effect/bomb.mp3           -c:a pcm_s16le -ac 1 -ar 22050 assets/sounds/hit.wav
ffmpeg -i sound_effect/impact_wall.mp3    -c:a pcm_s16le -ac 1 -ar 22050 assets/sounds/bump.wav
ffmpeg -i sound_effect/increase_speed.mp3 -c:a pcm_s16le -ac 1 -ar 22050 assets/sounds/power.wav
ffmpeg -i sound_effect/result_fanfare.mp3 -c:a pcm_s16le -ac 1 -ar 22050 assets/sounds/win.wav
ffmpeg -i sound_effect/setting.mp3        -c:a pcm_s16le -ac 1 -ar 22050 assets/sounds/select.wav
ffmpeg -i sound_effect/start_1.mp3        -c:a pcm_s16le -ac 1 -ar 22050 assets/sounds/start.wav
```

Mono at 22050 Hz is plenty for SFX — the whole set lands around 660 KB.

### Alternative: install pygame and use the mp3s as they are

```bash
pip install pygame
```

The game then picks up `sound_effect/*.mp3` directly, with no conversion, and gains
overlapping playback. But it is **not necessary** — the `.wav` route needs no install.

### Lookup order and backends

Per event, the first file found wins:

1. `assets/sounds/<event>.wav`
2. every folder in `config.EXTRA_SOUND_DIRS` (default `['../../sound_effect']`)

| backend | install needed | .mp3 | overlapping |
|---|---|---|---|
| `winsound` (Windows stdlib) | **no** ← the main path | no | no |
| command line (afplay/paplay/aplay/ffplay) | no | no | – |
| `pygame.mixer` | yes (optional) | yes | yes |
| silent | – | – | nothing usable found |

### Settings

```python
SOUND_ON     = True                     # config.py - start unmuted
SOUND_DIR    = 'sounds'                 # subfolder of assets/
SOUND_VOLUME = 0.6                      # 0.0-1.0 (pygame backend only)
EXTRA_SOUND_DIRS = ['../../sound_effect']
```

`audio.py` may never raise and never block — a missing file, a broken file or a busy
audio device must not take the game down.

---

## 7. Rules

**Fruit** → +`FRUIT_SCORE` (×2 with FEAST), +1 body segment, power bar up.
2P keeps 2 fruits on the field, at least 40 px apart, and **never on either snake's
body** (it used to be possible, and cost the eater a heart as a self-collision).

**Outer wall / box** → 30-frame stun, direction reset to stop, the move is not
committed (no HP lost). PHASE passes through boxes, but **the outer wall always stops
you**.

**Own body** → **30-frame stun + 1 HP** (the 2 segments right behind the head are
skipped). **No score is lost** — a fumble costs hearts only.

Three guards stop that draining you dry, and all three are needed:

1. **a 70-frame grace window** — without it the check fires every frame, because the
   head is still sitting on its own body
2. **only checked on a frame where the head actually moved** — a snake that bumps a
   wall while coiled has `direction='stop'` and never leaves its own body; without
   this it lost a heart every 70 frames and died standing still
3. **the 60-frame damage immunity is respected** — a self hit right after an enemy hit
   does not stack

The snake coasts out of its own coil once the stun ends, with no key press needed. Set
`SELF_HIT_DAMAGE = 0` in `config.py` for stun only, no HP loss.

### The core game — biting costs the BITER

The loop is **eat fruit → protect your score → bait the other snake into biting you**,
because a bite punishes the **biter**, not the victim. So the snake that is ahead on
score wants to dangle its body and tail in front of the other one's mouth, and the
snake behind has to resist the bait it is being offered — resist it, meet head on
instead, and the snake behind is *paid* for it. That is the second way to score,
alongside fruit.

**The one rule to remember: score only changes hands in a head-to-head clash.** Every
other collision costs hearts and leaves both players' scores completely alone.

| Event | Result |
|---|---|
| **Head to head**, scores differ | the **HIGHER score** loses −1 HP and **hands over half of its own score** to the one behind · **the lower score wins: it is paid, and loses no HP** |
| **Head to head**, scores exactly equal | both lose −1 HP · **no transfer either way** |
| **Your head touches the other snake's body or tail** (a bite) | the **biter loses −1 HP and nothing else** — no score, **not even when the biter is the one behind on score** · the victim loses nothing and gains nothing |
| **Own body** | −1 HP only, no score change |
| **Outer wall / a box** | a 30-frame stun only, no HP and no score |

Body and tail are treated **identically**, on purpose: the old rule rewarded biting the
tail, which worked against the whole point of the game.

> **The clash winner is not charged for biting.** The loser is stunned exactly where
> the heads met, so the winner's head is left touching its neck. The winner therefore
> gets a 30-frame bite grace: it suppresses bite damage only, it is not invulnerability,
> and once it expires biting the other snake's body costs a heart as usual.
>
> **One collision, one resolution.** After the transfer, who is "ahead" flips
> immediately. Without a lock the next frame — heads still touching, the loser stunned
> in place — would punish the snake that just *won* the clash. So the game skips the
> head-to-head check while either snake still has immunity frames: both have to be
> fit again before it counts as a new clash.

A 60-frame immunity follows any damage (the sprite blinks) so one touch cannot
chain-hit. SHIELD blocks the HP loss — and because the transfer is gated on the HP
loss landing, **SHIELD protects the score as a side effect.**

### Winning a round, and winning the match

**One round** → the enemy's HP reaches 0, **or** you reach 500 score. Both at once →
higher score wins; equal → DRAW.

The **round tally** is on screen the whole time as `P1  1 - 0  P2`, both on the in-game
HUD and on the result screen. First to `ROUNDS_TO_WIN` (default 2, i.e. best of 3) takes
the match.

**Score resets every round** (both snakes start a round at 0), but the game keeps a
record of each round so it can add up the whole match at the end.

### MVP = (score + survival bonus) x HP survived

At the end of every round the game records two things per player: **the score they
made that round** and **the HP they had left when it ended**. Then:

```
round MVP = (round score + SURVIVE_BONUS) x HP left
match MVP = every round added up
```

`SURVIVE_BONUS = 100` means **every heart still standing is worth 100 on its own.**
It exists because winning a round on hearts alone at a low score used to be worth an
MVP of 0, which does not reflect what happened; now finishing a round with 3 HP is
worth at least 300.

What has not changed: **a round you were knocked out of (HP = 0) is worth 0 MVP**
however many points you banked, because everything is multiplied by 0. Bank 500 and
then die and you carry away nothing. Surviving weighs exactly as much as scoring.

| Round | Score | HP left | MVP |
|---|---|---|---|
| R1 | 400 | 3 | (400+100)x3 = **1500** |
| R2 | 150 | 0 (knocked out) | **0** |
| R3 | 300 | 0 (knocked out) | **0** |
| Total | 850 | | **1500** |

### When MVP counts — it breaks a tie

**How the match is decided, in order:**

1. **Rounds won** — more rounds takes it (e.g. 2-1). MVP is ignored entirely here.
2. **Rounds level** → the higher **match MVP** wins.
3. **MVP level too** → `A DRAWN MATCH`.

Rounds can end level once `MAX_ROUNDS` (= `ROUNDS_TO_WIN * 2 - 1` = 3) have been
played and nobody reached 2: one round each plus a draw (1 - 1), or three draws (0 - 0).

> `MAX_ROUNDS` also closes a hole: without that ceiling a match where every round is
> drawn would never reach `ROUNDS_TO_WIN` and would loop forever.

### Two result screens

**1. ROUND OVER** — a round finished, the match is still open

```
              ROUND 2 OVER
          P2 EMBER WINS THE ROUND

              P1  1 - 1  P2

        score x hp + 100 per hp left = MVP
   P1  150 x 0 + 0 = 0      480 x 2 + 200 = 1160  P2
        MVP so far    P1 1500    |    P2 1160
          first to 2 rounds takes the match
       Press R for round 3     |     M for Menu
```

(`MVP so far` appears from round 2 on; in round 1 it would only repeat the line above.)

**2. MATCH RESULT** — the match is decided, here is the whole thing

```
                    MATCH RESULT
                P1 AQUA WINS THE MATCH

                   P1  1 - 1  P2

  ROUND  P1 score x hp + bonus = MVP  P2 score x hp + bonus = MVP  WON BY
  R1            400 x 3 + 300 = 1500           200 x 0 + 0 = 0    AQUA
  R2              150 x 0 + 0 = 0        480 x 2 + 200 = 1160    EMBER
  R3              300 x 0 + 0 = 0            300 x 0 + 0 = 0      DRAW
  ----------------------------------------------------------------------
  MVP TOTAL              1500                        1160      MVP: P1

           raw points   P1 850   |   P2 980
       rounds level 1 - 1  ->  MVP decides the match
          Press R for a NEW MATCH  |  M for Menu
```

Everything in one screen: **who won the match** · **score x HP for every round, with
the multiplication shown** · **match MVP** · **raw points** · and a bottom line saying
what actually decided it.

> The example above is MVP doing its job: rounds are level at 1-1 and P2 is ahead on
> raw points (980 to 850), but P2 only survived one round, so their MVP is 1160 while
> P1 survived the round they scored heavily in and finishes on 1500 — **P1 wins.**
> That is why this rule fits the core game: scoring well is not enough, you have to
> still be standing.

| Pressing R | Does |
|---|---|
| on ROUND OVER | plays the next round, **tally and MVP ledger carried over** |
| on MATCH RESULT | starts a fresh match at `0 - 0`, ledger cleared |
| during play | nothing (so a stray press cannot wipe a round) |

`M` back to the menu abandons the match; coming back starts a new one. A DRAW credits
neither player but is still recorded in the ledger (`WON BY` = `DRAW`).

---

## 8. Tuning

| To change | File | Heading |
|---|---|---|
| font · window icon · window size | `config.py` | Section 3A |
| **every colour in the game** (background, wall, boxes, text, cards, buttons) | `config.py` | **Section 3A2 THEME** |
| arena size, speed, HP, score, stun length, boxes, sound | `config.py` | Sections 3B-3E |
| characters: colour + sprite palette | `config.py` | Section 3F |
| powers: effect, cost, duration, icon, blurb | `config.py` | Section 3G |
| per-mode HUD / heart / bar positions | `solo.py` / `battle.py` | Section 3 |
| snake spawn points | `battle.py` | `SPAWN` in Section 3 |

**The knobs people usually want**

```python
SURVIVE_BONUS       = 100   # MVP each surviving heart is worth (0 = no bonus)
SCORE_TRANSFER      = 0.5   # share transferred in a head clash (0 = none, 1.0 = all)
                            # the only place score changes hands in the game
ROUNDS_TO_WIN       = 2     # rounds needed to take the match (2 = best of 3)
MAX_ROUNDS          = ROUNDS_TO_WIN * 2 - 1   # round ceiling, derived - leave it
TARGET_SCORE        = 500   # score that wins a round outright
MAX_HP              = 3
SELF_HIT_DAMAGE     = 1     # HP lost for hitting your own body (0 = stun only)
WALL_MARGIN         = 10    # keeps the head from sinking into the wall = half the sprite
SLOT_COLOR          = {'P1': 'mediumseagreen', 'P2': 'steelblue'}
```

**Dialling the core game up or down**

| You want | Change |
|---|---|
| a head clash to hurt more | raise `SCORE_TRANSFER` (1.0 = the whole score) |
| score never to move at all | `SCORE_TRANSFER = 0.0` (HP loss only) |
| biting to cost score too | subtract from the biter after `punish(biter)` in `resolve_bite()` |
| best of 5 | `ROUNDS_TO_WIN = 3` (`MAX_ROUNDS` follows to 5) |
| survival to matter more | raise `SURVIVE_BONUS` (300 makes one heart worth six fruit) |
| no survival bonus, back to score x HP | `SURVIVE_BONUS = 0` |
| MVP to ignore HP (raw points again) | make `mvp_total()` in `screens.py` `sum(r[slot] for r in rounds)` |
| MVP to decide every match, not just ties | drop the rounds test from `match_champion()` and compare MVP only |
| shorter rounds | lower `TARGET_SCORE`, or lower `MAX_HP` |

Constants are no longer duplicated across the mode files — change `config.py` once and
both modes follow.

---

## 9. Supplying your own art and sound

### 9.1 Upload your own `.gif` (no need to run make_sprites.py)

Put files in `assets/` with these names and the game picks them up — **no code
changes**. `<key>` is `p1` `p2` `p3` `p4` per `config.py` Section 3F.

| File | Size in use | Note |
|---|---|---|
| `<key>_head_up.gif` `_down` `_left` `_right` | 20×20 | **all four directions required** |
| `<key>_head_up_ghost.gif` (+ the other 3) | 20×20 | head while CLOAK is active |
| `<key>_body.gif` | 16×16 | one segment, stamped repeatedly |
| `heart_full.gif` / `heart_empty.gif` | 18×18 | HP hearts |
| `fruit.gif` | 16×16 | fruit |

**Rules you cannot get around** (turtle limitations, not the game's)

- Must be **GIF** — a `.png` also works: `load_shape()` converts it to `.gif` once
  (needs Pillow)
- **turtle cannot rotate an image**, hence four separate head files
- **turtle cannot scale an image** → **the file's pixel size IS the in-game size**;
  `shapesize()` does nothing. Want a bigger snake? Make a bigger file.
- GIF transparency is **on/off** only, no soft edges
- A missing or broken file is not fatal — that part falls back to a coloured square
- Set `USE_SPRITES = False` in `config.py` to force coloured squares everywhere

### 9.2 Can I recolour the body myself? Yes — by NOT shipping a body gif

**turtle cannot tint an image.** A `.gif` is a Tk image item; `color()` has no effect
on it at all. So if you ship `<key>_body.gif`, its colour is **baked into the file**
and `config.py` cannot change it.

Head and body are therefore decided **separately**. Four combinations:

| head gif | body gif | Result |
|---|---|---|
| ✅ | ✅ | both from your art — colour lives in the files |
| ✅ | ❌ | **head from your art, body a coloured square from `config.py`** ← this one |
| ❌ | ✅ | body from art, head a coloured square |
| ❌ | ❌ | coloured squares throughout |

> **So:** to have a nice hand-drawn head but still control the body colour in code,
> **ship only `<key>_head_*.gif` and no `<key>_body.gif`.** The body then uses that
> character's `main` colour, editable in `config.py` without touching any image.

All four combinations are tested and render without error.

> Note: `<key>_body_ghost.gif` **is not used** — CLOAK hides the body entirely rather
> than swapping in a ghost body. Don't spend time on that file.

### 9.3 Supplying your own sound

See **section 6** for the full step-by-step. In short: put `.wav` files in
`assets/sounds/` named after the events (`eat` `hit` `bump` `power` `win` `lose`
`select` `start`). Partial sets are fine, and nothing needs installing.

---

## 9.4 Changing the font

`config.py` → `FONT_CANDIDATES` is a **list**, not a single name, because tkinter
silently substitutes a different font when the one you asked for is missing — so you
never find out what you actually got. `engine.py` asks Tk which families exist and
picks **the first name in the list that this machine really has**.

```python
FONT_CANDIDATES = ['Consolas', 'Cascadia Mono', 'Courier New',
                   'DejaVu Sans Mono', 'Liberation Mono', 'Courier']
```

Put your preferred font first and keep a generic monospace last as the safety net. One
list works on Windows and Linux alike (Windows lands on Consolas, Linux on DejaVu).

## 9.5 Changing the window icon (replacing tkinter's feather)

Put your logo in `assets/` under one of these names — **first file found wins**:

```python
WINDOW_ICON = ['icon.png', 'icon.gif', 'logo.png', 'logo.gif', 'icon.ico']
```

| Extension | Works where | Note |
|---|---|---|
| `.png` `.gif` | **every OS** (Tk 8.6+) | recommended, via `iconphoto` |
| `.ico` | **Windows only** | via `iconbitmap` — Linux/Tk rejects it |

32×32 or 64×64 is a good size. With no file present the default tkinter icon simply
stays; it is not an error.

---

## 10. Technical notes (turtle has a lot of traps)

Each of these cost a real bug. Kept here so they don't come back:

- **A shape turtle always covers text.** turtle redraws a turtle's cursor with
  `tag_raise` every frame, so it floats above pen drawings and `write()` text no matter
  the creation order. Anything that needs text on top must be pen-drawn
  (`engine.filled_rect`) with clicks hit-tested (`wn.onscreenclick` +
  `engine.inside_rect`).
- **`onclick()` does not work on a multi-component compound shape.**
  `turtle.turtle._item` is a LIST there, so `tag_bind` matches nothing. Hit-test
  coordinates instead.
- **Shapes rotate by `heading - 90`** because turtle's built-ins are authored nose-up.
  Shapes in `engine.py` are authored in screen coordinates, so display them through
  `engine.shape_turtle()`, which sets heading 90.
- **Turtles must be destroyed on a scene change.** `hideturtle()` is not enough: delete
  the canvas items (`items`, `stampItems`, `drawingLineItem`, `_fillitem`, and the
  cursor — a LIST for compound shapes) and unregister the turtle, or every scene switch
  leaks. `engine.clear_all_turtles()` does this.
- **Image shapes are GIF only**, cannot rotate or scale, **and cannot be tinted**
  (`color()` has no effect on a Tk image item), so the colour lives in the art — see 9.2.
- **`addshape()` raises `tkinter.TclError`, not `TurtleGraphicsError`,** for a
  truncated GIF or a `.png` renamed `.gif`. Catching only `TurtleGraphicsError` let a
  bad sprite crash the whole scene, and because the cache was never written every retry
  crashed again. `load_shape()` now catches broadly and caches the failure.
- **Self-collision needs a grace window** or it retriggers every frame; see section 7.
- **The head must be stamped last** — canvas items keep creation order.
- **Body segments are placed by walking the path backwards accumulating distance**, not
  by a frame offset, or the body spreads apart while SPEED is active.
- **Sprites are drawn centred.** Letting the head's *centre* reach the arena edge sank
  half the sprite into the wall (measured: exactly 10 px, half of a 20×20 head), hence
  `WALL_MARGIN`.
- **tkinter substitutes fonts silently.** Ask `tkinter.font.families()` what actually
  exists before choosing — `engine._pick_font()` does.
