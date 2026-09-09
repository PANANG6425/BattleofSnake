# Snake Battle — マニュアル

> 言語: [ไทย](MANUAL.md) · [English](MANUAL.en.md) · **日本語**

`turtle` だけで書いたローカル対戦スネークゲームです（描画に pygame は使いません）。
モードは **1 Player** と **2 Player Battle** の 2 つ。試合前にキャラクターとパワーを選びます。

エントリーポイントは **`main.py`** だけです。

---

## 1. インストールと実行

**必須**

- `tkinter` が入った Python 3.8+（turtle は内部で tkinter を使います）
  - Windows / macOS: python.org のインストーラに同梱されています
  - Ubuntu / Debian: `sudo apt install python3-tk`
- **追加インストールは不要** — ゲームは `turtle` と標準ライブラリだけで動きます。
  スプライト `assets/*.gif` はリポジトリに同梱済みです。
- 任意
  - `pip install pillow` — `make_sprites.py` でスプライトを再生成するときだけ必要
    （キャラクターを追加した場合など）

> **pygame は不要です。** 描画も音も turtle + 標準ライブラリだけで動きます
> （音については第 6 章）。

**実行**

```bash
python main.py            # プレイ
python make_sprites.py    # GIF スプライトを全部再生成（Pillow が必要）
```

起動時にサウンドの状態が 1 行表示されます。例: `SOUND: 8 events via winsound`。
音が出ていない場合は、その理由と対処方法も表示されます。

フォントとウィンドウアイコンは `config.py` で変更できます — 9.4 と 9.5 を参照。

---

## 2. ファイル構成

**baseline kit のフォーマット**（Section 1-5）に沿っています。1 ファイル 500 行以内。

```
Code/snake_battle_2P/
├── main.py            26   ← エントリーポイント、これを実行
│
├── config.py         192   Section 3  全定数 + キャラクター/パワーのレジストリ
├── engine.py         436   Section 1  唯一の Screen、スプライト、シーン切替、描画補助
├── entity.py         256   Section 2  両モード共通の Snake クラス + パワーの実行部
├── audio.py          281              ノンブロッキングな効果音（ファイルが無ければ無音）
│
├── screens.py        411              メニュー・キャラセレ・リザルト 2 種
├── solo.py           209              1 人プレイ        Section 2, 3, 4, 5
├── battle.py         439              2 人対戦          Section 2, 3, 4, 5
│
├── make_sprites.py   138              スプライト生成ツール（実行時には不要、Pillow が必要）
└── assets/                            スプライト *.gif（+ .wav を入れるなら sounds/）
```

**Section 1-5 の場所**

| Section | 場所 |
|---|---|
| 1 Screen Setup | `engine.py` — turtle は 1 プロセスに 1 つの Screen しか許さないため集約 |
| 2 Game Entities | `entity.py`（Snake）+ 各モードファイルと `screens.py` の Section 2 見出し |
| 3 Parameters & Physics | プロジェクト全体は `config.py`、モード固有のレイアウトは各モードの Section 3 |
| 4 Input Handling | 各モードファイルと `screens.py` の Section 4 見出し |
| 5 Main Game Loop | `solo.py` / `battle.py` の Section 5 見出し（`wn.ontimer(game_loop, 16)`） |

**import の向き** — `config` は何も import しない → `engine` が Screen を作る →
`audio` / `entity` がその上に乗る → `screens` / `solo` / `battle` →
`main` は誰からも import されません。

`snake_battle_2P.py`（最初の 633 行の単一ファイル版）は**削除済み**です。誰も import して
いませんでした。中身を見たい場合は
`git show 33d5b4c:Code/snake_battle_2P/snake_battle_2P.py`

---

## 3. 操作

**メインメニュー** — ボタンをクリック、または `1` / `2` キー

**キャラクターセレクト** — プレイヤーごとに大きなカードが 1 枚。上の **◀ ▶** 矢印で
ロスターをめくります（カード本体をクリックしても次に進みます）。パワーのアイコンは
枠全体がクリック可能です。カード下のドットが現在の位置を示します。キーボードでも操作できます:

| | キャラクター | パワー |
|---|---|---|
| P1 | `A` / `D` | `W` / `S` |
| P2 | `←` / `→` | `↑` / `↓` |

`Enter` で開始 · `Esc` でメニューへ戻る

**ゲーム中**

| | 1 Player | 2 Player |
|---|---|---|
| 移動 | 矢印キー | P1 `W A S D` · P2 矢印キー |
| パワー使用 | `SPACE` | P1 `Q`（または `E`）· P2 `O`（または `P`） |
| 音の ON/OFF | `X` | `X` |
| リスタート | `R`（ゲームオーバー後） | `R`（ROUND OVER = **次のラウンド**、スコアと MVP 明細を持ち越し） |
| メニューへ | `M` | `M` |

> **パワーはプレイヤーごとに 1 キーだけ**です。選んだパワーが何であれ同じキーで発動します。
> 各プレイヤーが選べるのは 1 つだけなので、キーが足りなくなることなくパワーを増やせます。

---

## 4. キャラクター（4 体）

| キャラクター | 色 |
|---|---|
| AQUA | シアン |
| EMBER | オレンジ |
| VENOM | グリーン |
| ROYAL | バイオレット |

**4 体の性能は完全に同じ**で、違うのは色だけです。硬い・速いといった差はありません。
キャラクターはスキンであり、2P ではどちらの蛇かを見分ける手段でもあります。そのため
**2 人が同じキャラクターを選ぶことはできません** — 矢印は相手が持っているキャラクターを
自動でスキップします。パワーは重複して選べます。

**キャラクターの追加** — `config.py`（Section 3F）にエントリを追加して
`python make_sprites.py` を実行するだけ。キャラクターセレクトはレジストリから数を読むので
（ドットも自動で増えます）UI のコードを触る必要はありません。

生成せずに自分の `.gif` を使いたい場合は第 9 章へ。

> カードの立ち絵は turtle だけで描いています（キャラクターごとに色を変えた compound shape）。
> 画像ファイルではありません。スプライトの `.gif` は使えません。**turtle は image shape を
> 拡大縮小できない**ため、20×20 の頭は `shapesize()` を何に設定しても 20×20 のままです。

---

## 5. パワー（5 種類）

| パワー | 効果 | コスト | 持続 |
|---|---|---|---|
| **SPEED** | 移動速度が 2 倍 | 50 | 180 フレーム |
| **STEALTH** | 胴体が消え、頭がゴースト化（**当たり判定は全部残る**） | 50 | 180 フレーム |
| **SHIELD** | ダメージを一切受けない | 50 | 150 フレーム |
| **PHASE** | 障害物と自分の尾をすり抜ける | 50 | 150 フレーム |
| **FEAST** | フルーツのスコアが 2 倍 | 40 | 240 フレーム |

ゲージは最大 100。フルーツ 1 個で +25（2P）/ +20（1P）。発動中に再発動はできません。

**パワーの追加** — `config.py`（Section 3G）では各 `effect` を、ゲームが既に解釈できる
**効果の種類**として書きます:

```python
speed_mult   float   頭の速度の倍率
score_mult   float   フルーツのスコア倍率
cloak        bool    胴体を隠し、頭をゴーストスプライトに差し替え
invincible   bool    受けるダメージを無視
noclip       bool    障害物と自分の胴体が無害になる
```

> `cloak` は胴体を隠すだけで、**何かをすり抜ける効果はありません**。当たり判定を免除するのは
> `noclip`（PHASE）と `invincible`（SHIELD）だけです。以前は 1P だけ `cloak` も免除して
> いたため、1P では STEALTH が PHASE の完全上位互換になっていました。現在は両モードで
> 統一されています。

既存の種類を使い回す新しいパワーなら → **エントリとアイコンを追加するだけで完了。
ゲームのコードは一切変更不要です。** 本当に新しい種類が必要な場合は、ここにキーを追加し、
それを尊重すべき箇所 1 か所で `entity.py` の `powers_flag()` / `powers_effect()` から読みます。
ゲーム内でパワー名をハードコードしている箇所はありません。

---

## 6. サウンド — 手順どおりに

**音声ファイルは生成しませんし、パッケージも不要です。** 音声ファイルが 1 つも無い状態では
`sfx.play()` は即座に return し、サウンドのコードが無いのと全く同じように動きます。

### 手順 1 — ゲームがどの音を要求するか知る

イベントは 9 種類。呼び出し箇所は次のとおりです:

| イベント | 鳴るタイミング | 呼び出し元 |
|---|---|---|
| `eat` | フルーツを取った | `solo.py` · `battle.py` |
| `hit` | HP が減った（敵の攻撃・自分の胴体） | `battle.py` |
| `bump` | 壁や障害物にぶつかった | `battle.py` |
| `power` | パワーが実際に発動した | `solo.py` · `battle.py` |
| `win` | 勝者が出たリザルト画面 | `battle.py` |
| `lose` | 1P のゲームオーバー | `solo.py` |
| `select` | キャラクター / パワーを選んだ | `screens.py` |
| `start` | 試合開始 | `screens.py` · `solo.py` · `battle.py` |
| `score` | 未使用 — 予備 | – |

### 手順 2 — ファイルを置く場所（**2 か所から選べます**）

リポジトリのルートには既に `sound_effect/` フォルダがあります（現在 `.mp3` が 12 個）。
ゲームは**両方**を探し、**最初に見つかったものを使います**。優先順は次のとおりです:

```
BattleofSnake/
├── sound_effect/                          ← 選択肢 2（既存のパックがある場所）
│   ├── eat.wav                                  ← イベント名（eat_fruit.wav より優先）
│   ├── eat_fruit.wav                            ← その場で変換すれば改名も移動も不要
│   └── eat_fruit.mp3                            ← 元の mp3（pygame のみ）
└── Code/snake_battle_2P/
    └── assets/sounds/                     ← 選択肢 1、すべてより優先
        └── eat.wav
```

| 順 | 探す場所 | 備考 |
|---|---|---|
| 1 | `assets/sounds/<event>.wav` | すべてに優先する「正式な」置き場 |
| 2 | `sound_effect/<event>.wav` | 例: `sound_effect/eat.wav` — **一番簡単、置くだけ** |
| 3 | `sound_effect/<パック名>.wav` | 例: `sound_effect/eat_fruit.wav` — mp3 をその場で変換、名前はそのまま |
| 4 | `sound_effect/<パック名>.mp3` | pygame がある場合のみ · **pygame なし = スキップ** |

**どのフォルダでも `.wav` を `.mp3` より先に試します。** `.wav` は標準ライブラリだけで
鳴るからです。

追加の検索フォルダは `config.py` で変更できます:

```python
EXTRA_SOUND_DIRS = ['../../sound_effect']   # Code/snake_battle_2P/ からの相対パス
```

### 手順 3 — イベント名でファイルを置く

```
eat.wav    hit.wav    bump.wav    power.wav
win.wav    lose.wav   select.wav  start.wav
```

パック側の名前をそのまま使ってもかまいません（上記の選択肢 3）。対応表は既にあります:

| イベント | 使えるパック名 |
|---|---|
| `eat` | `eat_fruit` · `motion_eating` |
| `hit` | `bomb` |
| `bump` | `impact_wall` |
| `power` | `increase_speed` · `skill_selection` |
| `win` | `result_fanfare` |
| `lose` | `bomb` |
| `select` | `setting` · `skill_selection` |
| `start` | `start_1` · `start_2` · `start_3` |
| `score` | `score`（ゲームからはまだ呼ばれません） |

**一部だけでも大丈夫です** — ファイルが無いイベントは単に無音になり、エラーにはなりません。
`eat`・`hit`・`bump`・`power`・`win` の 5 つがあれば十分に賑やかになります。

> **なぜ `.wav` か** — Windows では標準ライブラリの `winsound` で再生されるため、
> インストールが一切不要です。`.mp3` は `winsound` や CLI プレイヤーでは**再生できません**。
> mp3 を読めるのは pygame だけで、pygame は完全に任意です。
>
> フォルダごと一括変換（`.mp3` の隣に `.wav` を書き出します。ゲームはそこも探します）:
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
> **重要なのは `-c:a pcm_s16le` です** — これが無いと 32-bit float になり、
> `winsound` が受け付けません。

### 手順 4 — 起動してステータス行を読む

```bash
python main.py
```

```
SOUND: 8 events via winsound          ← 動作中
SOUND: off - no audio files found...  ← ファイルが無い。何をすべきか書いてあります
SOUND: off - only .mp3 files were found, and .mp3 needs pygame...
```

ゲーム中は **`X`** でミュート切替。

### ファイルは見つかるのに音が出ない — ここで解決します

**圧倒的に多い原因は「16-bit PCM ではない」ことです。** `winsound` が再生できるのは
8 bit または 16 bit の PCM WAV だけです。オンライン変換や Audacity は **32-bit float**
で書き出すことが多く、拡張子は `.wav` でも `winsound` では再生できません。

ゲームが自動でチェックします。起動時にこう出ます:

```
SOUND: 2 events via winsound  (4 file(s) skipped as unplayable - see sfx.diagnose())
```

続いてファイルごとの表が出ます:

```
event    status     file / reason
eat      ready      eat.wav  [1 ch, 16-bit, 22050 Hz]
bump     UNUSABLE   bump.wav  <-- not a playable PCM wav: unknown extended format...
power    UNUSABLE   power.wav <-- not a playable PCM wav: unknown format: 2
win      UNUSABLE   win.wav   <-- not a playable PCM wav: file does not start with RIFF id
lose     UNUSABLE   lose.wav  <-- 1 ch, 24-bit - winsound needs 8 or 16-bit, not 24
```

| メッセージ | 意味 | 対処 |
|---|---|---|
| `unknown extended format` | 32-bit float | 16-bit PCM で再エンコード |
| `unknown format: 2` | ADPCM（圧縮） | 16-bit PCM で再エンコード |
| `does not start with RIFF id` | mp3 を `.wav` にリネームしただけ | リネームではなく実際に変換する |
| `winsound needs 8 or 16-bit, not 24` | 24-bit | 16-bit PCM で再エンコード |

**正しい再エンコード**

```bash
ffmpeg -i broken.wav -c:a pcm_s16le -ac 1 -ar 22050 fixed.wav
```

**Audacity では** — ファイル > 書き出し > WAV として書き出し で
**「WAV (Microsoft) signed 16-bit PCM」** を選んでください。32-bit float は不可です。

**再生時の詳細を見たい場合** は `config.py` で `SOUND_DEBUG = True` にすると、
再生に失敗するたびに理由が表示されます。

**いつでも自分で確認**

```python
from audio import sfx
print(sfx.diagnose())
```

### 同梱の mp3 を wav に変換する

リポジトリには `sound_effect/*.mp3` が既に入っています。Audacity、オンライン変換、
または ffmpeg などで変換してください:

```bash
ffmpeg -i sound_effect/eat_fruit.mp3      -c:a pcm_s16le -ac 1 -ar 22050 assets/sounds/eat.wav
ffmpeg -i sound_effect/bomb.mp3           -c:a pcm_s16le -ac 1 -ar 22050 assets/sounds/hit.wav
ffmpeg -i sound_effect/impact_wall.mp3    -c:a pcm_s16le -ac 1 -ar 22050 assets/sounds/bump.wav
ffmpeg -i sound_effect/increase_speed.mp3 -c:a pcm_s16le -ac 1 -ar 22050 assets/sounds/power.wav
ffmpeg -i sound_effect/result_fanfare.mp3 -c:a pcm_s16le -ac 1 -ar 22050 assets/sounds/win.wav
ffmpeg -i sound_effect/setting.mp3        -c:a pcm_s16le -ac 1 -ar 22050 assets/sounds/select.wav
ffmpeg -i sound_effect/start_1.mp3        -c:a pcm_s16le -ac 1 -ar 22050 assets/sounds/start.wav
```

効果音ならモノラル 22050 Hz で十分です。全部合わせて 660 KB 程度になります。

### 別の方法: pygame を入れて mp3 をそのまま使う

```bash
pip install pygame
```

これだけで `sound_effect/*.mp3` を変換せずにそのまま使えるようになり、音の重ね再生も
できます。ただし**必須ではありません** — `.wav` の方法なら何もインストールしません。

### 探索順とバックエンド

イベントごとに、最初に見つかったファイルが使われます:

1. `assets/sounds/<event>.wav`
2. `config.EXTRA_SOUND_DIRS` の各フォルダ（既定は `['../../sound_effect']`）

| バックエンド | インストール | .mp3 | 重ね再生 |
|---|---|---|---|
| `winsound`（Windows 標準ライブラリ） | **不要** ← 本筋 | 不可 | 不可 |
| コマンドライン（afplay/paplay/aplay/ffplay） | 不要 | 不可 | – |
| `pygame.mixer` | 必要（任意） | 可 | 可 |
| silent | – | – | 使えるファイルが無い |

### 設定

```python
SOUND_ON     = True                     # config.py - ミュート解除で開始
SOUND_DIR    = 'sounds'                 # assets/ 内のサブフォルダ
SOUND_VOLUME = 0.6                      # 0.0-1.0（pygame バックエンドのみ有効）
EXTRA_SOUND_DIRS = ['../../sound_effect']
```

`audio.py` は例外を投げてもブロックしてもいけません。ファイルが無い・壊れている・
オーディオデバイスが使用中、そのいずれでもゲームが落ちてはいけません。

---

## 7. ルール

**フルーツ** → スコア +100（FEAST 中は ×2）、胴体 +1 節、パワーゲージ増加。
2P はフィールドに常に 2 個、互いに 40 px 以上離して配置されます。

**外壁 / 障害物** → 30 フレームのスタン、方向は停止にリセット、移動は確定されません
（HP は減りません）。PHASE は障害物をすり抜けますが、**外壁は必ず止まります**。

**自分の胴体** → **30 フレームのスタン + HP 1**（頭の直後 2 節は除外）。
**スコアは減りません** — 自分のミスで失うのはハートだけです。

これで HP が一気に溶けないよう 3 つの歯止めがあり、3 つとも必要です:

1. **70 フレームの猶予** — これが無いと、頭が自分の胴体の上に乗ったままなので毎フレーム
   判定が成立してしまいます
2. **頭が実際に動いたフレームのみ判定** — とぐろを巻いた状態で壁にぶつかった蛇は
   `direction='stop'` になり、自分の胴体から離れません。これが無いと 70 フレームごとに
   1 ハート失い、止まったまま死にます
3. **60 フレームのダメージ無敵を尊重** — 敵に殴られた直後の自傷は重複しません

スタンが切れれば蛇は自分でとぐろから抜け出すので、キー入力は不要です。HP を減らさず
スタンだけにしたい場合は `config.py` の `SELF_HIT_DAMAGE = 0` にしてください。

### コアゲーム — 噛んだ側が損をする

このゲームの芯は **フルーツを食べる → スコアを守る → 相手に自分を噛ませる** です。
噛みつきは噛まれた側ではなく**噛んだ側**を罰するので、スコアで先行している蛇は
胴体と尾を相手の口の前で振ってみせたくなり、後ろにいる蛇は差し出された餌を
我慢しなければなりません。そして我慢して正面からぶつかれば、後ろの蛇は
**スコアを受け取れます**。フルーツと並ぶもう 1 つの得点手段です。

**覚えるべき唯一のルール: スコアが移動するのは「頭と頭」の衝突だけ**です。
それ以外の衝突はすべて HP のみを失い、スコアには一切触れません。

| 出来事 | 結果 |
|---|---|
| **頭と頭**、スコアが異なる | **スコアが高い側**が HP −1、さらに**自分のスコアの半分を譲渡** · **スコアが低い側の勝ち: スコアをもらえて、HP も失いません** |
| **頭と頭**、スコアが完全に同じ | 両方が HP −1 · **譲渡は発生しません** |
| **自分の頭が相手の胴体か尾に触れる**（噛みつき） | **噛んだ側が HP −1 だけ**。スコアは減りません — **噛んだ側のスコアが低い場合でも同じ**です · 噛まれた側は失いも得もしません |
| **自分の胴体** | HP −1 のみ、スコアは変化なし |
| **外壁 / 障害物** | 30 フレームのスタンのみ、HP もスコアも減りません |

胴体と尾は意図的に**同じ扱い**です。旧ルールは尾を噛むことに報酬を与えており、
ゲームの狙いと逆でした。

> **1 回の衝突につき 1 回だけ判定します。** 譲渡が起きた直後は「どちらが高いか」が
> 入れ替わるため、ロックが無いと次のフレーム（頭はまだ接触、負けた側はスタンで
> その場に固定）で、**たった今その衝突に勝った側**を罰してしまいます。そのため、
> どちらかに無敵フレームが残っている間は頭と頭の判定をスキップします。
> 両者が回復してから、初めて新しい衝突として数えます。

ダメージ後は 60 フレームの無敵（スプライトが点滅）が付き、1 回の接触で連続ヒットしません。
SHIELD は HP を守ります。譲渡は HP が実際に減ったかどうかに紐づいているため、
**SHIELD は結果としてスコアも守ります。**

### ラウンド勝利とマッチ勝利

**1 ラウンド** → 相手の HP が 0、**または**スコア 500 到達。同時なら高スコア側の勝ち、
同点なら DRAW。

**ラウンドスコア**は `P1  1 - 0  P2` の形で常に画面中央に表示されます（プレイ中の HUD と
リザルト画面の両方）。先に `ROUNDS_TO_WIN`（既定 2 = 3 本勝負）に達した側がマッチを取ります。

**スコアはラウンドごとにリセット**されます（両者 0 から開始）が、ゲームは各ラウンドの
記録を保持しており、マッチ終了時に合計を出します。

### MVP = スコア × 生き残った HP

各ラウンドの終了時に、ゲームはプレイヤーごとに 2 つを記録します。**そのラウンドで稼いだ
スコア**と、**終了時に残っていた HP** です。そしてこの 2 つを掛け合わせます:

```
ラウンド MVP = そのラウンドのスコア × 残り HP
マッチ MVP   = 全ラウンドの合計
```

要点は、**ノックアウトされたラウンド（HP = 0）は MVP が 0 になる**ことです。どれだけ
スコアを稼いでいても `スコア × 0 = 0` です。500 稼いでから倒されれば、持ち帰るのは 0。
つまり「生き残ること」は「稼ぐこと」と同じ重みを持ちます。

| ラウンド | スコア | 残り HP | MVP |
|---|---|---|---|
| R1 | 400 | 3 | **1200** |
| R2 | 150 | 0（ノックアウト） | **0** |
| R3 | 300 | 0（ノックアウト） | **0** |
| 合計 | 850 | | **1200** |

### MVP が効くのはいつか — 同点の決着

**マッチ決定の優先順:**

1. **ラウンド勝利数** — 多い側が勝ち（例 2-1）。この場合 MVP は一切考慮されません。
2. **ラウンド数が同じ** → **マッチ MVP** が高い側の勝ち。
3. **MVP も同じ** → `A DRAWN MATCH`（マッチ引き分け）。

ラウンド数が並ぶのは、`MAX_ROUNDS`（= `ROUNDS_TO_WIN × 2 - 1` = 3）を消化しても
どちらも 2 に届かなかった場合です。1 勝ずつ + 引き分け 1 回（1 - 1）や、
3 ラウンドすべて引き分け（0 - 0）などです。

> `MAX_ROUNDS` は穴もふさいでいます。この上限が無いと、全ラウンドが引き分けのマッチは
> 誰も `ROUNDS_TO_WIN` に到達せず、永久に終わりません。

### リザルト画面は 2 種類

**1. ROUND OVER** — ラウンド終了、マッチはまだ続く

```
              ROUND 2 OVER
          P2 EMBER WINS THE ROUND

              P1  1 - 1  P2

           score x hp left = MVP
     P1  150 x 0 = 0      480 x 2 = 960  P2
        MVP so far    P1 1200    |    P2 960
          first to 2 rounds takes the match
       Press R for round 3     |     M for Menu
```

（`MVP so far` はラウンド 2 以降に表示されます。ラウンド 1 では上の行と同じ内容に
なるため出しません。）

**2. MATCH RESULT** — マッチ決着、全体のまとめ

```
                    MATCH RESULT
                P1 AQUA WINS THE MATCH

                   P1  1 - 1  P2

  ROUND   P1  score x hp = MVP   P2  score x hp = MVP   WON BY
  R1              400 x 3 = 1200          200 x 0 = 0     AQUA
  R2                150 x 0 = 0        480 x 2 = 960    EMBER
  R3                300 x 0 = 0          300 x 0 = 0      DRAW
  ---------------------------------------------------------------
  MVP TOTAL              1200                   960    MVP: P1

           raw points   P1 850   |   P2 980
       rounds level 1 - 1  ->  MVP decides the match
          Press R for a NEW MATCH  |  M for Menu
```

1 画面で全部分かります: **マッチの勝者** · **各ラウンドのスコア × HP（掛け算を明示）** ·
**マッチ MVP** · **素点合計**（`raw points`）· そして最下段が何で決まったかを示します。

> 上の例はまさに MVP が働いた場面です。ラウンドは 1-1 で並び、素点では P2 が
> 980 対 850 でリードしています。しかし P2 が生き残ったのは 1 ラウンドだけなので
> MVP は 960。P1 は大きく稼いだラウンドを生き延びて 1200 — **P1 の勝ち**です。
> この仕様がコアゲームに合う理由がここにあります。稼ぐだけでは足りず、
> 立っていなければならないのです。

| R を押す場面 | 動作 |
|---|---|
| ROUND OVER 画面 | 次のラウンドへ。**ラウンドスコアと MVP 明細を持ち越し** |
| MATCH RESULT 画面 | `0 - 0` から新しいマッチを開始（明細はクリア） |
| プレイ中 | 何も起きません（誤操作でラウンドを消さないため） |

`M` でメニューに戻るとそのマッチは破棄され、次は新しいマッチになります。DRAW は
どちらにも加算されませんが、明細には記録されます（`WON BY` = `DRAW`）。

---

## 8. バランス調整

| 変えたいもの | ファイル | 見出し |
|---|---|---|
| フォント · ウィンドウアイコン · ウィンドウサイズ | `config.py` | Section 3A |
| **ゲーム内の全ての色**（背景・壁・障害物・文字・カード・ボタン） | `config.py` | **Section 3A2 THEME** |
| アリーナサイズ、速度、HP、スコア、スタン時間、障害物、サウンド | `config.py` | Section 3B-3E |
| キャラクター: 色 + スプライトのパレット | `config.py` | Section 3F |
| パワー: 効果・コスト・持続・アイコン・説明文 | `config.py` | Section 3G |
| モード固有の HUD / ハート / ゲージの位置 | `solo.py` / `battle.py` | Section 3 |
| 蛇のスポーン地点 | `battle.py` | Section 3 の `SPAWN` |

**よく触る値**

```python
SCORE_TRANSFER      = 0.5   # 頭と頭の衝突で譲渡される割合（0 = なし、1.0 = 全部）
                            # ゲーム内でスコアが移動する唯一の場所
ROUNDS_TO_WIN       = 2     # マッチを取るのに必要なラウンド数（2 = 3 本勝負）
MAX_ROUNDS          = ROUNDS_TO_WIN * 2 - 1   # ラウンド上限。自動計算なので触らない
TARGET_SCORE        = 500   # 到達した時点でラウンド勝利になるスコア
MAX_HP              = 3
SELF_HIT_DAMAGE     = 1     # 自分の胴体に当たったときに減る HP（0 でスタンのみ）
WALL_MARGIN         = 10    # 頭が壁に埋まるのを防ぐ = スプライトの半分
SLOT_COLOR          = {'P1': 'mediumseagreen', 'P2': 'steelblue'}
```

**コアゲームの強さを調整する**

| やりたいこと | 変える値 |
|---|---|
| 頭と頭の痛みを増やす | `SCORE_TRANSFER` を上げる（1.0 でスコア全部） |
| スコアを一切動かさない | `SCORE_TRANSFER = 0.0`（HP のみ減る） |
| 噛みつきにもスコア減点を付ける | `resolve_bite()` の `punish(biter)` の後に減点を足す |
| 5 本勝負にする | `ROUNDS_TO_WIN = 3`（`MAX_ROUNDS` は 5 に追従） |
| MVP で HP を無視する（素点に戻す） | `screens.py` の `mvp_total()` を `sum(r[slot] for r in rounds)` にする |
| 同点時だけでなく常に MVP で決める | `match_champion()` のラウンド判定を外し、MVP 比較だけにする |
| ラウンドを短くする | `TARGET_SCORE` か `MAX_HP` を下げる |

定数はモードファイルに重複していません。`config.py` を 1 か所直せば両モードに反映されます。

---

## 9. 自分の画像と音を使う

### 9.1 自分の `.gif` を入れる（make_sprites.py の実行は不要）

次の名前で `assets/` に置けば、ゲームがそのまま使います。**コードの変更は不要**です。
`<key>` は `config.py` Section 3F の `p1` `p2` `p3` `p4` です。

| ファイル | 現在のサイズ | 備考 |
|---|---|---|
| `<key>_head_up.gif` `_down` `_left` `_right` | 20×20 | **4 方向すべて必要** |
| `<key>_head_up_ghost.gif`（+ 残り 3 方向） | 20×20 | CLOAK 中の頭 |
| `<key>_body.gif` | 16×16 | 1 節。繰り返しスタンプされます |
| `heart_full.gif` / `heart_empty.gif` | 18×18 | HP のハート |
| `fruit.gif` | 16×16 | フルーツ |

**回避できない制約**（ゲームではなく turtle の制限です）

- **GIF** であること — `.png` でも可: `load_shape()` が一度だけ `.gif` に変換します
  （Pillow が必要）
- **turtle は画像を回転できない**ため、頭は 4 ファイルに分かれています
- **turtle は画像を拡大縮小できない** → **ファイルのピクセルサイズがそのままゲーム内サイズ**
  です。`shapesize()` は効きません。大きな蛇にしたいならファイルを大きく作ってください。
- GIF の透過は**オン/オフのみ**。半透明の縁は作れません
- ファイルが無い・壊れていても致命的ではありません。その部分だけ色付きの四角に戻ります
- `config.py` の `USE_SPRITES = False` で全体を色付きの四角に強制できます

### 9.2 胴体の色は自分で変えられる？ できます — body の gif を入れなければ

**turtle は画像に色を塗れません。** `.gif` は Tk の image item であり、`color()` は
一切効きません。つまり `<key>_body.gif` を入れると、その色は**ファイルに焼き込まれ**、
`config.py` からは変更できません。

そのため頭と胴体は**別々に**判定されます。組み合わせは 4 通り:

| head gif | body gif | 結果 |
|---|---|---|
| ✅ | ✅ | 頭も胴体も自分の画像 — 色はファイル側 |
| ✅ | ❌ | **頭は自分の画像、胴体は `config.py` の色付き四角** ← これ |
| ❌ | ✅ | 胴体は画像、頭は色付き四角 |
| ❌ | ❌ | 全部色付き四角 |

> **つまり:** 手描きの頭を使いつつ胴体の色をコードで管理したいなら、
> **`<key>_head_*.gif` だけを入れて `<key>_body.gif` は置かないこと。**
> 胴体はそのキャラクターの `main` 色を使うので、画像を触らずに `config.py` で変えられます。

4 通りすべてテスト済みで、エラーなく描画されます。

> 補足: `<key>_body_ghost.gif` は**使われていません**。CLOAK はゴーストの胴体に
> 差し替えるのではなく胴体を完全に隠すためです。このファイルに手間をかける必要はありません。

### 9.3 自分の音を使う

完全な手順は**第 6 章**を見てください。要点だけ言えば、イベント名（`eat` `hit` `bump`
`power` `win` `lose` `select` `start`）で `.wav` を `assets/sounds/` に置くだけです。
一部だけでも構いませんし、インストールも不要です。

---

## 9.4 フォントを変える

`config.py` の `FONT_CANDIDATES` は単一の名前ではなく**リスト**です。tkinter は指定した
フォントが無いと黙って別のフォントに差し替えるため、実際に何が使われたのか分からないから
です。`engine.py` は Tk にどのフォントファミリが存在するかを問い合わせ、
**そのマシンに実際にある最初の名前**を選びます。

```python
FONT_CANDIDATES = ['Consolas', 'Cascadia Mono', 'Courier New',
                   'DejaVu Sans Mono', 'Liberation Mono', 'Courier']
```

使いたいフォントを先頭に置き、末尾には汎用の等幅フォントを保険として残してください。
1 つのリストで Windows でも Linux でも動きます（Windows では Consolas、Linux では
DejaVu が選ばれます）。

## 9.5 ウィンドウアイコンを変える（tkinter の羽根マークを差し替える）

次のいずれかの名前でロゴを `assets/` に置いてください。**最初に見つかったファイルが
使われます**:

```python
WINDOW_ICON = ['icon.png', 'icon.gif', 'logo.png', 'logo.gif', 'icon.ico']
```

| 拡張子 | 動作環境 | 備考 |
|---|---|---|
| `.png` `.gif` | **全 OS**（Tk 8.6+） | 推奨。`iconphoto` 経由 |
| `.ico` | **Windows のみ** | `iconbitmap` 経由 — Linux/Tk は受け付けません |

32×32 か 64×64 が適切です。ファイルが無ければ tkinter の既定アイコンがそのまま残るだけで、
エラーにはなりません。

---

## 10. 技術メモ（turtle には罠が多い）

どれも実際にバグとして時間を取られたものです。再発しないよう残しています:

- **shape turtle は必ず文字の上に来ます。** turtle は毎フレーム `tag_raise` で
  カーソルを再描画するため、生成順に関係なくペンの描画や `write()` の文字より上に
  浮きます。文字を上に置きたいものはペンで描き（`engine.filled_rect`）、クリックは
  座標判定にします（`wn.onscreenclick` + `engine.inside_rect`）。
- **`onclick()` は複数コンポーネントの compound shape では機能しません。**
  そこでは `turtle.turtle._item` が LIST になるため `tag_bind` が何にもマッチしません。
  座標で判定してください。
- **shape は `heading - 90` だけ回転します。** turtle の組み込み shape が上向きで
  定義されているためです。`engine.py` の shape は画面座標で定義しているので、
  heading 90 を設定する `engine.shape_turtle()` を通して表示します。
- **シーン切替では turtle を破棄しなければなりません。** `hideturtle()` では不十分で、
  canvas item（`items`、`stampItems`、`drawingLineItem`、`_fillitem`、そして compound
  shape では LIST になるカーソル）を削除し、turtle を登録解除する必要があります。
  さもないとシーンを切り替えるたびにリークします。`engine.clear_all_turtles()` が
  これを行います。
- **image shape は GIF のみ**、回転も拡大縮小もできず、**色も塗れません**
  （`color()` は Tk の image item に効きません）。だから色は画像側にあります — 9.2 参照。
- **`addshape()` は `TurtleGraphicsError` ではなく `tkinter.TclError` を投げます。**
  壊れた GIF や `.gif` にリネームした `.png` の場合です。`TurtleGraphicsError` だけを
  捕まえていたため不正なスプライトでシーン全体がクラッシュし、キャッシュも書かれないので
  リトライしても毎回クラッシュしました。現在 `load_shape()` は広く捕まえて失敗を
  キャッシュします。
- **自傷判定には猶予が必要**です。無いと毎フレーム再発します。第 7 章を参照。
- **頭は最後にスタンプ**します。canvas item は生成順を保持するためです。
- **胴体の節は path を逆向きに辿って距離を積算**して配置します。フレーム数のオフセット
  ではありません。さもないと SPEED 中に胴体が伸びて離れてしまいます。
- **スプライトは中心を基準に描かれます。** 頭の*中心*がアリーナの端まで行けるようにすると
  スプライトの半分が壁に埋まりました（実測でちょうど 10 px、20×20 の頭の半分）。
  そのための `WALL_MARGIN` です。
- **tkinter はフォントを黙って差し替えます。** 選ぶ前に `tkinter.font.families()` で
  実際に存在するものを確認してください — `engine._pick_font()` がやっています。
