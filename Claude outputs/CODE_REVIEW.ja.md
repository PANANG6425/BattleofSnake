# CODE REVIEW — snake_battle_2P

> 言語: [ไทย](CODE_REVIEW.md) · **日本語**
>
> レビュー日 2026-09-09 · `Code/snake_battle_2P/` の 9 ファイルすべてを実物から読んでいます。
> 本書のファイル間の依存関係は **`ast` で抽出したもので、記憶で書いたものではありません。**
> したがって行番号はレビュー時点のコードと一致します。
>
> 対になるドキュメント: [MANUAL.ja.md](MANUAL.ja.md)（遊び方・変更方法）· 本書は（構造・レビュー結果）

---

## 目次

1. [数字のまとめ](#1-数字のまとめ)
2. [main.py は何を呼ぶか](#2-mainpy-は何を呼ぶか)
3. [表: どのファイルがどのファイルを呼ぶか](#3-表-どのファイルがどのファイルを呼ぶか)
4. [表: 誰から呼ばれているか（逆引き）](#4-表-誰から呼ばれているか逆引き)
5. [import の階層図](#5-import-の階層図)
6. [ファイル別: 役割と他ファイルが実際に使うもの](#6-ファイル別-役割と他ファイルが実際に使うもの)
7. [外部モジュールへの依存](#7-外部モジュールへの依存)
8. [最も壊れやすい仕組み: go_to_scene](#8-最も壊れやすい仕組み-go_to_scene)
9. [レビュー結果: 修正済み](#9-レビュー結果-修正済み)
10. [レビュー結果: 未修正](#10-レビュー結果-未修正)
11. [再検証の手順](#11-再検証の手順)

---

## 1. 数字のまとめ

| ファイル | 行数 | Section（baseline kit） | 役割 |
|---|---:|---|---|
| `main.py` | 26 | entry point | 起動点 |
| `config.py` | 197 | Section 3 | 定数 + レジストリ |
| `engine.py` | 443 | Section 1 | Screen + 描画 + シーン切替 |
| `entity.py` | 263 | Section 2 | Snake クラス + パワー実行部 |
| `audio.py` | 281 | — | サウンド |
| `screens.py` | 421 | Section 2 + 4 | メニュー + キャラセレ + リザルト |
| `solo.py` | 209 | Section 2·3·4·5 | 1 人プレイ |
| `battle.py` | 476 | Section 2·3·4·5 | 2 人対戦 |
| `make_sprites.py` | 138 | tool（実行時には不要） | スプライト生成 |
| **合計** | **2,454** | | 全ファイルが上限 500 行以内 |

最大は `battle.py` の 476 行で、残りは 24 行しかありません。これより大きなものを
追加するなら一部を切り出すべきです（前回はまさにこの理由でリザルト画面を
`screens.py` へ移しました）。

---

## 2. main.py は何を呼ぶか

`main.py` は **26 行**しかなく、プロジェクト内モジュールの `import` は **3 つだけ**です:

```python
from engine import wn, go_to_scene      # L17
from audio  import sfx                  # L18
from screens import menu_scene          # L19
```

そして 4 つのことをして終わります:

```python
print(sfx.report())                             # L21  サウンド状態を 1 行
if sfx.backend == 'silent' or sfx._bad_wavs:    # L22  問題があるときだけ
    print(sfx.diagnose())                       # L23  診断表を続けて出す
go_to_scene(menu_scene)                         # L25  メニューを開く
wn.mainloop()                                   # L26  制御を tkinter へ渡す
```

**`main.py` にゲームロジックは一切ありません** — スコア計算も当たり判定もループもなし。

> **import の順序が重要** — `engine` が先でなければなりません。`audio`（その L24）と
> `screens`（その L21）は import される時点で `turtle.Screen()` が存在している必要が
> あります。順序を入れ替えると壊れます。
>
> **`wn.mainloop()` の後に自走するコードはありません。** すべてのフレームは
> `wn.ontimer()` から、すべてのキーは `wn.onkeypress()` から、すべてのクリックは
> `wn.onscreenclick()` から来ます。

---

## 3. 表: どのファイルがどのファイルを呼ぶか

`module level` = ファイル先頭の `import` · `LOCAL` = **関数の内側**にある `import`
（循環 import を解消する唯一の方法 — 第 5 章参照）

### main.py

| 行 | 呼ぶ先 | レベル | 使っている名前 |
|---:|---|---|---|
| L17 | `engine.py` | module level | `wn`, `go_to_scene` |
| L18 | `audio.py` | module level | `sfx` |
| L19 | `screens.py` | module level | `menu_scene` |

### config.py

**プロジェクト内モジュールも標準ライブラリも、一切 import しません** — 純粋なデータ
ファイルです。だからどこから import しても安全で、循環が生じる余地がありません。

### engine.py

| 行 | 呼ぶ先 | レベル | 使っている名前 |
|---:|---|---|---|
| L29 | `config.py` | module level | `TITLE`, `BG_COLOR`, `WIN_W`, `WIN_H`, `ASSET_DIR`, `USE_SPRITES`, `FONT_CANDIDATES`, `WINDOW_ICON`, `BAR_FRAME`（9 個） |

### entity.py

| 行 | 呼ぶ先 | レベル | 使っている名前 |
|---:|---|---|---|
| L13 | `config.py` | module level | `character`, `power`, `SEG_SPACING`, `START_LENGTH`, `SKILL_MAX` |
| L14 | `engine.py` | module level | `load_shape`, `new_pen` |

### audio.py

| 行 | 呼ぶ先 | レベル | 使っている名前 |
|---:|---|---|---|
| L23 | `config.py` | module level | `SOUND_ON`, `SOUND_DIR`, `SOUND_VOLUME`, `EXTRA_SOUND_DIRS`, `SOUND_DEBUG` |
| L24 | `engine.py` | module level | `ASSET_DIR`, `BASE_DIR`（パスだけ。描画系は一切取っていません） |

### screens.py

| 行 | 呼ぶ先 | レベル | 使っている名前 |
|---:|---|---|---|
| L16 | `config.py` | module level | 20 個（レジストリ + 全色 + `SURVIVE_BONUS`, `ROUNDS_TO_WIN`） |
| L21 | `engine.py` | module level | 13 個（`wn`, `go_to_scene`, `write_at`, `draw_label`, `filled_rect`, `rounded_card`, `header_strip`, `stroke_box`, `fill_box`, `inside_rect`, `shape_turtle`, `new_pen`, `make_head_shape`） |
| L24 | `audio.py` | module level | `sfx` |
| **L105** | **`solo.py`** | **LOCAL** | `game_1p_scene` |
| **L106** | **`battle.py`** | **LOCAL** | `game_2p_scene` |

> L105-106 は `character_select_scene()` の内側にあります。Enter キーでモードを
> 開く必要がある一方、両モードも `screens` を import して戻ってくるため、
> どちらも LOCAL でなければなりません。

### solo.py

| 行 | 呼ぶ先 | レベル | 使っている名前 |
|---:|---|---|---|
| L17 | `config.py` | module level | 16 個（`ARENA_1P`, `SPEED_1P`, `SKILL_GAIN_1P`, 色, `WALL_MARGIN`, …） |
| L21 | `engine.py` | module level | `wn`, `go_to_scene`, `new_pen`, `STATE`, `FONT`, `draw_skill_bar` |
| L22 | `audio.py` | module level | `sfx` |
| L23 | `entity.py` | module level | `Snake`, `make_fruit`, `powers_flag`, `powers_effect`, `powers_hud_tags` |
| **L49** | **`screens.py`** | **LOCAL** | `menu_scene` |

### battle.py

| 行 | 呼ぶ先 | レベル | 使っている名前 |
|---:|---|---|---|
| L15 | `config.py` | module level | **32 個** — プロジェクト最多（ルールがすべてここにあるため） |
| L22 | `engine.py` | module level | `wn`, `go_to_scene`, `load_shape`, `new_pen`, `STATE`, `draw_skill_bar`, `fill_box`, `write_at`, `shape_turtle` |
| L24 | `audio.py` | module level | `sfx` |
| L25 | `entity.py` | module level | `Snake`, `make_fruit`, `powers_flag`, `powers_effect`, `powers_hud_tags` |
| **L67** | **`screens.py`** | **LOCAL** | `menu_scene`, `draw_result`, `scoreline` |

> L67 が、2P モードがリザルト画面の描画を `screens.py` に委譲している箇所です。
> `battle.py` は記録だけを持ちます（ledger に append、ラウンド加算、`match_over` の設定）。
> そして `draw_result()` を 1 か所だけ呼びます。

### make_sprites.py

| 行 | 呼ぶ先 | レベル | 使っている名前 |
|---:|---|---|---|
| L21 | `config.py` | module level | `CHARACTERS` |

**実行時のどのファイルも `make_sprites` を import していません** — ゲーム本体は
Pillow に依存しません。

---

## 4. 表: 誰から呼ばれているか（逆引き）

| ファイル | import している側 | 数 |
|---|---|---:|
| `config.py` | `engine`, `entity`, `audio`, `screens`, `solo`, `battle`, `make_sprites` | **7** |
| `engine.py` | `main`, `entity`, `audio`, `screens`, `solo`, `battle` | **6** |
| `audio.py` | `main`, `screens`, `solo`, `battle` | 4 |
| `entity.py` | `solo`, `battle` | 2 |
| `screens.py` | `main`, `solo` *(local)*, `battle` *(local)* | 3 |
| `solo.py` | `screens` *(local)* | 1 |
| `battle.py` | `screens` *(local)* | 1 |
| `main.py` | **なし** | 0 |
| `make_sprites.py` | **なし** | 0 |

**この表から 2 つ読み取れます:**

- `config.py` と `engine.py` は **変更の影響が最も大きいファイル**（7 と 6）。
  ここを触ったら regression を全部走らせる必要があります。
- `main.py` と `make_sprites.py` は **葉**です。誰も依存していないので自由に変更できます。

---

## 5. import の階層図

```
                       main.py  (26)
                          │                       ← main を import する者はいない
        ┌─────────────────┼──────────────────┐
        │ engine          │ audio            │ screens
        ▼                 ▼                  ▼
 ╔══════════════════════════════════════════════════════════╗
 ║  screens.py (421)     solo.py (209)     battle.py (476)  ║  ← シーン層
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
               engine.py (443)     ← プロセスに 1 つだけの turtle.Screen()
                     │
                     ▼
               config.py (197)     ← 標準ライブラリすら import しない
```

**守るべき唯一のルール: 矢印は常に下向き。** 下の層は上の層を知りません。

**システム内の循環は 1 か所だけ** — 上の二重枠、`screens` ↔ `solo` / `battle` が
互いを呼び合います。local import 4 か所で解消しています
（`screens` L105, L106 · `solo` L49 · `battle` L67）。

> この 4 か所をファイル先頭に移すと、ゲーム起動時に即 `ImportError` になります。
> 呼び戻された時点で、Python 側はそのモジュールの import をまだ終えていないからです。

---

## 6. ファイル別: 役割と他ファイルが実際に使うもの

### `main.py` — 26 行

- **役割:** 4 段階の起動（第 2 章参照）
- **他ファイルが使うもの:** なし
- **やってはいけないこと:** ゲームロジックを入れること。ルールに関する `if` が
  ここにあるなら、置き場所を間違えています。

### `config.py` — 197 行 · Section 3

- **役割:** ゲームの全定数 + THEME（すべての色を 1 か所に）+
  レジストリ `CHARACTERS`（4 体 = 色だけ）と `POWERS`（5 種類、effect を
  「効果の種類」として記述）
- **他ファイルが使うもの:** `battle` が 32 個 · `screens` 20 · `solo` 16 ·
  `engine` 9 · `entity` 5 · `audio` 5 · `make_sprites` 1
- **やってはいけないこと:** 何かを `import` すること（現在 import 行は 0）。
  これが最下層に置ける理由そのものです。

### `engine.py` — 443 行 · Section 1

- **役割:** 5 パート
  - `1` 唯一の `turtle.Screen()` + 実際にインストール済みのフォント選択 + ウィンドウアイコン
  - `1B` `load_shape()` — `.gif` の読み込みが失敗しても壊れない（`None` を返す）
  - `1C` `go_to_scene()` / `unbind_all_keys()` / `clear_all_turtles()`（第 8 章）
  - `1D` 描画補助のすべて — `write_at` は `screens` で 35 回、`battle` で 6 回使用
  - `1E` compound shape（カード上の蛇の頭 + パワーアイコン 5 個）
- **他ファイルが使うもの:** `screens` 13 個 · `battle` 9 · `solo` 6 · `entity` 2 ·
  `audio` 2（パスのみ）· `main` 2
- **やってはいけないこと:** ゲームのルールを知ること。このファイルは
  「スコア」が何かを知るべきではありません。

### `entity.py` — 263 行 · Section 2

- **役割:** 両モードが共有する `Snake` クラス + パワーの実行部
  · パワーの状態は `{key: 残りフレーム}` という 1 つの dict。新しいパワーを
  追加しても属性を増やす必要がありません
  · ゲームは効果を**種類**で問い合わせます（`powers_flag` / `powers_effect`）。
  パワー名では問い合わせません
- **他ファイルが使うもの:** `solo` と `battle` が同じ 5 個を使用 —
  `Snake`, `make_fruit`, `powers_flag`, `powers_effect`, `powers_hud_tags`
- **細かいが重要な点:** `segments()` は `path` を逆にたどって**距離を累積**します。
  フレーム数を数える実装にすると、SPEED 発動中に胴体が伸びて間隔が開きます。

### `audio.py` — 281 行

- **役割:** サウンド専用。ファイルを生成せず、パッケージも不要
  · backend を順に試す: `winsound`（標準）→ CLI プレイヤー → `pygame`（あれば）→ 無音
  · `inspect_wav()` が `wave` モジュールで事前チェックするので
  「ファイルは見つかるが再生できない」を言い当てられます
  · `_search_order()` が 4 段階で探索（`assets/sounds/` → `sound_effect/`）。
  どのフォルダでも `.wav` が `.mp3` より先
- **他ファイルが使うもの:** 全員が同じ 1 つの名前 — `sfx`
  （`battle` 7 回 · `solo` 5 · `screens` 4 · `main` 4）
- **やってはいけないこと:** `raise` と block。音声ファイルが壊れていても
  ゲームを落としてはいけないので、`play()` は意図的に try/except で囲んでいます。

### `screens.py` — 421 行 · Section 2 + 4

- **役割:** プレイ**以外**のすべての画面
  - `menu_scene()` — メインメニュー
  - `character_select_scene(mode)` — キャラクターとパワーの選択
  - `draw_result()` → `_draw_round()` / `_draw_match()` — リザルト 2 種類
  - MVP のロジック: `mvp_total()`, `match_champion()`, `scoreline()`
- **他ファイルが使うもの:** `main` は `menu_scene` · `solo` は `menu_scene` ·
  `battle` は `menu_scene`, `draw_result`, `scoreline`
- **細かいが重要な点:** クリックは**座標判定**（`inside_rect`）で、亀の
  `onclick()` は使いません。turtle には罠が 2 つあるからです —
  shape turtle は毎フレーム文字より上に持ち上げられる、そして
  `onclick()` は 2 部品以上の compound shape では**何も bind せずに黙って通る**。

### `solo.py` — 209 行 · Section 2·3·4·5

- **役割:** 1 人プレイ — アリーナが広く、敵がおらず、死んだら終わり。
  独自の game loop と独自の `GAME OVER` 画面を持ちます
- **他ファイルが使うもの:** `screens` が `game_1p_scene`（local, L105）
- **なぜ `screens.py` のリザルトを使わないのか:** このモードにはラウンドも MVP も
  ラウンドスコアもありません。意図した差であって、まとめ忘れた重複ではありません。

### `battle.py` — 476 行 · Section 2·3·4·5

- **役割:** 2 人対戦 — **ルールのすべてがこのファイル**にあります
  - `step()` — 移動 + 壁/障害物への衝突（スタンのみ）
  - `punish(loser, hp=1)` — ゲーム内で **HP を減らす唯一の場所**
  - `resolve_head_clash()` — **スコアが移動する唯一の場所**
  - `resolve_bite()` — 噛みついた側だけが HP を失う
  - `resolve_self_collision()` — 自分の胴体
  - `check_win()` — HP 0 または `TARGET_SCORE` 到達でラウンド終了
  - `show_result()` — ラウンドを記録して `screens.draw_result()` へ委譲
  - `game_loop()` — 1 フレーム 5 段階: 移動 → フルーツ/自傷 → 接触 → 描画 → 勝敗判定
- **他ファイルが使うもの:** `screens` が `game_2p_scene`（local, L106）
- **細かいが重要な点:** ラウンドスコアと ledger は **global ではありません**。
  シーンの引数 `wins` / `history` で渡されるため、`M` でメニューに戻ると
  マッチが自動的にクリアされます。

### `make_sprites.py` — 138 行 · tool

- **役割:** `CHARACTERS` から `.gif` を一括生成 · Pillow は**このツールを実行する時だけ**必要
- **他ファイルが使うもの:** なし
- **ゲームの依存関係への影響:** なし — 本体は「turtle + 標準ライブラリのみ」を維持

---

## 7. 外部モジュールへの依存

| ファイル | 標準ライブラリ | 任意（optional） |
|---|---|---|
| `engine.py` | `math`, `os`, `tkinter`, `tkinter.font`, `turtle` | `PIL` — **L133 の local import だけ** |
| `entity.py` | `turtle` | – |
| `audio.py` | `os`, `shutil`, `subprocess`, `wave` | `winsound`（Windows のみ）, `pygame` — どちらも local import |
| `solo.py` | `random` | – |
| `battle.py` | `random`, `turtle` | – |
| `make_sprites.py` | `os` | `PIL`（このツールには必須） |
| `config.py`, `main.py`, `screens.py` | **なし** | – |

**「pygame を使わない」というルールに違反していないことを確認しました:**

- `engine.py` L133 の `PIL` は、`assets/` に `.gif` の対応がない `.png` を
  置いた場合**のみ**走る `try` の中にあります。Pillow が無ければ `except` に落ちて
  色付きの四角にフォールバックします。
- `audio.py` の `pygame` は最後の backend で、かつ local import です。
  無ければ黙ってスキップします。**pygame が必須になる箇所はゲーム内に一切ありません。**

---

## 8. 最も壊れやすい仕組み: go_to_scene

turtle は `Screen` を 1 つしか持てないため、「画面を変える」は新しい画面を作ることでは
なく、**古いものを完全に取り壊すこと**です。この順序は過去のバグ 3 件
（アリーナに亀が残る · canvas item のリーク · 前のシーンのキーがまだ効く）の
原因そのものなので、覚えておく価値があります。

| 段階 | すること | 飛ばすとどうなるか |
|---:|---|---|
| 1 | `STATE['epoch'] += 1` | `ontimer` に残っていた古い game loop が新しいシーンに上書き描画する |
| 2 | `unbind_all_keys()` — **`ALL_KEYS` の全キー** + `onscreenclick` | 前のシーンのキーが、すでに消えた亀を指す callback を発火する |
| 3 | `clear_all_turtles()` — `wn._turtles` から unregister **かつ** `items`, `drawingLineItem`, `_fillitem`, cursor（compound shape のときは**リスト**）を削除 | 亀と canvas item が増え続けてゲームが重くなる |
| 4 | 現在の epoch を渡して新しいシーンの builder を呼ぶ | – |
| 5 | 新しいシーンが自分のキーを bind し、`ontimer` を開始 | – |

**測定できます:** menu ↔ 2P を 25 回切り替えて数える — **亀 9 / canvas item 39** で
一定であるべきです。数字が増えていくなら段階 3 が漏れています（テスト `_t_leak`）。

---

## 9. レビュー結果: 修正済み

すべて headless で実際に実行して確認済みです。コードを読んだ推測ではありません。

### 9.1 頭同士の衝突に勝った側が、同じフレームで「噛みつき」扱いされる — `battle.py`

**症状:** 「スコアの低い側が衝突に勝ち、何も失わない」というルールに反する。

**原因:** `resolve_head_clash()` の後、負けた側は**衝突した位置で**スタンして
止まります。そのため勝った側の頭は相手の首に触れたままになり、同じフレームの
`resolve_bite()` が勝った側の HP を削っていました。

**実座標で確認:** 頭同士の距離 `9.22 px`、勝った側の頭と相手の首の距離 `7.28 px`、
対して `HIT_RADIUS = 12` → 両方の条件を同時に満たしていました。

**修正:** `Snake`（`entity.py`）に `bite_grace` を追加 · `resolve_head_clash()` が
`winner.bite_grace = STUN_FRAMES`（30 フレーム）を設定 · `resolve_bite()` は
grace が残っていれば即 return。**噛みつきだけを抑えるもので、無敵ではありません** —
30 フレーム後に実際に噛めば従来どおり HP が減ります（テストで両方向を確認）。

### 9.2 2P モードでフルーツが胴体の上に出現する — `battle.py` `random_free_spot()`

**症状:** 胴体の上にフルーツが出現 → 取った側が自己衝突扱いで HP を失う。

**原因:** この関数は障害物・蛇の頭（`SPAWN_CLEAR`）・他のフルーツを見ていましたが、
**胴体を一度も見ていませんでした**。`solo.py` は最初からこれを見ています
（あちらで一度バグになって修正済みでしたが、2P に持ってきていませんでした）。

**修正:** `BODY_CLEAR = 24` を追加し、両方の `pl.segments()` をチェック。
**測定:** 40 節の蛇 2 匹で 400 か所を抽選 → 胴体に最も近い点が `24.0 px` で基準どおり。

### 9.3 `SELF_HIT_DAMAGE` が boolean として読まれていた — `battle.py`

**症状:** `config.py` は「自分の胴体に当たったときに減る HP」と書いていますが、
コードは `if SELF_HIT_DAMAGE:` として常に 1 だけ減らしていました →
`2` に設定しても黙って 1 しか減りません。

**修正:** `punish(loser, hp=1)` が量を引数で受け取るようにし、自傷時は
`punish(snake, SELF_HIT_DAMAGE)` を呼びます。

### 9.4 パワーを追加するとキャラクターセレクトが画面ごと壊れる — `engine.py` `shape_turtle()`

**症状:** `config.py` はパワー追加を「data only」と約束していますが、アイコンを
まだ描いていない場合 `t.shape(name)` が画面構築の途中で `TurtleGraphicsError` を
投げ、半分だけ描かれて何も押せない画面が残ります。

**修正:** try/except で囲み、灰色の四角にフォールバック。ファイルが見つからないとき
`None` を返す `load_shape()` と挙動を揃えました。

---

## 10. レビュー結果: 未修正

以下 4 件は実在しますが、到達が難しいか、判断待ちのため未修正です。

### 10.1 同一フレームで 2 キー押すと 180 度反転できる — `entity.py` `turn()`

反転防止は `self.direction` と比較しますが、それは**同じフレーム内の**先の
キー入力がすでに書き換えています。`up` から `Left` → 直後に `Down` を押すと
頭が動いていないのに `down` になり、自分の軌跡を逆走します。しかも両モードが
`segments()[:2]` を除外しているため罰もありません。

**未修正の理由:** 16 ms 以内に押す必要があり、修正には「押された方向」と
「commit された方向」を分離する必要があります — `Snake` の状態の変更になります。
この穴を閉じたい場合は言ってください。

### 10.2 キャラクターが 2 体だと選択矢印が効かなくなる — `screens.py` `step_char()`

相手が持っているキャラクターを飛ばすループが、元のインデックスに戻ってきて
「選択成功」と扱う場合があります（効果音も再描画も走るのに何も変わらない）。
· **現在は 4 体なので発生しません。** `CHARACTERS` を 2 体に減らした場合のみ。

### 10.3 `CHAR_DEFAULTS` / `POWER_DEFAULTS` がレジストリと照合されない — `screens.py` L117-121

レジストリを変更して defaults のキーが実在しなくなると 2 つの症状が出ます:
矢印を押すと tkinter の callback 内で `ValueError` が静かに出る（traceback は
stderr へ行き、キーは無反応になる）。そして Enter を押すと両プレイヤーが
**同じキャラクター**になります — その箇所のコメントが防いでいると書いていることが
起きます。· config を間違えて編集したときのケースで、プレイ中には起きません。

### 10.4 デッドコード 4 か所

| 場所 | 内容 |
|---|---|
| `engine.py` | `WINDOW_ICON_USED` は設定されるが誰も読まない |
| `audio.py` | `SOUND_EVENTS` の `score` イベントは一度も再生されない（`diagnose()` の表にだけ出る） |
| `battle.py` | `build_obstacles()` に、起きない再呼び出しのための `clear()` がある（呼び出しは 1 回だけ） |
| `make_sprites.py` | 誰も読み込まない `<key>_body_ghost.gif` を書き出す — cloak 中は胴体を完全に隠すため |

いずれも動作に影響しないので、そのままでも問題ありません。

---

## 11. 再検証の手順

headless（Xvfb）で実行して値を測ります。コードを読んだ推測ではありません。

| テスト | 何を見るか | 直近の結果 |
|---|---|---|
| `_econ` | スコアの経済: 噛みつき両方向・頭衝突 3 パターン・自傷・SHIELD・衝突ロック | 0 fail |
| `_fixes` | 9.1-9.3 のバグを実座標で再現 | 0 fail |
| `_mvp` | MVP の式・3 段階の決着順・全ラウンド引き分けでも終わるか | 0 fail |
| `_match` | 実際に `R` で 3 ラウンド進め、canvas から表を読む | 0 fail |
| `_hud` | ゲージ横のアイコン・蛇の上の STUN・画面上の survive ボーナス | 0 fail |
| `_tagpos` | アリーナ 8 隅での STUN ラベル。枠外に出ず HUD 帯と重ならないか | 0 violation |
| `_stress` | 実 pipeline でランダムに 5 ラウンド、毎フレーム invariant を検査 | 0 violation |
| `_t_sweep` | 全シーンを起動し、bind された全キーを叩く | 0 error |
| `_t_leak` | menu ↔ 2P を 25 回切り替え、亀と canvas item を数える | 9 / 39 で一定 |
| `ruff --select F,B` | 静的解析（`F` = 実際の誤り、`B` = バグを招く書き方） | 全パス |

**画面なしでできる最速チェック:**

```bash
python -m py_compile *.py                          # 構文
ruff check --select F,B *.py                       # 実際の誤り + バグを招く書き方
python -c "import ast;[ast.parse(open(f).read()) for f in __import__('glob').glob('*.py')]"
```

**500 行以内かの確認:**

```bash
wc -l *.py | sort -n
```

---

## 付録: レビュー時点の設定値

```python
FRUIT_SCORE     = 50      # フルーツ 1 個のスコア
TARGET_SCORE    = 800     # 到達した時点でラウンド勝利
MAX_HP          = 3
ROUNDS_TO_WIN   = 2       # 3 本勝負
MAX_ROUNDS      = 3       # = ROUNDS_TO_WIN * 2 - 1（自動計算）
SURVIVE_BONUS   = 100     # MVP 計算時、残りハート 1 つあたり 100
SCORE_TRANSFER  = 0.5     # 頭同士の衝突で移るスコア（スコアが動く唯一の場所）
SELF_HIT_DAMAGE = 1
STUN_FRAMES     = 30
INVULN_FRAMES   = 60
HIT_RADIUS      = 12
```

各値の詳細と変更方法は [MANUAL.ja.md](MANUAL.ja.md) 第 8 章にあります。
