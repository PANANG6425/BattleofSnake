# HOW TO PLAY — Snake Battle

> Two-player snake on one keyboard, written in pure Python `turtle`.
> **The rules are not normal snake rules: biting punishes the BITER.**
> Read section 4 before your first match.

---

## 1. Start

```bash
python snake_battle.py
```

Needs Python 3.8+ with `tkinter` (the python.org installer for Windows and macOS already
includes it · Ubuntu: `sudo apt install python3-tk`). **Nothing else to install.**

From the menu pick **1 PLAYER** or **2 PLAYER BATTLE** → choose a character and a power → `Enter`.

---

## 2. Controls

### Character Select

| | Change character | Change power |
|---|---|---|
| P1 | `A` / `D` | `W` / `S` |
| P2 | `←` / `→` | `↑` / `↓` |

You can also click the ◀ ▶ arrows or click a power icon · `Enter` starts · `Esc` goes back.

> **Two players cannot take the same character.** The arrows skip whatever the other
> player is holding. Powers may be duplicated.

### In game

| | 1 Player | 2 Player |
|---|---|---|
| Move | `↑ ↓ ← →` | P1 `W A S D` · P2 `↑ ↓ ← →` |
| Use power | `Space` | P1 `Q` · P2 `O` |
| Sound on / off | `X` | `X` |
| Restart / next round | `R` | `R` (on the result screen) |
| Back to menu | `M` | `M` |

---

## 3. Goal

**Win a round** by either:

- dropping the other player's HP to **0** (both start with 3 hearts), or
- reaching **800 points** first (a fruit is 50 → about 16 fruit)

**Win the match** by taking **2 rounds** (best of 3).

---

## 4. The core rule — read this one to the end

Normal snake: touch anything and you die. Not here.

### 4.1 Biting someone costs the BITER

Put your head into the other snake's body or tail → **you lose 1 HP**, not them.
No points change hands, even if you are the one behind on score.

**What follows from that:** the player who is ahead wants to *dangle* their body and tail
in front of the other player's mouth, and the player who is behind has to **resist biting**
the bait.

### 4.2 Head-to-head — the LOWER score wins, and gets paid

| Situation | Result |
|---|---|
| Scores differ | The player **ahead** loses 1 HP **and hands over half of their own score** · the player behind loses nothing |
| Scores exactly level | Both lose 1 HP · no transfer |

**This is the second way to score**, next to eating fruit — if you are behind, ramming
head-first is profit.

> **Remember: this is the only place points change hands.** Every other collision costs
> HP alone.

### 4.3 Everything at once

| What you did | HP | Score |
|---|---|---|
| Head clash, you were ahead | −1 | half of it transfers to the other player |
| Head clash, you were behind | — | **you gain points** |
| Bit the other snake's body / tail | −1 | — |
| Got bitten | — | — |
| Hit your own body | −1 | — |
| Hit a wall or a box | — | — (stunned for 0.5 s) |

After losing HP you blink and are **immune for 1 second**, so nothing can chain-hit you.

---

## 5. Powers — one per player

The meter fills to 100 · **one fruit = +25** → a power roughly every 2 fruit.

| Power | What it does | Cost | Duration |
|---|---|---|---|
| **SPEED** | move twice as fast | 50 | ~3 s |
| **STEALTH** | body disappears, head goes ghost (**you still collide with everything**) | 50 | ~3 s |
| **SHIELD** | take no damage at all | 50 | ~2.5 s |
| **PHASE** | pass through boxes and your own body | 50 | ~2.5 s |
| **FEAST** | fruit is worth double | 40 | ~4 s |

> **STEALTH does not let you pass through anything** — it only hides your body. The one
> that really passes through is PHASE.
>
> A power cannot be re-triggered while it is still running.

---

## 6. Reading the screen

| What you see | Where | Meaning |
|---|---|---|
| ❤❤❤ + name + number | top left / top right | HP and score for this round |
| coloured bar | under the name | power meter (full at 100) |
| icon beside the bar | beside the bar | the power you picked — `Q` / `O` fires this |
| `P1  1 - 0  P2` | centre, gold | rounds won in this match |
| `STUN` / `BOOST` / `CLOAK` | **floating over the snake** | that snake's current state |

`STUN` = frozen for 0.5 s (from a wall, a box, or losing HP).

---

## 7. Result screens

**End of a round → `ROUND OVER`** — who took the round, the round score, what is left to
play for. `R` goes to the next round; the tally and the ledger carry over.

**End of the match → `MATCH RESULT`** — the whole match:

```
  ROUND  P1 score x hp + bonus = MVP  P2 score x hp + bonus = MVP  WON BY
  R1            400 x 3 + 300 = 1500           200 x 0 + 0 = 0      SIAM
  R2              150 x 0 + 0 = 0        480 x 2 + 200 = 1160     SAKURA
  R3              300 x 0 + 0 = 0            300 x 0 + 0 = 0        DRAW
  ----------------------------------------------------------------------
  MVP TOTAL              1500                        1160      MVP: P1
```

**MVP = (score + 100) × HP left**, added up over every round.

- **Every heart you finish a round with is worth 100 points on its own.**
- **A round you were knocked out of (HP = 0) is worth nothing**, however many points you
  banked — everything is multiplied by 0.
- **MVP does not decide the match.** Rounds won decide it. MVP is only the tie-breaker
  when the rounds are level (1–1 after three rounds, say). Level on MVP too is a drawn match.

`R` here starts a fresh match at 0–0 · `M` abandons it and goes back to the menu.

---

## 8. Tips

**If you are ahead**

- Avoid head clashes — you lose every one of them and hand over half your score.
- Park your body and tail across the other player's mouth and let them bite.
- Being ahead already walks you toward the 800-point win. Do not gamble.
- SHIELD is worth most when ahead: it blocks the HP loss **and** the score transfer.

**If you are behind**

- Ram head-first. You win the clash and get points for free.
- Do not bite their body, however tempting — you are the only one who gets hurt.
- SPEED helps you catch their head.

**General**

- You grow one segment per fruit — the longer you are, the easier it is to hit yourself
  on a tight turn.
- Walls and boxes cost no HP, only a stun — they are cover, not death.
- Dying to your own body still costs HP, and a round you are knocked out of scores 0 MVP.
- `X` toggles sound at any time.

---

## 9. Troubleshooting

| Symptom | Fix |
|---|---|
| No sound at all | Read the `SOUND:` line the game prints at startup — it says why. Usually the `.wav` files are not 16-bit PCM. |
| `ModuleNotFoundError: tkinter` | Linux: `sudo apt install python3-tk` |
| The text looks odd | The game picks a font the machine actually has; the candidate list is at the top of `snake_battle.py`. |
| Want to change difficulty / colours / speed | Section 3 of `snake_battle.py` — see `docs/MANUAL.md` section 8. |

---

*Technical detail — file map, adding sound, tuning, adding a character — is in
`docs/MANUAL.md`.*
