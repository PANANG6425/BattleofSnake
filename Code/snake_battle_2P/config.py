"""
config.py - every tunable value in one place.

This module imports NOTHING from the game, so it can be imported from anywhere
without creating an import cycle. Change a number here and rerun the game.
"""

# ===========================================
# WINDOW & ARENA
# ===========================================
WIN_W, WIN_H = 800, 600                         # Window size in pixels
BG_COLOR = 'black'                              # Arena background color
TITLE = 'Snake Battle - Local Multiplayer (P1: WASD | P2: Arrow Keys)' # Window title

ARENA_L, ARENA_R = -375, 375                    # Left / right inner limits of the playfield
ARENA_B, ARENA_T = -275, 205                    # Bottom / top inner limits of the playfield
# The strip above ARENA_T (y 210..280) is reserved for the stats panel, so snakes
# and fruits can never wander behind the hearts, score or skill bars.
BORDER_TOP = 210                                # Y position where the arena wall is drawn
BORDER_BOTTOM = -280                            # Y position of the bottom wall
BORDER_L, BORDER_R = -380, 380                  # X positions of the side walls

FRAME_MS = 16                                   # Milliseconds per frame (16 ms is about 60 FPS)

# ===========================================
# MOVEMENT
# ===========================================
BASE_SPEED = 3                                  # Default movement speed in pixels per frame
BOOST_SPEED = 6                                 # Movement speed while Speed Boost is active
SEG_SPACING = 15                                # Distance in pixels between body segments
START_LENGTH = 4                                # Body segments each snake starts with
GROW_PER_FRUIT = 1                              # Body segments gained per fruit

OPPOSITE = {'up': 'down', 'down': 'up',         # Lookup used to block instant 180-degree turns
            'left': 'right', 'right': 'left'}

# ===========================================
# COMBAT & SCORING
# ===========================================
MAX_HP = 3                                      # Starting hearts per player
TARGET_SCORE = 500                              # Score that wins the match instantly
FRUIT_SCORE = 100                               # Score per fruit
SCORE_PENALTY = 0.5                             # Score multiplier when hit (-50%)
FRUIT_COUNT = 2                                 # Fruits on the field at any time

HIT_RADIUS = 12                                 # Pixel distance treated as a collision
SELF_HIT_RADIUS = 10                            # Slightly tighter radius for running into yourself
SELF_SKIP_SEGMENTS = 3                          # Segments right behind the head that cannot be bitten

STUN_FRAMES = 30                                # Frames frozen after a bump or a hit
INVULN_FRAMES = 60                              # Immunity frames after taking damage
BUMP_COOLDOWN = 45                              # Frames before a wall/obstacle can stun the same snake again
SELF_HIT_COOLDOWN = 45                          # Frames before biting yourself can stun again
# Both cooldowns MUST be larger than STUN_FRAMES. That gap (45 - 30 = 15 frames,
# about 45 px of travel) is what guarantees a snake always escapes whatever it is
# overlapping instead of being re-stunned on the very frame its stun ends.

# ===========================================
# SKILLS
# ===========================================
SKILL_MAX = 100                                 # Full skill bar value
SKILL_GAIN = 25                                 # Skill bar gained per fruit
SKILL_COST = 50                                 # Skill bar spent per activation
SKILL_FRAMES = 180                              # Skill duration in frames (about 3 seconds)

# ===========================================
# OBSTACLES
# ===========================================
OBSTACLE_COUNT = 6                              # Number of obstacle boxes
OBSTACLE_SIZE = 60                              # Width / height of each box
OBSTACLE_PAD = 6                                # Extra pixels around a box that already count as a hit
OBSTACLE_SPOTS = [(-200, 65), (0, 65), (200, 65),      # Symmetric layout: neither player gets a better spawn
                  (-200, -135), (0, -135), (200, -135)] # Leaves a clear corridor at y = -35
OBSTACLE_EDGE = '#5a5a6e'                       # Obstacle outline color
OBSTACLE_FILL = '#2b2b3a'                       # Obstacle fill color
WALL_COLOR = 'gray'                             # Arena wall color

# ===========================================
# PLAYERS
# ===========================================
# (name, sprite key, main color, cloak color, spawn position, spawn direction)
PLAYER_SETUP = [
    ('P1', 'p1', '#22e0e0', '#0d3a3a', (-250, -35), 'right'), # Player 1 - WASD
    ('P2', 'p2', '#ffa22a', '#3a260d', (250, -35), 'left'),   # Player 2 - Arrow keys
]

# ===========================================
# HUD
# ===========================================
HEART_Y = 250                                   # Vertical center of the heart icon row
HEART_STEP = 22                                 # Horizontal spacing between heart icons
BAR_W, BAR_H = 132, 12                          # Skill bar size
BAR_Y = 224                                     # Skill bar baseline
BAR_FRAME = '#5a5a6b'                           # Skill bar frame color
HINT_COLOR = '#4a4a4a'                          # Bottom control hint color
FONT = 'Courier'                                # Font family used everywhere

# Stun bar floating above each snake's head
STUN_BAR_W = 26                                 # Stun bar width
STUN_BAR_H = 5                                  # Stun bar height
STUN_BAR_LIFT = 20                              # Pixels above the head
STUN_BAR_FILL = '#ffd23f'                        # Stun bar fill color (amber)
STUN_BAR_BG = '#3a3a46'                          # Stun bar empty color

# ===========================================
# EFFECTS
# ===========================================
FX_MAX = 220                                    # Hard cap on live particles (keeps the frame rate stable)
FX_EAT_COUNT = 12                               # Particles per fruit pickup
FX_HIT_COUNT = 18                               # Particles per damage hit
FX_BUMP_COUNT = 8                               # Particles per wall / obstacle bump
FX_SKILL_COUNT = 16                             # Particles per skill activation
FX_LIFE = 20                                    # Frames a particle lives
FX_GRAVITY = 0.0                                # Downward pull per frame (0 = float freely)

# ===========================================
# SOUND
# ===========================================
SOUND_ON = True                                 # Set False to start muted (M toggles in game)
SOUND_DIR = 'sounds'                            # Subfolder of assets/ holding the .wav files
SOUND_VOLUME = 0.6                              # 0.0 - 1.0, only applied by the pygame backend

# ===========================================
# ASSETS
# ===========================================
ASSET_DIR = 'assets'                            # Folder holding sprites and sounds
USE_SPRITES = True                              # False forces the plain colored-square look
