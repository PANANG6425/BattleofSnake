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
FRUIT_SCORE = 100
SKILL_MAX = 100

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
TARGET_SCORE = 500
ROUNDS_TO_WIN = 2                               # Rounds to take the match (best of 3)

# --- Scoring on a knockdown -------------------------------------------------
# The core loop is: eat fruit, PROTECT your score, and bait the enemy into biting
# you - because biting costs the BITER, not the victim. So every knockdown moves
# score from the loser to the winner.
DEATH_SCORE_PENALTY = 50                        # Flat points lost per knockdown
SCORE_TRANSFER = 0.5                            # Share of the loser's remaining score
                                                # handed to the winner

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
CHARACTERS = [
    {'key': 'p1', 'name': 'AQUA',  'main': '#22e0e0', 'dim': '#0d3a3a',
     'palette': ('#22e0e0', '#0b6a6a', '#b6ffff', '#0e3d3d', '#082424')},
    {'key': 'p2', 'name': 'EMBER', 'main': '#ffa22a', 'dim': '#3a260d',
     'palette': ('#ffa22a', '#8a4a00', '#ffe0a8', '#4a2f0c', '#241705')},
    {'key': 'p3', 'name': 'VENOM', 'main': '#5ce65c', 'dim': '#123d12',
     'palette': ('#5ce65c', '#186b18', '#c9ffc9', '#123d12', '#0a240a')},
    {'key': 'p4', 'name': 'ROYAL', 'main': '#c86ef0', 'dim': '#341044',
     'palette': ('#c86ef0', '#5e1f7a', '#eecbff', '#341044', '#1d0926')},
]
CHAR_DEFAULTS = ('p1', 'p2')                    # Pre-selected for P1 and P2

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
