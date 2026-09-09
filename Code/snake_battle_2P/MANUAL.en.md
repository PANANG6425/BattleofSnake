# Snake Battle — Local Multiplayer | MANUAL

> Language: [ไทย](MANUAL.md) · **English** · [日本語](MANUAL.ja.md)

A 2-player snake fighting game on one machine, written in pure `turtle` (no pygame).
Built on top of `snake_baseline1P.py`

> **This version is split into modules** — the entry point is `main.py` (the old single-file `snake_battle_2P.py` is retired)

---

## 1. Install & run

**Requirements**

- Python 3.8+ with `tkinter` (turtle uses tkinter internally)
  - Windows / macOS: the python.org installer already includes it
  - Ubuntu / Debian: `sudo apt install python3-tk`
- **Nothing extra to install to play** — the bundled sounds and images work as they are
- Optional (only to regenerate assets / for better sound quality)
  - `pip install pillow` — only to run `make_sprites.py` or to drop in your own `.png` files
  - `pip install pygame` — with it, sounds can overlap and latency is lowest (you still get sound without it)

**Run**

```bash
python main.py            # play the game
python make_sprites.py    # regenerate the whole GIF sprite set (needs Pillow)
python make_sounds.py     # regenerate the whole WAV sound set (stdlib only, nothing to install)
```

**File tree**

```
snake_battle_2P/
├── main.py          ← entry point, run this file (wires every module + game loop + Result screen)
├── config.py          every constant, balance the game here
├── screen.py          creates the game's single turtle window (Screen is a singleton)
├── sprites.py         loads GIFs into turtle + converts PNG→GIF for you
├── sounds.py          non-blocking sound playback, picks a backend automatically
├── effects.py         particle system (dust / sparks)
├── arena.py           walls + obstacle boxes + box collision check
├── snake.py           the Snake class (two instances = multiplayer)
├── fruit.py           fruit + safe random placement
├── hud.py             top stats panel + stun bar above each snake's head
├── rules.py           combat rules / fruit pickup / win conditions
├── make_sprites.py    sprite generator (optional)
├── make_sounds.py     sound generator (optional)
└── assets/
    ├── *.gif          sprite images
    └── sounds/*.wav   sounds
```

Import order: `config` → `screen` → `sprites`/`sounds` → `arena`/`effects` → `snake`/`fruit` → `rules`/`hud` → `main`
**Never let a lower module import back up the chain** (that creates a circular import)

> If `assets/` is missing or the files are broken, the game **still runs** — sprites fall back to colored squares and sound goes silent

---

## 2. Controls

| | Player 1 (cyan) | Player 2 (orange) |
|---|---|---|
| Move | `W` `A` `S` `D` | `↑` `↓` `←` `→` |
| Speed Boost | `Q` | `O` |
| Invisibility | `E` | `P` |
| Mute / unmute | `M` | |
| Restart | `R` (Result screen only) | |

> **Click the game window first** or the keys do nothing (turtle needs focus)
> **No 180-degree turn** in any situation — including while stopped or pressed against a wall (see section 9)
> You have to turn left or right once first, like a standard snake game

---

## 3. Rules

### Pickups / hitting obstacles

| Event | Result |
|---|---|
| Eat a fruit 🍎 | +100 score, 1 segment longer, skill bar +25, `eat` sound + sparks |
| Hit an obstacle box | 30 frames of stun + dust + `bump` sound — **no death, no HP loss** |
| Hit an arena wall | Same as an obstacle box |
| Bite yourself / your own tail | Stun — **no death**, and the snake drives itself back out (see section 9) |

### Attacking — the same rules for both players

| Your head hits | Result |
|---|---|
| Enemy **head** | Enemy loses 1 HP + enemy score −50% |
| Enemy **tail** (last segment) | Enemy loses 1 HP + enemy score −50% |
| Enemy **body** (middle segments) | **You** lose 1 HP + your score −50% |

- Head-to-head at the same time = both take damage (the rule is checked in both directions)
- After taking a hit you get **60 frames of immunity**, the sprite flickers, and you cannot be hit again during it
- Collision distance is 12 px (10 px for hitting yourself)

### Skills (cost 50 bar, last 180 frames ≈ 3 s)

| Skill | Result |
|---|---|
| Speed Boost | 3 → 6 px/frame |
| Invisibility | Body disappears, head becomes a faded sprite — **still fully collidable** |

### Win conditions

1. Enemy HP = 0 → win
2. Score reaches 500 → instant win
3. Both reach it at once → higher score wins / equal = DRAW
4. Both run out of HP at once = DRAW

---

## 4. Balancing — edit `config.py` and nothing else

| Variable | Default | Meaning |
|---|---|---|
| `MAX_HP` | 3 | Hearts per player (the heart icon row sizes itself) |
| `TARGET_SCORE` | 500 | Score that wins instantly |
| `FRUIT_SCORE` / `FRUIT_COUNT` | 100 / 2 | Score per fruit / fruits on the field |
| `SCORE_PENALTY` | 0.5 | Score multiplier when you take a hit |
| `BASE_SPEED` / `BOOST_SPEED` | 3 / 6 | px per frame, normal / Boost |
| `SEG_SPACING` | 15 | Distance between body segments |
| `START_LENGTH` | 4 | Starting length |
| `SKILL_COST` / `SKILL_GAIN` / `SKILL_FRAMES` | 50 / 25 / 180 | Cost / gain per fruit / duration |
| `STUN_FRAMES` | 30 | Stun length in frames |
| `INVULN_FRAMES` | 60 | Immunity after taking a hit |
| `BUMP_COOLDOWN` / `SELF_HIT_COOLDOWN` | 45 / 45 | Blocks rapid repeat stuns — **must be larger than `STUN_FRAMES`** |
| `HIT_RADIUS` / `SELF_HIT_RADIUS` | 12 / 10 | Collision distance |
| `SELF_SKIP_SEGMENTS` | 3 | Segments behind the head that cannot be bitten |
| `OBSTACLE_COUNT` / `OBSTACLE_SIZE` / `OBSTACLE_SPOTS` | 6 / 60 / list | Obstacle boxes |
| `FRAME_MS` | 16 | ms per frame (16 ≈ 60 FPS) |
| `PLAYER_SETUP` | — | Player names / colors / spawn points |
| `FX_*` | — | Particle count / lifetime |
| `SOUND_ON` / `SOUND_VOLUME` | True / 0.6 | Sound |
| `USE_SPRITES` | True | `False` = force the old colored-square look |

> **Two things to watch**
> 1. `BUMP_COOLDOWN` and `SELF_HIT_COOLDOWN` **must be larger than** `STUN_FRAMES` — that gap is what guarantees a snake can drive out of whatever it is stuck on. Set them lower and the deadlock bug comes back.
> 2. `BOOST_SPEED` should not exceed about `SEG_SPACING`. Any faster and the head "jumps" over a box or an enemy body in a single frame, because collisions are checked point to point, not along the path between frames.

---

## 5. Order of work in one frame (`main.game_loop`)

```
1. tick_timers()        count down stun / immunity / cooldown / skills, then set the speed
   move()               step the head (blocked = position is not committed)
   refresh_segments()   compute the body segment positions "once" per frame, then cache them
2. resolve_fruit()      fruit pickup
   resolve_self_collision()
3. resolve_attacks(p1→p2) then resolve_attacks(p2→p1)
4. render()             draw the body, then stamp the head on top
   effects.update_and_draw()   particles
   hud.draw_panel()            stats panel
   hud.draw_stun_bars()        stun bar above the head (drawn last = top layer)
5. check_win()          if there is a winner → show_result() and stop the loop
   wn.update()          push the frame to the screen in one go
   ontimer(16 ms)       schedule the next frame
```

---

## 6. Mechanics you should be able to explain (the non-obvious parts)

1. **The body comes from path history, not a list of turtles**
   `move()` appends the head coordinate to `self.path` every frame, then `_compute_segments()` walks that history backwards **accumulating distance** and places one segment every 15 px
   *Why distance and not frames:* during Boost the snake travels 6 px/frame, so counting frames would double the gap between segments and stretch the body

2. **`refresh_segments()` is called once per frame**
   `segments()` used to be recomputed 3–4 times per frame per player (3 calls in rules + render). Now it is cached once.

3. **The head is stamped last**
   Turtle canvas items stack in creation order, so if the head were the turtle created in `__init__`, body stamps drawn later would cover it. The head turtle is hidden and kept only as the position / collision anchor, and the head image is drawn with a stamp at the end.

4. **The whole body uses a single turtle** (`clearstamps()` + `stamp()`), so a longer snake never creates more objects

5. **`path` is trimmed every frame** to keep only what is needed, otherwise the list grows forever

6. **The stats panel owns its own space.** `ARENA_T = 205` and the top wall is drawn at y=210, so snakes and fruit can never cover the numbers

7. **Cooldowns are what prevent the deadlock** (see section 9)

---

## 7. turtle & sound limitations

### turtle

| Limitation | Effect on the code |
|---|---|
| Image shapes accept **GIF** only | `sprites.py` converts PNG→GIF with Pillow |
| **Images cannot rotate** | You need 4 separate head sprites and swap `shape()` based on `facing` |
| **`shapesize()` has no effect on images** | The file's pixel size is the in-game size |
| **`color()` has no effect on images** | Effects have to swap sprites (ghost) or flicker (skip the stamp) |
| A shape's name is **the path passed to `addshape()`** | The code stores the path itself as the shape name |
| GIF transparency is **on/off only** | Slightly hard edges, that is normal |
| `Screen` is a **singleton** | Only `screen.py` calls `turtle.Screen()` |
| `tracer(0)` | You must call `wn.update()` yourself every frame |

### Sound

`sounds.py` tries backends in order and the first usable one wins:

1. **pygame.mixer** — best, sounds can overlap, volume works (needs `pip install pygame`)
2. **winsound** — Windows, ships with Python, one sound at a time
3. **command line** — `afplay` (macOS) / `paplay`, `aplay`, `ffplay` (Linux)
4. **silent** — nothing usable → `play()` does nothing and the game still plays fine

Every `play()` is wrapped in try/except — a missing sound file or a broken sound card **must never break the game**
The hint line at the bottom center of the screen shows the sound status; press `M` to toggle it. The chosen backend is printed to the terminal at startup.

---

## 8. Swapping in your team's art and sound

Drop your files into `assets/` with **the same names and the same sizes** and you never touch the code

| File | Size |
|---|---|
| `p1_head_{up,down,left,right}.gif` | 20×20 |
| `p1_head_{...}_ghost.gif` | 20×20 |
| `p1_body.gif`, `p1_body_ghost.gif` | 16×16 |
| (the same set for `p2_`) | |
| `heart_full.gif`, `heart_empty.gif` | 18×18 |
| `fruit.gif` | 16×16 |
| `sounds/{eat,hit,bump,skill,win}.wav` | — |

- You can drop in `.png` files instead (same names); the first run converts them to `.gif` (needs Pillow)
- Draw the head **facing right** as the master, then let `make_sprites.py` produce all 4 directions
- If you make the sprites bigger, adjust `SEG_SPACING` and `HIT_RADIUS` to match
- To change snake colors or shapes, edit `PALETTES` in `make_sprites.py` and rerun it
- To change sounds, edit the numbers in `make_sounds.py` and rerun it, or drop in your own `.wav` files
  Each sound is a single line: `tone(start_freq, end_freq, length_ms, wave_fn, decay, noise)`
  For example `save(tone(660, 880, 60) + tone(880, 1320, 70), 'eat')` is two rising notes in sequence
  Pick `square` (chiptune) or `saw` (brighter) for the waveform, chain notes with `+`, and add gaps with `silence(ms)`
- To add a new sound, append its name to `SOUND_NAMES` in `sounds.py` and call `sfx.play('that_name')` where you need it

---

## 9. Fixed bug — deadlock when eating your own tail / hitting a wall

**Old symptom:** eat your own tail and the player froze, unable to play at all / hit a wall and the stun looped forever

**There were 3 real root causes working together**

1. On a collision the old code set `direction = 'stop'` → the snake stood still, so the body never moved away from the head
2. The old `turn()` compared against `direction` → while `direction == 'stop'` a **180-degree turn was allowed**, which drove the head into its own neck
3. There was no cooldown → after moving 3 px the head still overlapped the same body segment, so it was stunned again immediately, forever

**The fix**

| Fix | Where |
|---|---|
| **Do not clear `direction`** on a wall / box / self collision — the snake keeps driving and gets itself out of the spot | `snake.move()`, `rules.resolve_self_collision()` |
| `turn()` compares against **`facing`** instead of `direction` → no 180-degree turn in any situation, and the escape is a left or right turn (always available) | `snake.turn()` |
| `BUMP_COOLDOWN` / `SELF_HIT_COOLDOWN` = 45 (> `STUN_FRAMES` 30) → a 15-frame window ≈ 45 px where the snake can move without being re-stunned, which **guarantees it gets out** | `config.py`, `snake.tick_timers()` |
| Holding a key against a wall no longer stuns repeatedly (the cooldown blocks it) | `snake.move()` |

Headless test result: the old code moved **0 px in 5 seconds** (genuinely frozen). The new code eats its own tail and keeps going for 360 px, escapes a wall by turning immediately, and loses no HP from self collisions.

---

## 10. Common problems

| Symptom | Cause / fix |
|---|---|
| `ModuleNotFoundError: tkinter` | Install `python3-tk` (Linux) or use Python from python.org |
| Keys do nothing | You have not clicked the game window yet |
| Snakes are colored squares, not sprites | `assets/` is not in the same folder as `main.py` → run `python make_sprites.py` |
| No sound | Check the bottom center of the screen. `SOUND: none` means the files are missing (`python make_sounds.py`) or there is no backend (`pip install pygame`) |
| Sound is delayed or drops out | Install `pygame` and it improves a lot (the `cli` backend spawns a new process every time) |
| `ImportError: cannot import name ...` | An import is in the wrong order. See the no-backward-imports rule in section 1 |
| The game stutters | Lower `FX_MAX` / `OBSTACLE_COUNT`, or raise `FRAME_MS` (16 → 20) |
| The window opens and closes instantly | Run it from a terminal to see the real error |

---

## 11. Not built yet (per the design draft)

Screen 1 (Start menu), 2 (Character select), 6 (Setting), 7 (Leaderboard)
Right now `main.py` drops straight into the match and ends at Result

To continue, add a `screens.py` (state machine: `MENU` / `SELECT` / `PLAY` / `RESULT`)
and let `main.py` switch states. The game itself needs no changes. Character select can use the existing `load_shape()` +
`PALETTES` as they are (just add a key such as `p1_green`)
