# CODE REVIEW — snake_battle_2P

> รีวิววันที่ 2026-09-09 · อ่านจากไฟล์จริงใน `Code/snake_battle_2P/` ทั้ง 9 ไฟล์
> ความสัมพันธ์ระหว่างไฟล์ในเอกสารนี้ **ดึงด้วย `ast` ไม่ได้พิมพ์จากความจำ**
> เลขบรรทัดจึงตรงกับโค้ดตอนรีวิว
>
> เอกสารคู่กัน: [MANUAL.md](MANUAL.md) (วิธีเล่น/วิธีแก้) · ไฟล์นี้คือ (โครงสร้าง/ผลรีวิว)

---

## สารบัญ

1. [สรุปตัวเลข](#1-สรุปตัวเลข)
2. [main.py เรียกอะไร](#2-mainpy-เรียกอะไร)
3. [ตาราง: ไฟล์ไหนเรียกไฟล์ไหน](#3-ตาราง-ไฟล์ไหนเรียกไฟล์ไหน)
4. [ตาราง: ถูกเรียกโดยใคร (ย้อนกลับ)](#4-ตาราง-ถูกเรียกโดยใคร-ย้อนกลับ)
5. [ผังชั้น import](#5-ผังชั้น-import)
6. [รายไฟล์: หน้าที่ + สิ่งที่คนอื่นใช้จริง](#6-รายไฟล์-หน้าที่--สิ่งที่คนอื่นใช้จริง)
7. [โมดูลภายนอกที่แตะ](#7-โมดูลภายนอกที่แตะ)
8. [กลไกที่พังง่ายสุด: go_to_scene](#8-กลไกที่พังง่ายสุด-go_to_scene)
9. [ผลรีวิว: แก้แล้ว](#9-ผลรีวิว-แก้แล้ว)
10. [ผลรีวิว: ยังไม่แก้](#10-ผลรีวิว-ยังไม่แก้)
11. [วิธีตรวจซ้ำ](#11-วิธีตรวจซ้ำ)

---

## 1. สรุปตัวเลข

| ไฟล์ | บรรทัด | Section (baseline kit) | บทบาท |
|---|---:|---|---|
| `main.py` | 26 | entry point | จุดเริ่ม |
| `config.py` | 197 | Section 3 | ค่าคงที่ + ทะเบียน |
| `engine.py` | 443 | Section 1 | Screen + วาด + สลับซีน |
| `entity.py` | 263 | Section 2 | คลาส Snake + power runtime |
| `audio.py` | 281 | — | เสียง |
| `screens.py` | 421 | Section 2 + 4 | เมนู + เลือกตัว + หน้าผล |
| `solo.py` | 209 | Section 2·3·4·5 | โหมด 1 คน |
| `battle.py` | 476 | Section 2·3·4·5 | โหมด 2 คน |
| `make_sprites.py` | 138 | tool (ไม่ใช่ runtime) | gen รูป |
| **รวม** | **2,454** | | ทุกไฟล์อยู่ใต้เพดาน 500 |

ไฟล์ใหญ่สุด `battle.py` = 476 เหลือที่ 24 บรรทัด ถ้าจะเพิ่มอะไรใหญ่กว่านี้
ควรย้ายบางส่วนออก (คราวก่อนย้ายหน้าผลไป `screens.py` เพราะเหตุนี้)

---

## 2. main.py เรียกอะไร

`main.py` มี **26 บรรทัด** และ `import` โมดูลในโปรเจกต์แค่ **3 ตัว** เท่านั้น:

```python
from engine import wn, go_to_scene      # L17
from audio  import sfx                  # L18
from screens import menu_scene          # L19
```

แล้วทำ 4 อย่างจบ:

```python
print(sfx.report())                             # L21  สถานะเสียง 1 บรรทัด
if sfx.backend == 'silent' or sfx._bad_wavs:    # L22  ถ้าเสียงมีปัญหา
    print(sfx.diagnose())                       # L23  พิมพ์ตารางวินิจฉัยต่อ
go_to_scene(menu_scene)                         # L25  เปิดเมนู
wn.mainloop()                                   # L26  ยกเวทีให้ tkinter
```

**ไม่มี logic ของเกมใน `main.py` เลย** — ไม่มีการคิดแต้ม ไม่มีการตรวจชน ไม่มี loop

> **ลำดับ import สำคัญ** — `engine` ต้องมาก่อน เพราะ `audio` (L24 ของมัน) และ `screens`
> (L21 ของมัน) ต้องมี `turtle.Screen()` อยู่แล้วตอนถูก import ถ้าสลับลำดับจะพัง
>
> **หลัง `wn.mainloop()` ไม่มีโค้ดของเราวิ่งเอง** ทุกเฟรมมาจาก `wn.ontimer()`
> ทุกปุ่มมาจาก `wn.onkeypress()` ทุกคลิกมาจาก `wn.onscreenclick()`

---

## 3. ตาราง: ไฟล์ไหนเรียกไฟล์ไหน

`module level` = `import` ที่หัวไฟล์ · `LOCAL` = `import` อยู่ **ข้างในฟังก์ชัน**
(เป็นวิธีเดียวที่แก้ circular import — ดูข้อ 5)

### main.py

| บรรทัด | เรียก | ระดับ | เอาอะไรไปใช้ |
|---:|---|---|---|
| L17 | `engine.py` | module level | `wn`, `go_to_scene` |
| L18 | `audio.py` | module level | `sfx` |
| L19 | `screens.py` | module level | `menu_scene` |

### config.py

**ไม่ import โมดูลในโปรเจกต์เลย และไม่ import stdlib เลยด้วย** — เป็นไฟล์ข้อมูลล้วน
จึงปลอดภัยที่จะ import จากที่ไหนก็ได้ ไม่มีโอกาสเกิดวง

### engine.py

| บรรทัด | เรียก | ระดับ | เอาอะไรไปใช้ |
|---:|---|---|---|
| L29 | `config.py` | module level | `TITLE`, `BG_COLOR`, `WIN_W`, `WIN_H`, `ASSET_DIR`, `USE_SPRITES`, `FONT_CANDIDATES`, `WINDOW_ICON`, `BAR_FRAME` (9 ชื่อ) |

### entity.py

| บรรทัด | เรียก | ระดับ | เอาอะไรไปใช้ |
|---:|---|---|---|
| L13 | `config.py` | module level | `character`, `power`, `SEG_SPACING`, `START_LENGTH`, `SKILL_MAX` |
| L14 | `engine.py` | module level | `load_shape`, `new_pen` |

### audio.py

| บรรทัด | เรียก | ระดับ | เอาอะไรไปใช้ |
|---:|---|---|---|
| L23 | `config.py` | module level | `SOUND_ON`, `SOUND_DIR`, `SOUND_VOLUME`, `EXTRA_SOUND_DIRS`, `SOUND_DEBUG` |
| L24 | `engine.py` | module level | `ASSET_DIR`, `BASE_DIR` (เอาแค่ path ไม่ได้เอาอะไรที่วาด) |

### screens.py

| บรรทัด | เรียก | ระดับ | เอาอะไรไปใช้ |
|---:|---|---|---|
| L16 | `config.py` | module level | 20 ชื่อ (ทะเบียน + สีทั้งหมด + `SURVIVE_BONUS`, `ROUNDS_TO_WIN`) |
| L21 | `engine.py` | module level | 13 ชื่อ (`wn`, `go_to_scene`, `write_at`, `draw_label`, `filled_rect`, `rounded_card`, `header_strip`, `stroke_box`, `fill_box`, `inside_rect`, `shape_turtle`, `new_pen`, `make_head_shape`) |
| L24 | `audio.py` | module level | `sfx` |
| **L105** | **`solo.py`** | **LOCAL** | `game_1p_scene` |
| **L106** | **`battle.py`** | **LOCAL** | `game_2p_scene` |

> L105-106 อยู่ข้างใน `character_select_scene()` เพราะปุ่ม Enter ต้องเปิดโหมด
> แต่ทั้ง 2 โหมดก็ import `screens` กลับมา → ต้องเป็น local ทั้งคู่

### solo.py

| บรรทัด | เรียก | ระดับ | เอาอะไรไปใช้ |
|---:|---|---|---|
| L17 | `config.py` | module level | 16 ชื่อ (`ARENA_1P`, `SPEED_1P`, `SKILL_GAIN_1P`, สี, `WALL_MARGIN`, …) |
| L21 | `engine.py` | module level | `wn`, `go_to_scene`, `new_pen`, `STATE`, `FONT`, `draw_skill_bar` |
| L22 | `audio.py` | module level | `sfx` |
| L23 | `entity.py` | module level | `Snake`, `make_fruit`, `powers_flag`, `powers_effect`, `powers_hud_tags` |
| **L49** | **`screens.py`** | **LOCAL** | `menu_scene` |

### battle.py

| บรรทัด | เรียก | ระดับ | เอาอะไรไปใช้ |
|---:|---|---|---|
| L15 | `config.py` | module level | **32 ชื่อ** — มากสุดในโปรเจกต์ (กติกาทั้งหมดอยู่ที่นี่) |
| L22 | `engine.py` | module level | `wn`, `go_to_scene`, `load_shape`, `new_pen`, `STATE`, `draw_skill_bar`, `fill_box`, `write_at`, `shape_turtle` |
| L24 | `audio.py` | module level | `sfx` |
| L25 | `entity.py` | module level | `Snake`, `make_fruit`, `powers_flag`, `powers_effect`, `powers_hud_tags` |
| **L67** | **`screens.py`** | **LOCAL** | `menu_scene`, `draw_result`, `scoreline` |

> L67 คือจุดที่โหมด 2P ส่งหน้าผลไปให้ `screens.py` วาด — `battle.py` เก็บแค่การบันทึก
> (append ledger, บวกรอบ, ตั้ง `match_over`) แล้วเรียก `draw_result()` จุดเดียว

### make_sprites.py

| บรรทัด | เรียก | ระดับ | เอาอะไรไปใช้ |
|---:|---|---|---|
| L21 | `config.py` | module level | `CHARACTERS` |

**ไม่มีไฟล์ runtime ไหน import `make_sprites`** — ตัวเกมจึงไม่พึ่ง Pillow

---

## 4. ตาราง: ถูกเรียกโดยใคร (ย้อนกลับ)

| ไฟล์ | ถูก import โดย | จำนวน |
|---|---|---:|
| `config.py` | `engine`, `entity`, `audio`, `screens`, `solo`, `battle`, `make_sprites` | **7** |
| `engine.py` | `main`, `entity`, `audio`, `screens`, `solo`, `battle` | **6** |
| `audio.py` | `main`, `screens`, `solo`, `battle` | 4 |
| `entity.py` | `solo`, `battle` | 2 |
| `screens.py` | `main`, `solo` *(local)*, `battle` *(local)* | 3 |
| `solo.py` | `screens` *(local)* | 1 |
| `battle.py` | `screens` *(local)* | 1 |
| `main.py` | **ไม่มีใคร** | 0 |
| `make_sprites.py` | **ไม่มีใคร** | 0 |

**อ่านตารางนี้ได้ 2 อย่าง:**

- `config.py` และ `engine.py` เป็น **ไฟล์ที่แก้แล้วกระเทือนที่สุด** (7 และ 6 ไฟล์)
  แก้ตรงนี้ต้องรัน regression ทั้งชุด
- `main.py` กับ `make_sprites.py` เป็น **ใบไม้** ไม่มีใครพึ่ง แก้ได้อิสระ

---

## 5. ผังชั้น import

```
                       main.py  (26)
                          │                       ← ไม่มีใคร import main
        ┌─────────────────┼──────────────────┐
        │ engine          │ audio            │ screens
        ▼                 ▼                  ▼
 ╔══════════════════════════════════════════════════════════╗
 ║  screens.py (421)     solo.py (209)     battle.py (476)  ║  ← ชั้นซีน
 ║        ▲ └── L49 local ──┘   ▲                           ║
 ║        │                     └────── L67 local ──────────╢
 ║        └── L105 / L106 local ────────────────────────────╢
 ╚══════════════════════════════════════════════════════════╝
        │                          │
        │ Snake, make_fruit        │ sfx
        ▼                          ▼
   entity.py (263)            audio.py (281)
        │                          │
        └────────────┬─────────────┘
                     ▼
               engine.py (443)     ← turtle.Screen() ตัวเดียวของทั้ง process
                     │
                     ▼
               config.py (197)     ← ไม่ import อะไรเลยแม้แต่ stdlib
```

**กฎเดียวที่ต้องรักษา: ลูกศรชี้ลงเสมอ** ไฟล์ชั้นล่างไม่รู้จักไฟล์ชั้นบน

**วงเดียวในระบบ** คือกรอบคู่ข้างบน — `screens` ↔ `solo` / `battle` เรียกกันไปกลับ
แก้ด้วย local import 4 จุด (`screens` L105, L106 · `solo` L49 · `battle` L67)

> ถ้าย้าย local import 4 จุดนั้นขึ้นไปหัวไฟล์ → `ImportError` ทันทีตอนเปิดเกม
> เพราะ Python ยัง import โมดูลนั้นไม่เสร็จ ตอนที่โมดูลนั้นสั่ง import กลับมา

---

## 6. รายไฟล์: หน้าที่ + สิ่งที่คนอื่นใช้จริง

### `main.py` — 26 บรรทัด

- **หน้าที่:** บูต 4 ขั้น (ดูข้อ 2)
- **คนอื่นใช้อะไรจากมัน:** ไม่มี
- **ห้าม:** ใส่ logic เกมลงไป — ถ้ามี `if` เกี่ยวกับกติกาที่นี่ แปลว่าวางผิดที่

### `config.py` — 197 บรรทัด · Section 3

- **หน้าที่:** ค่าคงที่ทุกตัวของเกม + THEME (สีทุกสีอยู่ที่เดียว) +
  ทะเบียน `CHARACTERS` (4 ตัว = แค่สี) และ `POWERS` (5 อย่าง เขียน effect เป็น "ชนิดของผล")
- **คนอื่นใช้อะไรจากมัน:** `battle` ใช้ 32 ชื่อ · `screens` 20 · `solo` 16 ·
  `engine` 9 · `entity` 5 · `audio` 5 · `make_sprites` 1
- **ห้าม:** `import` อะไรทั้งนั้น (ตอนนี้ 0 บรรทัด import) — เป็นสิ่งที่ทำให้มันอยู่ล่างสุดได้

### `engine.py` — 443 บรรทัด · Section 1

- **หน้าที่:** 5 ส่วน
  - `1` `turtle.Screen()` ตัวเดียว + เลือกฟอนต์ที่ติดตั้งจริง + ไอคอนหน้าต่าง
  - `1B` `load_shape()` โหลด `.gif` แบบล้มเหลวได้ไม่พัง (คืน `None`)
  - `1C` `go_to_scene()` / `unbind_all_keys()` / `clear_all_turtles()` (ดูข้อ 8)
  - `1D` helper วาดทั้งหมด — `write_at` ถูกใช้ 35 ครั้งใน `screens` และ 6 ครั้งใน `battle`
  - `1E` compound shape (หัวงูบนการ์ด + ไอคอน power 5 อัน)
- **คนอื่นใช้อะไรจากมัน:** `screens` 13 ชื่อ · `battle` 9 · `solo` 6 · `entity` 2 ·
  `audio` 2 (แค่ path) · `main` 2
- **ห้าม:** รู้จักกติกาเกม — ไฟล์นี้ไม่ควรรู้ว่า "แต้ม" คืออะไร

### `entity.py` — 263 บรรทัด · Section 2

- **หน้าที่:** คลาส `Snake` ที่ทั้ง 2 โหมดใช้ร่วมกัน + runtime ของ power
  · power state เป็น dict เดียว `{key: frames left}` เพิ่ม power ใหม่ไม่ต้องเพิ่ม attribute
  · เกมถามผลด้วย **ชนิด** (`powers_flag` / `powers_effect`) ไม่ใช่ชื่อ power
- **คนอื่นใช้อะไรจากมัน:** `solo` และ `battle` ใช้ชุดเดียวกัน 5 ชื่อ —
  `Snake`, `make_fruit`, `powers_flag`, `powers_effect`, `powers_hud_tags`
- **จุดที่ละเอียด:** `segments()` เดินย้อน `path` แล้ว**สะสมระยะทาง** ไม่ใช่นับเฟรม
  ถ้านับเฟรม ตอน SPEED ทำงานลำตัวจะยืดห่างออกจากกัน

### `audio.py` — 281 บรรทัด

- **หน้าที่:** เสียงล้วน ไม่ generate ไฟล์ ไม่ต้องลง package
  · ไล่ backend: `winsound` (stdlib) → CLI player → `pygame` (ถ้ามี) → เงียบ
  · `inspect_wav()` ใช้ module `wave` ตรวจล่วงหน้า จึงบอกได้ว่า "เจอไฟล์แต่เล่นไม่ได้"
  · `_search_order()` ค้น 4 ลำดับ (`assets/sounds/` → `sound_effect/`) `.wav` ก่อน `.mp3` เสมอ
- **คนอื่นใช้อะไรจากมัน:** ทุกคนใช้ชื่อเดียว — `sfx` (`battle` เรียก 7 ครั้ง ·
  `solo` 5 · `screens` 4 · `main` 4)
- **ห้าม:** `raise` หรือ block — ไฟล์เสียงพังต้องไม่ทำเกมตาย ทุก `play()` ครอบ try/except โดยตั้งใจ

### `screens.py` — 421 บรรทัด · Section 2 + 4

- **หน้าที่:** ทุกหน้าจอที่ **ไม่ใช่** การเล่น
  - `menu_scene()` — เมนูหลัก
  - `character_select_scene(mode)` — เลือกตัวละคร + power
  - `draw_result()` → `_draw_round()` / `_draw_match()` — หน้าผล 2 แบบ
  - logic MVP: `mvp_total()`, `match_champion()`, `scoreline()`
- **คนอื่นใช้อะไรจากมัน:** `main` ใช้ `menu_scene` · `solo` ใช้ `menu_scene` ·
  `battle` ใช้ `menu_scene`, `draw_result`, `scoreline`
- **จุดที่ละเอียด:** คลิกใช้**ตรวจพิกัด** (`inside_rect`) ไม่ใช่ `onclick()` บนเต่า
  เพราะ turtle มี 2 กับดัก — shape turtle ถูกยกทับตัวหนังสือทุกเฟรม และ
  `onclick()` **ไม่ bind อะไรเลยแบบเงียบๆ** บน compound shape ที่มี 2 ชิ้นขึ้นไป

### `solo.py` — 209 บรรทัด · Section 2·3·4·5

- **หน้าที่:** โหมด 1 คน — สนามกว้างกว่า ไม่มีศัตรู ตายแล้วจบ
  มี game loop และหน้า `GAME OVER` ของตัวเอง
- **คนอื่นใช้อะไรจากมัน:** `screens` ใช้ `game_1p_scene` (local, L105)
- **ทำไมไม่ใช้หน้าผลของ `screens.py`:** โหมดนี้ไม่มีรอบ ไม่มี MVP ไม่มีสกอร์รอบ
  เป็นความต่างที่ตั้งใจ ไม่ใช่โค้ดซ้ำที่ลืมรวม

### `battle.py` — 476 บรรทัด · Section 2·3·4·5

- **หน้าที่:** โหมด 2 คน — **กติกาทั้งหมดอยู่ไฟล์นี้**
  - `step()` — เดิน + ชนกำแพง/กล่อง (สตันเท่านั้น)
  - `punish(loser, hp=1)` — **จุดเดียวที่หัก HP** ในเกม
  - `resolve_head_clash()` — **จุดเดียวที่แต้มย้ายมือ**
  - `resolve_bite()` — กัดแล้วคนกัดเสีย HP เท่านั้น
  - `resolve_self_collision()` — ชนตัวเอง
  - `check_win()` — จบรอบเมื่อ HP = 0 หรือถึง `TARGET_SCORE`
  - `show_result()` — บันทึกรอบแล้วส่งต่อให้ `screens.draw_result()`
  - `game_loop()` — 5 ขั้นต่อเฟรม: เดิน → ผลไม้/ชนตัวเอง → ปะทะ → วาด → เช็คชนะ
- **คนอื่นใช้อะไรจากมัน:** `screens` ใช้ `game_2p_scene` (local, L106)
- **จุดที่ละเอียด:** สกอร์รอบและ ledger **ไม่ใช่ global** — ส่งผ่านพารามิเตอร์
  `wins` / `history` ของซีน กด `M` กลับเมนูจึงล้างแมตช์อัตโนมัติ

### `make_sprites.py` — 138 บรรทัด · tool

- **หน้าที่:** สร้าง `.gif` ทั้งชุดจาก `CHARACTERS` · ต้องมี Pillow **เฉพาะตอนรัน tool นี้**
- **คนอื่นใช้อะไรจากมัน:** ไม่มี
- **ผลต่อ dependency ของเกม:** ไม่มี — ตัวเกมยังอยู่ในกฎ "turtle + stdlib เท่านั้น"

---

## 7. โมดูลภายนอกที่แตะ

| ไฟล์ | stdlib | ของเสริม (optional) |
|---|---|---|
| `engine.py` | `math`, `os`, `tkinter`, `tkinter.font`, `turtle` | `PIL` — **local import ที่ L133 เท่านั้น** |
| `entity.py` | `turtle` | – |
| `audio.py` | `os`, `shutil`, `subprocess`, `wave` | `winsound` (Windows only), `pygame` — local import ทั้งคู่ |
| `solo.py` | `random` | – |
| `battle.py` | `random`, `turtle` | – |
| `make_sprites.py` | `os` | `PIL` (จำเป็นสำหรับ tool นี้) |
| `config.py`, `main.py`, `screens.py` | **ไม่มีเลย** | – |

**ตรวจแล้วว่าไม่ผิดกฎ "ไม่ใช้ pygame":**

- `PIL` ใน `engine.py` L133 อยู่ใน `try` ที่ทำงาน **เฉพาะเมื่อ**มีคนวาง `.png`
  ใน `assets/` โดยไม่มี `.gif` คู่กัน ไม่มี Pillow ก็ตกไปที่ `except` แล้วใช้สี่เหลี่ยมสีแทน
- `pygame` ใน `audio.py` เป็น backend ตัวสุดท้ายและเป็น local import
  ถ้าไม่มีก็ข้ามไปเงียบๆ **ไม่มีจุดใดในเกมที่ต้องมี pygame**

---

## 8. กลไกที่พังง่ายสุด: go_to_scene

เพราะ turtle มี `Screen` ได้ตัวเดียว การ "เปลี่ยนหน้า" จึงไม่ใช่การสร้างหน้าใหม่
แต่คือ**การรื้อของเก่าออกให้หมดก่อน** ลำดับนี้เป็นที่มาของบั๊กเก่า 3 ตัว
(เต่าค้างในสนาม · canvas item รั่ว · ปุ่มซีนเก่ายังทำงาน) จึงคุ้มที่จะจำ

| ขั้น | ทำอะไร | ถ้าข้าม |
|---:|---|---|
| 1 | `STATE['epoch'] += 1` | game loop เก่าที่ค้างใน `ontimer` จะวาดทับซีนใหม่ |
| 2 | `unbind_all_keys()` — **ทุกปุ่มใน `ALL_KEYS`** + `onscreenclick` | ปุ่มซีนเก่ายิง callback ที่ชี้ไปยังเต่าที่ตายแล้ว |
| 3 | `clear_all_turtles()` — unregister จาก `wn._turtles` **และ** ลบ `items`, `drawingLineItem`, `_fillitem`, cursor (ที่**เป็น list** เมื่อเป็น compound shape) | เต่า/canvas item รั่วขึ้นเรื่อยๆ จนเกมหนืด |
| 4 | เรียก builder ของซีนใหม่ พร้อม epoch ปัจจุบัน | – |
| 5 | ซีนใหม่ bind ปุ่มตัวเอง แล้วเริ่ม `ontimer` รอบใหม่ | – |

**วัดผลได้:** สลับ menu ↔ 2P จำนวน 25 รอบ แล้วนับ — ต้องนิ่งที่ **9 เต่า / 39 canvas item**
ถ้าเลขไต่ขึ้น แปลว่าขั้นที่ 3 พลาด (เทสต์ `_t_leak`)

---

## 9. ผลรีวิว: แก้แล้ว

ทุกข้อยืนยันด้วยการรันจริงแบบ headless แล้ว ไม่ใช่การอ่านโค้ดเดา

### 9.1 คนชนะการชนหัว ถูกคิดว่า "กัด" ในเฟรมเดียวกัน — `battle.py`

**อาการ:** ผิดกติกาที่ตั้งไว้ว่า "ฝ่ายแต้มน้อยชนะการชนและไม่เสียอะไร"

**สาเหตุ:** หลัง `resolve_head_clash()` คนแพ้ถูกสตันค้างอยู่**ตรงจุดที่ชน** หัวของคนชนะ
จึงแนบคออีกฝ่ายอยู่พอดี แล้ว `resolve_bite()` ในเฟรมเดียวกันก็หัก HP คนชนะ

**ยืนยันด้วยพิกัดจริง:** หัวห่างกัน `9.22 px` และหัวคนชนะห่างคออีกฝ่าย `7.28 px`
ขณะที่ `HIT_RADIUS = 12` → เข้าเงื่อนไขทั้ง 2 อย่างพร้อมกัน

**วิธีแก้:** เพิ่ม `bite_grace` ใน `Snake` (`entity.py`) · `resolve_head_clash()`
ตั้ง `winner.bite_grace = STUN_FRAMES` (30 เฟรม) · `resolve_bite()` return ทันทีถ้ายังมี grace
**กันแค่การกัด ไม่ได้ทำให้อมตะ** — พ้น 30 เฟรมแล้วกัดจริงยังเสีย HP ตามเดิม (เทสต์ยืนยันทั้ง 2 ทาง)

### 9.2 ผลไม้โหมด 2P เกิดบนลำตัวได้ — `battle.py` `random_free_spot()`

**อาการ:** ผลไม้เกิดบนลำตัว → คนกินเสีย HP เพราะนับเป็นชนตัวเอง

**สาเหตุ:** ฟังก์ชันเช็คกล่อง, หัวงู (`SPAWN_CLEAR`) และผลไม้ลูกอื่น แต่**ไม่เคยเช็คลำตัว**
ขณะที่ `solo.py` เช็คมาตั้งแต่ต้น (เคยเป็นบั๊กที่นั่นแล้วแก้ไป แต่ไม่ได้ยกมา 2P)

**วิธีแก้:** เพิ่ม `BODY_CLEAR = 24` และเช็ค `pl.segments()` ของทั้ง 2 ตัว
**วัดผล:** สุ่ม 400 จุดกับงูยาว 40 ท่อน 2 ตัว → จุดที่ใกล้ลำตัวสุด = `24.0 px` พอดีตามเกณฑ์

### 9.3 `SELF_HIT_DAMAGE` ถูกอ่านเป็น boolean — `battle.py`

**อาการ:** `config.py` เขียนว่า "HP ที่เสียตอนชนตัวเอง" แต่โค้ดทำ `if SELF_HIT_DAMAGE:`
แล้วหัก 1 ตายตัว → ตั้งเป็น `2` ก็ยังเสีย 1 อย่างเงียบๆ

**วิธีแก้:** `punish(loser, hp=1)` รับจำนวนเป็นพารามิเตอร์ และเรียก
`punish(snake, SELF_HIT_DAMAGE)` ตอนชนตัวเอง

### 9.4 เพิ่ม power ใหม่แล้ว Character Select พังทั้งหน้า — `engine.py` `shape_turtle()`

**อาการ:** `config.py` สัญญาว่าเพิ่ม power เป็น "data only" แต่ถ้ายังไม่ได้วาดไอคอน
`t.shape(name)` จะ raise `TurtleGraphicsError` กลางการสร้างหน้า เหลือจอวาดครึ่งเดียวที่กดอะไรไม่ได้

**วิธีแก้:** ครอบ try/except แล้ว fallback เป็นสี่เหลี่ยมเทา ให้พฤติกรรมตรงกับ
`load_shape()` ที่คืน `None` เมื่อหาไฟล์ไม่เจอ

---

## 10. ผลรีวิว: ยังไม่แก้

4 ข้อนี้เป็นของจริง แต่ยังไม่แก้เพราะเข้าถึงยากหรือรอการตัดสินใจ

### 10.1 กด 2 ปุ่มในเฟรมเดียวกัน กลับหลังหันได้ — `entity.py` `turn()`

ตัวกันการกลับหลังหันเทียบกับ `self.direction` ซึ่งปุ่มก่อนหน้าใน**เฟรมเดียวกัน**
เพิ่งเปลี่ยนไปแล้ว จาก `up` กด `Left` แล้ว `Down` ทันทีจะได้ `down` ทั้งที่หัวยังไม่ขยับ
= ถอยทับรอยตัวเอง และไม่โดนโทษ เพราะทั้ง 2 โหมดข้าม `segments()[:2]`

**ทำไมยังไม่แก้:** ต้องกดภายใน 16 ms และการแก้ต้องแยก "ทิศที่กด" ออกจาก
"ทิศที่ commit แล้ว" — เป็นการเปลี่ยน state ของ `Snake` บอกได้ถ้าอยากปิดช่องนี้

### 10.2 ถ้าเหลือตัวละคร 2 ตัว ลูกศรเลือกตัวจะกดไม่ติด — `screens.py` `step_char()`

ลูปข้ามตัวที่อีกฝ่ายถืออยู่ อาจวนกลับมาที่ตัวเดิมแล้วนับว่าเลือกสำเร็จ (มีเสียง มีการวาดใหม่
แต่ไม่เปลี่ยนอะไร) · **ตอนนี้มี 4 ตัวจึงไม่เกิด** เกิดเฉพาะถ้าลด `CHARACTERS` เหลือ 2

### 10.3 `CHAR_DEFAULTS` / `POWER_DEFAULTS` ไม่ถูกตรวจกับทะเบียน — `screens.py` L117-121

ถ้าแก้ทะเบียนแล้ว key ใน defaults ไม่มีอยู่จริง จะได้ 2 อาการ:
กดลูกศรได้ `ValueError` เงียบๆ ใน callback ของ tkinter (traceback ไปที่ stderr ปุ่มตายเฉยๆ)
และกด Enter แล้วผู้เล่นทั้งสองได้ตัวละคร**เดียวกัน** ซึ่งเป็นสิ่งที่คอมเมนต์ตรงนั้นบอกว่ากันอยู่
· เป็นเคสตอนแก้ config ผิด ไม่ใช่ตอนเล่น

### 10.4 โค้ดตาย 4 จุด

| ที่ | อะไร |
|---|---|
| `engine.py` | `WINDOW_ICON_USED` ถูกเซ็ตแต่ไม่มีใครอ่าน |
| `audio.py` | event `score` ใน `SOUND_EVENTS` ไม่เคยถูกเล่น (มีแต่ในตาราง `diagnose()`) |
| `battle.py` | `build_obstacles()` มี `clear()` สำหรับการเรียกซ้ำที่ไม่เคยเกิด (เรียกครั้งเดียว) |
| `make_sprites.py` | เขียนไฟล์ `<key>_body_ghost.gif` ที่ไม่มีใครโหลด — ตอน cloak ลำตัวถูกซ่อนทั้งหมด |

ทั้งหมดไม่มีผลต่อการทำงาน ปล่อยไว้ได้

---

## 11. วิธีตรวจซ้ำ

รันแบบ headless (Xvfb) แล้ววัดค่า ไม่ใช่อ่านโค้ดเดา

| เทสต์ | ตรวจอะไร | ผลล่าสุด |
|---|---|---|
| `_econ` | เศรษฐกิจแต้ม: กัด 2 ทาง, ชนหัว 3 แบบ, ชนตัวเอง, SHIELD, ล็อกการชน | 0 fail |
| `_fixes` | บั๊ก 9.1-9.3 สร้างสถานการณ์ด้วยพิกัดจริง | 0 fail |
| `_mvp` | สูตร MVP, ลำดับตัดสิน 3 ชั้น, เสมอทุกรอบยังจบ | 0 fail |
| `_match` | เล่น 3 รอบผ่าน `R` จริง แล้วอ่านตารางจาก canvas | 0 fail |
| `_hud` | ไอคอนข้างหลอด, STUN บนตัวงู, โบนัส survive บนจอ | 0 fail |
| `_tagpos` | ป้าย STUN ที่มุมสนาม 8 จุด ไม่ล้นขอบ ไม่ชนแถบ HUD | 0 violation |
| `_stress` | เล่นสุ่ม 5 รอบผ่าน pipeline จริง ตรวจ invariant ทุกเฟรม | 0 violation |
| `_t_sweep` | บูตทุกซีน ยิงทุกปุ่มที่ bind ไว้ | 0 error |
| `_t_leak` | สลับ menu ↔ 2P 25 รอบ นับเต่ากับ canvas item | นิ่ง 9 / 39 |
| `ruff --select F,B` | static analysis (`F` = ผิดจริง, `B` = bug-prone) | ผ่านหมด |

**เช็คเร็วสุดโดยไม่ต้องมีจอ:**

```bash
python -m py_compile *.py                          # syntax
ruff check --select F,B *.py                       # ผิดจริง + bug-prone
python -c "import ast;[ast.parse(open(f).read()) for f in __import__('glob').glob('*.py')]"
```

**ตรวจว่าไฟล์ยังอยู่ใต้ 500 บรรทัด:**

```bash
wc -l *.py | sort -n
```

---

## ภาคผนวก: ค่าที่ตั้งอยู่ตอนรีวิว

```python
FRUIT_SCORE     = 50      # แต้มต่อผลไม้ 1 ลูก
TARGET_SCORE    = 800     # ถึงแล้วชนะรอบทันที
MAX_HP          = 3
ROUNDS_TO_WIN   = 2       # แข่ง 3 เอา 2
MAX_ROUNDS      = 3       # = ROUNDS_TO_WIN * 2 - 1 (คำนวณเอง)
SURVIVE_BONUS   = 100     # HP ที่เหลือดวงละ 100 ตอนคิด MVP
SCORE_TRANSFER  = 0.5     # แต้มที่โอนตอนหัวชนหัว (ที่เดียวที่แต้มย้ายมือ)
SELF_HIT_DAMAGE = 1
STUN_FRAMES     = 30
INVULN_FRAMES   = 60
HIT_RADIUS      = 12
```

รายละเอียดของแต่ละค่าและวิธีปรับ อยู่ใน [MANUAL.md](MANUAL.md) ข้อ 8
