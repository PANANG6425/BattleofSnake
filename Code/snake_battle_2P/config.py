"""
config.py - SECTION 3: Parameters & Physics (for the whole game)

Every tunable number lives here, plus the two registries that make the game
extensible without touching game code:

    CHARACTERS  a skin: colour + sprite palette. Never affects balance.
    POWERS      one power per player per match: cost, duration, effect.

Nothing in this file imports anything, so it is safe to import from anywhere.
"""

# ===========================================
# SECTION 3A: SCREEN & TIMING
# ===========================================
WIN_W, WIN_H = 800, 600
TITLE = 'Snake Game'
FRAME_MS = 16                                   # ~60 FPS

ASSET_DIR = 'assets'
USE_SPRITES = True                              # False forces plain coloured squares

# Font: the FIRST name actually installed wins, so one list works on every machine.
# engine.py resolves it at startup and exports the winner as engine.FONT.
# Put your preferred font first; keep a generic monospace last as the safety net.
FONT_CANDIDATES = ['Consolas', 'Cascadia Mono', 'Courier New', 'DejaVu Sans Mono',
                   'Liberation Mono', 'Courier']

# Window icon, replacing tkinter's feather. First file found in assets/ wins.
# .png / .gif work everywhere (Tk 8.6+); .ico only on Windows. Drop your logo in
# assets/ under one of these names - if none exist the default feather stays.
WINDOW_ICON = ['icon.png', 'icon.gif', 'logo.png', 'logo.gif', 'icon.ico']

# ===========================================
# SECTION 3A2: THEME - every colour in one place
# ===========================================
BG_COLOR = 'black'                              # Arena background
BG_MENU = '#0b0f14'                             # Menu / Character Select background

WALL_COLOR = 'gray'                             # Arena border
OBSTACLE_FILL = '#2b2b3a'
OBSTACLE_EDGE = '#5a5a6e'

BAR_FRAME = '#5a5a6b'                           # Skill bar outline
TEXT_BRIGHT = 'white'
TEXT_MUTED = '#8a93a3'
TEXT_FAINT = '#4a4a4a'
TEXT_TAG = '#dddddd'                            # BOOST / CLOAK / STUN labels
TEXT_DIM = 'gray'                               # "FIRST TO 500", result hints
HIGHLIGHT = 'gold'                              # Selected power, PRESS ENTER

PANEL_BG = '#141b24'                            # Character Select panel
CARD_BG = '#0e141b'                             # Character card interior
CARD_EDGE = '#39424f'                           # Unselected outline
ARROW_COLOR = '#c7ccd4'                         # Flip arrows
BUTTON_FILL = '#1b2430'                         # Menu buttons
SLOT_COLOR = {'P1': 'mediumseagreen', 'P2': 'steelblue'}

# ===========================================
# SECTION 3B: SHARED GAMEPLAY (both modes)
# ===========================================
SEG_SPACING = 15                                # Pixels between body segment centres
WALL_MARGIN = 10                                # Half the head sprite: stops the snake
                                                # sinking into the border wall
START_LENGTH = 4
GROW_PER_FRUIT = 1
FRUIT_SCORE = 50
SKILL_MAX = 100

# Fruit skins. Purely cosmetic - every one is worth FRUIT_SCORE - and each respawn
# picks a fresh one at random. Names are assets/<name>.gif, written by
# import_assets.py from the drawings in ../../Asset/. Whichever files are missing
# are simply not offered; with none of them present the game falls back to
# assets/fruit.gif, and without that to a red circle.
FRUIT_VARIANTS = ['fruit_apple', 'fruit_banana', 'fruit_grape',
                  'fruit_guava', 'fruit_pineapple']

# ===========================================
# SECTION 3C: 1P MODE
# ===========================================
ARENA_1P = (-380, 380, -280, 235)               # left, right, bottom, top
                                                # top leaves room for the HUD bar
SPEED_1P = 4
SKILL_GAIN_1P = 20

# ===========================================
# SECTION 3D: 2P BATTLE MODE
# ===========================================
ARENA_2P = (-375, 375, -275, 205)               # Lower top edge: the HUD sits above it
SPEED_2P = 3                                    # Slower - two snakes share one arena
SKILL_GAIN_2P = 25

MAX_HP = 3
TARGET_SCORE = 800
ROUNDS_TO_WIN = 2                               # Rounds to take the match (best of 3)
MAX_ROUNDS = ROUNDS_TO_WIN * 2 - 1              # Hard stop: a match of all draws would
                                                # otherwise never reach ROUNDS_TO_WIN.
                                                # Level on rounds here -> MVP decides,
                                                # see screens.py match_champion()

# Every heart still standing at the end of a round is worth this much MVP on its own,
# so winning a round on hearts is never worth nothing even at a low score. MVP is
# score x hp + SURVIVE_BONUS x hp - see screens.py mvp_total().
SURVIVE_BONUS = 100

# --- The one place score changes hands --------------------------------------
# Collisions cost HEARTS, never points - except a head-to-head clash, where the snake
# that is AHEAD loses a heart and hands this share of its score to the snake behind.
# That is the whole reason to protect a lead by baiting instead of charging.
SCORE_TRANSFER = 0.5                            # 0.0 = no transfer, 1.0 = the lot

SELF_HIT_DAMAGE = 1                             # HP lost for running into your own body
                                                # (0 = stun only, the old behaviour)
STUN_FRAMES = 30                                # Frozen frames after a bump or self hit
SELF_HIT_GRACE_EXTRA = 40                       # Extra frames a self hit cannot retrigger
INVULN_FRAMES = 60                              # Immunity frames after taking damage
HIT_RADIUS = 12

OBSTACLE_COUNT = 6
OBSTACLE_SIZE = 60
OBSTACLE_SPOTS = [(-200, 65), (0, 65), (200, 65),
                  (-200, -135), (0, -135), (200, -135)]   # Symmetric 3x2 grid

FRUIT_COUNT_2P = 2
FRUIT_MIN_GAP = 40                              # Keep fruits apart

# ===========================================
# SECTION 3E: SOUND (see engine.py - no audio is generated, files are optional)
# ===========================================
SOUND_ON = True                                 # X toggles in game
SOUND_DIR = 'sounds'                            # Subfolder of assets/ for .wav files
SOUND_VOLUME = 0.6                              # Only applied by the pygame backend
# Extra folders to search after assets/sounds/, relative to the code folder. The
# repo ships its .mp3 pack two levels up; change this if you move things.
EXTRA_SOUND_DIRS = ['../../sound_effect']
SOUND_DEBUG = False                             # True prints every playback failure

# ===========================================
# SECTION 3F: CHARACTER REGISTRY
# ===========================================
# All characters play IDENTICALLY - colour only. `key` is also the sprite filename
# prefix, so character 'p3' loads assets/p3_head_up.gif and assets/p3_body.gif.
# `palette` is (main, dark outline, light highlight, ghost main, ghost outline) and is
# used only to GENERATE sprites; `main` / `dim` are what the game draws with when a
# sprite file is missing. To add one: append an entry, run make_sprites.py.
# The roster is the two hand-drawn snakes, each in two colourways. Every one has a
# portrait at assets/<key>_portrait.gif; import_assets.PORTRAIT_ART decides which
# drawing and which hue rotation produces each, and `main` here is that costume's
# dominant colour so the arena sprite matches the card the player picked.
# Character Select falls back to the drawn head if a portrait file is missing, so
# nothing below depends on the art existing.
CHARACTERS = [
    {'key': 'p1', 'name': 'SIAM',   'main': '#e03131', 'dim': '#3f1010',   # Thai, red
     'palette': ('#e03131', '#7a1414', '#ffd0c0', '#4a1616', '#280b0b')},
    {'key': 'p2', 'name': 'SAKURA', 'main': '#4d6bff', 'dim': '#1b2450',   # Japan, blue
     'palette': ('#4d6bff', '#1b2f9a', '#cdd8ff', '#1f2a5e', '#111735')},
    {'key': 'p3', 'name': 'NAGA',   'main': '#2fd45a', 'dim': '#0f3a1c',   # Thai, green
     'palette': ('#2fd45a', '#12722c', '#c8ffd6', '#123d1e', '#0a2412')},
    {'key': 'p4', 'name': 'KOI',    'main': '#e04ce8', 'dim': '#3c0f40',   # Japan, magenta
     'palette': ('#e04ce8', '#7a1580', '#ffcdff', '#3f1044', '#240926')},
]
CHAR_DEFAULTS = ('p1', 'p2')                    # Pre-selected for P1 and P2:
                                                # Thai vs Japan, one of each drawing

# ===========================================
# SECTION 3G: POWER REGISTRY
# ===========================================
# `effect` IS the behaviour, written as EFFECT KINDS the game already applies:
#
#     speed_mult   float   head speed multiplier      (max of active)
#     score_mult   float   fruit score multiplier     (max of active)
#     cloak        bool    body hidden, head goes ghost
#     invincible   bool    incoming damage ignored
#     noclip       bool    obstacles and own body stop hurting
#
# A new power reusing these kinds is data only - append an entry, give it an icon,
# done. A genuinely new kind needs the key here plus one read via powers_flag() /
# powers_effect() at the one place that should honour it. Nothing hardcodes a name.
POWERS = [
    {'key': 'SPEED',   'name': 'SPEED',   'tag': 'SPD', 'hud': 'BOOST',
     'icon': 'speed_icon',   'blurb': 'Move twice as fast',
     'cost': 50, 'duration': 180, 'effect': {'speed_mult': 2.0}},
    {'key': 'STEALTH', 'name': 'STEALTH', 'tag': 'STL', 'hud': 'CLOAK',
     'icon': 'stealth_icon', 'blurb': 'Body vanishes, still solid',
     'cost': 50, 'duration': 180, 'effect': {'cloak': True}},
    {'key': 'SHIELD',  'name': 'SHIELD',  'tag': 'SHD', 'hud': 'SHIELD',
     'icon': 'shield_icon',  'blurb': 'Take no damage at all',
     'cost': 50, 'duration': 150, 'effect': {'invincible': True}},
    {'key': 'PHASE',   'name': 'PHASE',   'tag': 'PHS', 'hud': 'PHASE',
     'icon': 'phase_icon',   'blurb': 'Slip through boxes and your own tail',
     'cost': 50, 'duration': 150, 'effect': {'noclip': True}},
    {'key': 'FEAST',   'name': 'FEAST',   'tag': 'FST', 'hud': 'FEAST',
     'icon': 'feast_icon',   'blurb': 'Fruit is worth double',
     'cost': 40, 'duration': 240, 'effect': {'score_mult': 2.0}},
]
POWER_DEFAULTS = ('SPEED', 'STEALTH')           # Pre-selected for P1 and P2

# ===========================================
# SECTION 3H: LOOKUPS
# ===========================================
_CHAR_BY_KEY = {c['key']: c for c in CHARACTERS}
_POWER_BY_KEY = {p['key']: p for p in POWERS}


def character(key):
    """Look up a character, falling back to the first one for a bad key."""
    return _CHAR_BY_KEY.get(key, CHARACTERS[0])


def power(key):
    """Look up a power, falling back to the first one for a bad key."""
    return _POWER_BY_KEY.get(key, POWERS[0])
