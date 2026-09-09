"""
game_config.py - every tunable number, in one place.

Before this file, snake_1p.py and snake_2p.py each declared their own BASE_SPEED /
MAX_HP / SKILL_GAIN / ... *inside* their scene function, so a balance change meant
finding and editing the same value twice. Tune here instead.

What lives where:
    game_config.py  arena, speeds, HP, scoring, timing, sound settings
    powers.py       the power registry, and each power's cost / duration / effect
    characters.py   the roster, and each character's colours / sprite palette

Nothing in this file imports anything, so it is safe to import from anywhere.
"""

# ===========================================
# WINDOW
# ===========================================
WIN_W, WIN_H = 800, 600                         # Window size in pixels
BG_COLOR = 'black'                              # Arena background
TITLE = 'Snake Game'                            # Window title on the menu
FONT = 'Courier'                                # Font family used everywhere
FRAME_MS = 16                                   # Milliseconds per frame (~60 FPS)

ASSET_DIR = 'assets'                            # Folder holding sprites and sounds
USE_SPRITES = True                              # False forces the plain colored-square look

# ===========================================
# SHARED GAMEPLAY (both modes)
# ===========================================
SEG_SPACING = 15                                # Pixels between body segment centers
START_LENGTH = 4                                # Body segments at the start of a life
GROW_PER_FRUIT = 1                              # Segments gained per fruit
FRUIT_SCORE = 100                               # Base score per fruit
SKILL_MAX = 100                                 # Full skill bar

# ===========================================
# 1P MODE
# ===========================================
ARENA_1P = (-380, 380, -280, 260)               # left, right, bottom, top
SPEED_1P = 4                                    # Pixels per frame
SKILL_GAIN_1P = 20                              # Bar gained per fruit

# ===========================================
# 2P BATTLE MODE
# ===========================================
ARENA_2P = (-375, 375, -275, 205)               # Lower top edge: the HUD sits above it
SPEED_2P = 3                                    # Slower than 1P - two snakes, one arena
SKILL_GAIN_2P = 25                              # Bar gained per fruit

MAX_HP = 3                                      # Starting hearts per player
TARGET_SCORE = 500                              # Score that wins the match instantly
SCORE_PENALTY = 0.5                             # Score multiplier applied when you take a hit

STUN_FRAMES = 30                                # Frozen frames after a bump or self hit
SELF_HIT_GRACE_EXTRA = 40                       # Extra frames a self hit cannot retrigger
INVULN_FRAMES = 60                              # Immunity frames after taking damage
HIT_RADIUS = 12                                 # Distance counted as a collision

OBSTACLE_COUNT = 6                              # Boxes in the arena
OBSTACLE_SIZE = 60                              # Box side length in pixels
OBSTACLE_SPOTS = [(-200, 65), (0, 65), (200, 65),
                  (-200, -135), (0, -135), (200, -135)]   # Fixed symmetric 3x2 grid

FRUIT_COUNT_2P = 2                              # Fruits on the field at once
FRUIT_MIN_GAP = 40                              # Keep fruits this far apart

# ===========================================
# SOUND (see audio.py - no audio is generated, files are optional)
# ===========================================
SOUND_ON = True                                 # Start unmuted (X toggles in game)
SOUND_DIR = 'sounds'                            # Subfolder of assets/ holding .wav files
SOUND_VOLUME = 0.6                              # 0.0 - 1.0, applied by the pygame backend
