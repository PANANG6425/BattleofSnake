# Snake Battle — Local Multiplayer | MANUAL

> Language: [ไทย](MANUAL.md) · [English](MANUAL.en.md) · **日本語**

1台のPCで2人が対戦するスネークゲームです。`turtle` だけで書かれています（pygame は使いません）。
`snake_baseline1P.py` を拡張したものです。

> **このバージョンはモジュールに分割済み** — エントリーポイントは `main.py`（旧・単一ファイルの `snake_battle_2P.py` は廃止）

---

## 1. インストール & 実行

**必要なもの**

- `tkinter` が入った Python 3.8+（turtle は内部で tkinter を使います）
  - Windows / macOS: python.org のインストーラーに最初から含まれています
  - Ubuntu / Debian: `sudo apt install python3-tk`
- **プレイするだけなら追加インストールは不要** — 同梱の音と画像はそのまま使えます
- 任意（アセットを再生成する場合、または音質を上げたい場合のみ）
  - `pip install pillow` — `make_sprites.py` を実行する場合、または自分で `.png` を置く場合のみ
  - `pip install pygame` — 入れると音が重ねて再生できて遅延も最小になります（入れなくても音は鳴ります）

**実行**

```bash
python main.py            # ゲームをプレイ
python make_sprites.py    # GIF スプライト一式を再生成（Pillow が必要）
python make_sounds.py     # WAV サウンド一式を再生成（stdlib のみ、インストール不要）
```

**ファイル構成**

```
snake_battle_2P/
├── main.py          ← エントリーポイント。このファイルを実行（全モジュールの結線 + game loop + Result 画面）
├── config.py          定数はすべてここ。バランス調整はこのファイルで
├── screen.py          ゲーム唯一の turtle ウィンドウを作る（Screen は singleton）
├── sprites.py         GIF を turtle に読み込む + PNG→GIF 変換
├── sounds.py          ノンブロッキングな音の再生。backend は自動選択
├── effects.py         particle system（ほこり／きらめき）
├── arena.py           壁 + 障害物ボックス + ボックス衝突判定
├── snake.py           Snake クラス（2体生成 = マルチプレイ）
├── fruit.py           フルーツ + 安全な位置へのランダム配置
├── hud.py             上部の stats パネル + 頭上のスタンバー
├── rules.py           戦闘ルール／フルーツ取得／勝利条件
├── make_sprites.py    スプライト generator（任意）
├── make_sounds.py     サウンド generator（任意）
└── assets/
    ├── *.gif          スプライト画像
    └── sounds/*.wav   サウンド
```

import 順: `config` → `screen` → `sprites`/`sounds` → `arena`/`effects` → `snake`/`fruit` → `rules`/`hud` → `main`
**下位モジュールから上位モジュールへ逆向きに import してはいけません**（circular import になります）

> `assets/` が無い、またはファイルが壊れていても、ゲームは**そのまま動きます** — スプライトは色付きの四角にフォールバックし、音は無音になります

---

## 2. 操作キー

| | Player 1（シアン） | Player 2（オレンジ） |
|---|---|---|
| 移動 | `W` `A` `S` `D` | `↑` `↓` `←` `→` |
| Speed Boost | `Q` | `O` |
| Invisibility | `E` | `P` |
| ミュート切り替え | `M` | |
| リスタート | `R`（Result 画面のみ） | |

> **先にゲームウィンドウをクリックしてください**。しないとキーが効きません（turtle はフォーカスが必要）
> **180度の反転はどんな場合もできません** — 停止中や壁に押し当てている最中も含みます（第9章を参照）
> 標準的なスネークゲームと同じで、まず左右どちらかに1回曲がる必要があります

---

## 3. ルール

### アイテム取得／障害物への衝突

| イベント | 結果 |
|---|---|
| フルーツを食べる 🍎 | +100 スコア、1 節長くなる、skill bar +25、`eat` の音 + きらめき |
| 障害物ボックスに衝突 | 30 フレームのスタン + ほこり + `bump` の音 — **死なない、HP も減らない** |
| アリーナの壁に衝突 | 障害物ボックスと同じ |
| 自分の体・自分の尾を噛む | スタン — **死なない**。しかも蛇は自力で抜け出せます（第9章を参照） |

### 攻撃 — 両プレイヤー共通のルール

| 自分の頭が当たった場所 | 結果 |
|---|---|
| 敵の**頭** | 敵が 1 HP 減少 + 敵のスコア −50% |
| 敵の**尾**（最後の節） | 敵が 1 HP 減少 + 敵のスコア −50% |
| 敵の**胴体**（中間の節） | **自分が** 1 HP 減少 + 自分のスコア −50% |

- 同時に頭と頭がぶつかった場合は両者ダメージ（ルールは両方向で判定されます）
- ダメージを受けた後は **60 フレームの immunity** が付き、スプライトが点滅します。この間は再度ダメージを受けません
- 衝突と判定される距離は 12 px（自分への衝突は 10 px）

### スキル（50 bar を消費、180 フレーム ≈ 3 秒持続）

| スキル | 結果 |
|---|---|
| Speed Boost | 3 → 6 px/フレーム |
| Invisibility | 胴体が消え、頭が薄いスプライトになる — **衝突判定は通常どおり有効** |

### 勝利条件

1. 敵の HP = 0 → 勝ち
2. スコアが 500 に到達 → 即勝ち
3. 同時に到達 → スコアが高い方が勝ち／同点は DRAW
4. 同時に HP が尽きた場合は DRAW

---

## 4. バランス調整 — 編集するのは `config.py` だけ

| 変数 | 初期値 | 意味 |
|---|---|---|
| `MAX_HP` | 3 | 1人あたりのハート数（ハートアイコンの列は自動で数が合います） |
| `TARGET_SCORE` | 500 | 即勝ちになるスコア |
| `FRUIT_SCORE` / `FRUIT_COUNT` | 100 / 2 | 1個あたりのスコア／フィールド上のフルーツ数 |
| `SCORE_PENALTY` | 0.5 | ダメージを受けたときのスコア倍率 |
| `BASE_SPEED` / `BOOST_SPEED` | 3 / 6 | 1フレームあたりの px、通常／Boost |
| `SEG_SPACING` | 15 | 胴体の節どうしの間隔 |
| `START_LENGTH` | 4 | 開始時の長さ |
| `SKILL_COST` / `SKILL_GAIN` / `SKILL_FRAMES` | 50 / 25 / 180 | 消費量／フルーツ1個あたりの獲得量／持続時間 |
| `STUN_FRAMES` | 30 | スタンのフレーム数 |
| `INVULN_FRAMES` | 60 | ダメージ後の immunity |
| `BUMP_COOLDOWN` / `SELF_HIT_COOLDOWN` | 45 / 45 | 連続スタンを防ぐ — **`STUN_FRAMES` より大きくすること** |
| `HIT_RADIUS` / `SELF_HIT_RADIUS` | 12 / 10 | 衝突と判定される距離 |
| `SELF_SKIP_SEGMENTS` | 3 | 頭の直後にある、噛めない節の数 |
| `OBSTACLE_COUNT` / `OBSTACLE_SIZE` / `OBSTACLE_SPOTS` | 6 / 60 / list | 障害物ボックス |
| `FRAME_MS` | 16 | 1フレームあたりの ms（16 ≈ 60 FPS） |
| `PLAYER_SETUP` | — | プレイヤーの名前／色／スポーン地点 |
| `FX_*` | — | パーティクルの数／寿命 |
| `SOUND_ON` / `SOUND_VOLUME` | True / 0.6 | サウンド |
| `USE_SPRITES` | True | `False` = 従来の色付き四角の見た目を強制 |

> **注意すべき2点**
> 1. `BUMP_COOLDOWN` と `SELF_HIT_COOLDOWN` は `STUN_FRAMES` **より大きくしなければなりません** — この差こそが、蛇が引っかかった場所から抜け出せることを保証しています。小さく設定すると deadlock バグが再発します。
> 2. `BOOST_SPEED` は `SEG_SPACING` 程度を超えないようにしてください。それより速いと、頭が1フレームでボックスや敵の体を「飛び越えて」しまいます。衝突判定は点と点で行っており、フレーム間の経路上は判定していないためです。

---

## 5. 1フレーム内の処理順序（`main.game_loop`）

```
1. tick_timers()        stun / immunity / cooldown / スキルをカウントダウンし、速度を設定
   move()               頭を1歩進める（衝突した場合 = 座標を commit しない）
   refresh_segments()   胴体の節の座標を1フレームに「1回だけ」計算し、cache する
2. resolve_fruit()      フルーツの取得
   resolve_self_collision()
3. resolve_attacks(p1→p2) の後に resolve_attacks(p2→p1)
4. render()             胴体を描画し、その上に頭を stamp
   effects.update_and_draw()   パーティクル
   hud.draw_panel()            stats パネル
   hud.draw_stun_bars()        頭上のスタンバー（最後に描画 = 最前面）
5. check_win()          勝者がいれば → show_result() して loop を停止
   wn.update()          画面へ一度にまとめて反映
   ontimer(16 ms)       次のフレームを予約
```

---

## 6. 説明できるようにしておきたい仕組み（素直でない箇所）

1. **胴体は path history から作られ、turtle のリストではない**
   `move()` は毎フレーム頭の座標を `self.path` に記録し、`_compute_segments()` がその履歴を逆向きにたどって**移動距離を累積**し、15 px ごとに1節を置きます
   *なぜフレーム数ではなく距離で数えるのか:* Boost 中は 6 px/フレーム進むため、フレーム数で数えると節の間隔が2倍になり、胴体が伸びてしまいます

2. **`refresh_segments()` は1フレームに1回だけ呼ぶ**
   以前は `segments()` が1人あたり毎フレーム3〜4回再計算されていました（rules から3か所 + render）。現在は1回だけ計算して cache しています。

3. **頭は最後に stamp される**
   turtle の canvas は生成順に重なります。もし頭が `__init__` で作った turtle のままなら、後から stamp した胴体が頭を覆ってしまいます。そこで頭の turtle は非表示にして座標／衝突判定の基準としてのみ使い、頭の画像は最後に stamp で描いています。

4. **胴体全体で turtle は1つだけ**（`clearstamps()` + `stamp()`）。蛇が長くなってもオブジェクトは増えません

5. **`path` は毎フレーム切り詰められ**、必要な分だけを保持します。そうしないとリストが無限に増えていきます

6. **stats パネルは専用の領域を持っています。** `ARENA_T = 205`、上の壁は y=210 に描かれるので、蛇やフルーツが数字に重なることはありません

7. **deadlock を防いでいるのは cooldown です**（第9章を参照）

---

## 7. turtle とサウンドの制約

### turtle

| 制約 | コードへの影響 |
|---|---|
| image shape は **GIF** のみ対応 | `sprites.py` が Pillow で PNG→GIF 変換します |
| **画像は回転できない** | 頭のスプライトを4方向分用意し、`facing` に応じて `shape()` を切り替えます |
| **`shapesize()` は画像に効かない** | ファイルのピクセルサイズ = ゲーム内のサイズ |
| **`color()` は画像に効かない** | エフェクトはスプライトの差し替え（ghost）か点滅（stamp しない）で表現します |
| shape の名前 = **`addshape()` に渡した path** | コードは path をそのまま shape 名として保持します |
| GIF の透過は **オン／オフのみ** | 縁が少し硬く見えますが、これは正常です |
| `Screen` は **singleton** | `turtle.Screen()` を呼ぶのは `screen.py` だけです |
| `tracer(0)` | 毎フレーム自分で `wn.update()` を呼ぶ必要があります |

### サウンド

`sounds.py` は backend を順番に試し、最初に使えたものを採用します:

1. **pygame.mixer** — 最良。音を重ねて再生でき、volume も効きます（`pip install pygame` が必要）
2. **winsound** — Windows 専用、Python に同梱、同時に1音のみ
3. **command line** — `afplay`（macOS）/ `paplay`, `aplay`, `ffplay`（Linux）
4. **silent** — 使えるものが無い場合 → `play()` は何もせず、ゲームは通常どおり動きます

すべての `play()` は try/except で囲まれています — 音声ファイルが無くてもサウンドカードに問題があっても、**ゲームを壊してはいけません**
画面下部中央のヒント行にサウンドの状態（`SOUND: on` / `off` / `none`）が表示され、`M` キーで切り替えられます。選ばれた backend 名は起動時に terminal に print されます。

---

## 8. 画像とサウンドをチームのものに差し替える

`assets/` に **同じ名前・同じサイズ** でファイルを上書きすれば、コードを触る必要はありません

| ファイル | サイズ |
|---|---|
| `p1_head_{up,down,left,right}.gif` | 20×20 |
| `p1_head_{...}_ghost.gif` | 20×20 |
| `p1_body.gif`, `p1_body_ghost.gif` | 16×16 |
| （`p2_` 用の同じ一式） | |
| `heart_full.gif`, `heart_empty.gif` | 18×18 |
| `fruit.gif` | 16×16 |
| `sounds/{eat,hit,bump,skill,win}.wav` | — |

- `.png` を置いても構いません（同じ名前）。初回実行時に `.gif` へ変換されます（Pillow が必要）
- 頭は **右向き** を原型として描き、`make_sprites.py` に4方向へ回転させます
- スプライトを大きくする場合は、`SEG_SPACING` と `HIT_RADIUS` も合わせて調整してください
- 蛇の色や形を変えるには `make_sprites.py` の `PALETTES` を編集して再実行します
- サウンドを変えるには `make_sounds.py` の数値を編集して再実行するか、自分の `.wav` を上書きします
  各サウンドは1行で定義されています: `tone(開始周波数, 終了周波数, 長さ_ms, wave_fn, decay, noise)`
  例えば `save(tone(660, 880, 60) + tone(880, 1320, 70), 'eat')` は上昇する2音を連結したものです
  波形は `square`（chiptune）か `saw`（より明るい）から選び、音は `+` で連結、`silence(ms)` で間を空けます
- サウンドを追加するには `sounds.py` の `SOUND_NAMES` に名前を足し、必要な場所で `sfx.play('その名前')` を呼びます

---

## 9. 修正済みのバグ — 自分の尾を噛んだとき／壁に衝突したときの deadlock

**以前の症状:** 自分の尾を噛むとプレイヤーが固まり、まったく動かせなくなる／壁に衝突するとスタンが延々とループする

**本当の原因は、同時に作用していた3つでした**

1. 衝突時、旧コードは `direction = 'stop'` にしていた → 蛇が静止し、胴体が頭から離れて動かなくなる
2. 旧 `turn()` は `direction` と比較していた → `direction == 'stop'` の間は **180度の反転が可能** で、頭が自分の首に突っ込んでしまう
3. cooldown が無かった → 3 px 動いても頭はまだ同じ胴体の節に重なっているため、即座に再スタンし、永久にループする

**修正方法**

| 修正 | 場所 |
|---|---|
| 壁／ボックス／自分への衝突時に **`direction` をクリアしない** — 蛇は進み続け、引っかかった場所から自力で抜け出せる | `snake.move()`, `rules.resolve_self_collision()` |
| `turn()` は `direction` ではなく **`facing`** と比較する → 180度の反転はどんな場合もできず、逃げ道は左右への旋回（常に可能） | `snake.turn()` |
| `BUMP_COOLDOWN` / `SELF_HIT_COOLDOWN` = 45（`STUN_FRAMES` 30 より大きい）→ 再スタンされずに動ける 15 フレーム ≈ 45 px の猶予ができ、**抜け出せることが保証される** | `config.py`, `snake.tick_timers()` |
| 壁にキーを押しつけ続けても連続スタンしない（cooldown が防ぐ） | `snake.move()` |

headless テストの結果: 旧コードは **5秒間で 0 px** しか動かなかった（本当に固まっていた） — 新コードは自分の尾を噛んでも 360 px 進み続け、壁に衝突しても即座に旋回して逃げられ、自分への衝突で HP が減ることもありません。

---

## 10. よくあるトラブル

| 症状 | 原因／対処 |
|---|---|
| `ModuleNotFoundError: tkinter` | `python3-tk` をインストール（Linux）、または python.org の Python を使う |
| キーを押しても蛇が動かない | まだゲームウィンドウをクリックしていない |
| 蛇がスプライトではなく色付きの四角になる | `assets/` が `main.py` と同じフォルダに無い → `python make_sprites.py` を実行 |
| 音が出ない | 画面下部中央を確認。`SOUND: none` ならファイルが無い（`python make_sounds.py`）か backend が無い（`pip install pygame`） |
| 音が遅れる／途切れる | `pygame` を入れると大きく改善します（`cli` backend は毎回 process を新規に起動します） |
| `ImportError: cannot import name ...` | import の順序が間違っています。第1章の逆向き import 禁止のルールを参照 |
| ゲームがカクつく | `FX_MAX` / `OBSTACLE_COUNT` を減らす、または `FRAME_MS` を増やす（16 → 20） |
| ウィンドウが開いてすぐ閉じる | terminal から実行すると本当のエラーが見えます |

---

## 11. まだ未実装（設計ドラフト基準）

画面 1（Start menu）、2（Character select）、6（Setting）、7（Leaderboard）
現時点の `main.py` はすぐに試合へ入り、Result で終了します

続けて作るなら `screens.py` の追加をおすすめします（state machine: `MENU` / `SELECT` / `PLAY` / `RESULT`）。
そして `main.py` で state を切り替えます — ゲーム本体は変更不要です。Character select は既存の `load_shape()` +
`PALETTES` をそのまま使えます（`p1_green` のような key を追加するだけ）
