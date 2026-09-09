import turtle                                   # Import the turtle graphics module for drawing and window handling
import random                                   # Import random for fruit spawning and obstacle placement
import os                                       # Import os to locate the assets/ sprite folder next to this file

# ===========================================
# SECTION 1: SCREEN SETUP
# ===========================================
wn = turtle.Screen()                            # Create the main game window
wn.title('Snake Battle - Local Multiplayer (P1: WASD | P2: Arrow Keys)') # Set title displayed on window title bar
wn.bgcolor('black')                             # Set background color of window to black
wn.setup(width=800, height=600)                 # Set window dimensions (width = 800px, height = 600px)
wn.tracer(0)                                    # Turn off auto screen updates to enable smooth frame rendering

game_active = True                              # Loop control flag (True: game is active, False: match finished)

# ===========================================
# SECTION 2: TUNING PARAMETERS
# ===========================================
ARENA_L, ARENA_R = -375, 375                    # Left / right inner limits of the playfield in pixels
ARENA_B, ARENA_T = -275, 205                    # Bottom / top inner limits of the playfield in pixels
# The strip above ARENA_T (y 210..280) is reserved for the stats panel, so snakes and
# fruits can never wander behind the hearts, score or skill bars.

BASE_SPEED = 3                                  # Default movement speed in pixels per frame
BOOST_SPEED = 6                                 # Movement speed while the Speed Boost skill is active
SEG_SPACING = 15                                # Distance in pixels between consecutive body segments
START_LENGTH = 4                                # Number of body segments each snake starts with
GROW_PER_FRUIT = 1                              # Body segments gained per fruit eaten

MAX_HP = 3                                      # Starting hearts per player
TARGET_SCORE = 500                              # Score needed to win the match instantly
FRUIT_SCORE = 100                               # Score awarded per fruit
SCORE_PENALTY = 0.5                             # Multiplier applied to score when a player takes a hit (-50%)

SKILL_MAX = 100                                 # Full skill bar value
SKILL_GAIN = 25                                 # Skill bar gained per fruit eaten
SKILL_COST = 50                                 # Skill bar consumed per skill activation
SKILL_FRAMES = 180                              # Skill duration in frames (~3 seconds at 60 FPS)

STUN_FRAMES = 30                                # Frames a snake is frozen after an obstacle / wall bump or a hit
INVULN_FRAMES = 60                              # Frames of immunity after taking damage (prevents multi-hit chains)
HIT_RADIUS = 12                                 # Pixel distance treated as a collision between two entities
OBSTACLE_COUNT = 6                              # Number of turtle-drawn obstacle boxes in the arena
OBSTACLE_SIZE = 60                              # Width / height of each square obstacle box in pixels

# ===========================================
# SECTION 2B: SPRITE LOADING (assets/*.gif)
# ===========================================
# turtle can only register image shapes from GIF files and it cannot rotate or scale them,
# which is why every snake ships one sprite per facing direction. Run make_sprites.py to
# (re)generate the whole set, or drop your own art into assets/ using the same file names.
USE_SPRITES = True                              # Set to False to force the original plain-square look
ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets') # Sprite folder next to this file

def load_shape(name):                           # Register one sprite with turtle and return its shape name
    if not USE_SPRITES:                         # Sprites disabled -> caller falls back to plain squares
        return None
    gif_path = os.path.join(ASSET_DIR, name + '.gif') # Expected GIF path for this sprite
    if not os.path.isfile(gif_path):            # No GIF yet: try converting a same-named PNG once
        png_path = os.path.join(ASSET_DIR, name + '.png') # Optional PNG drop-in from your artist
        if os.path.isfile(png_path):            # A PNG exists, so convert it to the GIF turtle needs
            try:
                from PIL import Image, ImageOps # Pillow is only needed for this optional conversion
                src = Image.open(png_path).convert('RGBA') # Load the PNG with its alpha channel
                alpha = src.split()[3].point(lambda v: 255 if v > 128 else 0) # GIF alpha is on/off only
                pal = src.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255) # Leave index 255 free
                pal.paste(255, mask=ImageOps.invert(alpha)) # Flag transparent pixels with index 255
                pal.save(gif_path, transparency=255) # Save the GIF beside the PNG
            except Exception:                   # Pillow missing or the PNG is unreadable
                return None                     # Fall back to plain squares for this sprite
        else:                                   # Neither GIF nor PNG is present
            return None                         # Fall back to plain squares for this sprite
    try:
        wn.addshape(gif_path)                   # Register the GIF with the turtle shape table
        return gif_path                         # The registered name is the path itself
    except turtle.TurtleGraphicsError:          # Registration failed (corrupt or unsupported GIF)
        return None                             # Fall back to plain squares for this sprite

# ===========================================
# SECTION 3: ARENA BOUNDARIES (4 Outer Walls)
# ===========================================
border = turtle.Turtle()                        # Instantiate Turtle object for drawing arena boundaries
border.color('gray')                            # Set wall border color to gray
border.pensize(6)                               # Set line thickness of boundary walls to 6 pixels
border.penup()                                  # Lift pen to move to starting corner without drawing
border.goto(-380, 210)                          # Position pen at top-left corner of the arena (below the HUD strip)
border.pendown()                                # Lower pen to begin drawing outer walls
for _ in range(2):                              # Loop twice to draw two pairs of equal sides
    border.forward(760)                         # Draw top/bottom horizontal wall (width = 760px)
    border.right(90)                            # Turn pen right 90 degrees
    border.forward(490)                         # Draw right/left vertical wall (height = 490px)
    border.right(90)                            # Turn pen right 90 degrees
border.hideturtle()                             # Hide wall-drawing cursor graphics for clean look

# ===========================================
# SECTION 4: OBSTACLE BOXES (drawn with turtle)
# ===========================================
obstacle_pen = turtle.Turtle()                  # Dedicated Turtle object used only to draw obstacle boxes
obstacle_pen.hideturtle()                       # Hide the cursor so only the boxes are visible
obstacle_pen.penup()                            # Lift pen so repositioning never draws stray lines
obstacle_pen.color('#5a5a6e', '#2b2b3a')        # Outline color (light slate) and fill color (dark slate)
obstacle_pen.pensize(3)                         # Outline thickness of each obstacle box

obstacles = []                                  # Collision list of boxes as (left, bottom, right, top) tuples

def draw_obstacle_box(cx, cy, size):            # Draw one filled square obstacle centered on (cx, cy)
    half = size / 2                             # Half-size used to convert center point into corner point
    obstacle_pen.penup()                        # Lift pen before travelling to the box corner
    obstacle_pen.goto(cx - half, cy + half)     # Move to the top-left corner of the box
    obstacle_pen.setheading(0)                  # Face east so the square is drawn axis-aligned
    obstacle_pen.pendown()                      # Lower pen to start drawing the outline
    obstacle_pen.begin_fill()                   # Start recording the shape so it can be filled
    for _ in range(4):                          # Draw the four equal sides of the square
        obstacle_pen.forward(size)              # Draw one side of the box
        obstacle_pen.right(90)                  # Turn 90 degrees to start the next side
    obstacle_pen.end_fill()                     # Close and fill the recorded shape
    obstacle_pen.penup()                        # Lift pen again once the box is finished
    obstacles.append((cx - half, cy - half, cx + half, cy + half)) # Store bounding box for collision checks

def build_obstacles():                          # Place all obstacle boxes for a fresh match
    obstacle_pen.clear()                        # Erase previously drawn boxes (used when restarting)
    obstacles.clear()                           # Reset the collision list so old boxes stop blocking
    spots = [(-200, 65), (0, 65), (200, 65),    # Fixed, symmetric layout keeps the match fair for both players
             (-200, -135), (0, -135), (200, -135)] # Two rows, leaving a clear corridor at y = -35 for both spawns
    for cx, cy in spots[:OBSTACLE_COUNT]:       # Draw as many boxes as OBSTACLE_COUNT requests
        draw_obstacle_box(cx, cy, OBSTACLE_SIZE) # Render the box and register its collision bounds

def inside_obstacle(x, y, pad=0):               # Test whether a point falls inside any obstacle box
    for left, bottom, right, top in obstacles: # Check the point against every registered box
        if left - pad <= x <= right + pad and bottom - pad <= y <= top + pad: # Point within padded bounds?
            return True                         # Report a collision immediately
    return False                                # No obstacle contains this point

build_obstacles()                               # Draw the initial set of obstacle boxes

# ===========================================
# SECTION 5: SNAKE ENTITY (shared by both players)
# ===========================================
class Snake:                                    # One class instantiated twice: this is what makes the game multiplayer
    def __init__(self, name, key, color, dim_color, start_pos, start_dir):
        self.name = name                        # Display label shown in the HUD ("P1" / "P2")
        self.key = key                          # Sprite file prefix for this player ("p1" / "p2")
        self.color_main = color                 # Normal color of this snake (also the fallback square color)
        self.color_dim = dim_color              # Faint color used while the Invisibility skill is active
        self.start_pos = start_pos              # Spawn coordinates used on reset
        self.start_dir = start_dir              # Spawn facing direction used on reset

        # Sprite tables: one head image per facing direction, plus a faded "ghost" set for Invisibility
        self.head_sprites = {d: load_shape('{}_head_{}'.format(key, d))
                             for d in ('up', 'down', 'left', 'right')} # Normal head sprites
        self.ghost_sprites = {d: load_shape('{}_head_{}_ghost'.format(key, d))
                              for d in ('up', 'down', 'left', 'right')} # Cloaked head sprites
        self.body_sprite = load_shape('{}_body'.format(key)) # Normal body segment sprite
        self.use_sprites = all(self.head_sprites.values()) and self.body_sprite is not None # Every file loaded?

        self.head = turtle.Turtle()             # Turtle object representing the snake head
        self.head.penup()                       # Lift pen so the head never draws a trail line
        if self.use_sprites:                    # Sprite mode: start facing the spawn direction
            self.head.shape(self.head_sprites[start_dir]) # Apply the matching head image
        else:                                   # Fallback mode: the original plain square head
            self.head.shape('square')           # Set head shape to square
            self.head.color(color)              # Set head color to this player's color
            self.head.shapesize(0.8, 0.8)       # Scale head down to roughly 16x16 pixels

        self.stamper = turtle.Turtle()          # Single Turtle object reused to stamp every body segment
        self.stamper.penup()                    # Lift pen so stamping never draws lines
        if self.use_sprites:                    # Sprite mode: stamp the body image
            self.stamper.shape(self.body_sprite) # Apply the body segment image
        else:                                   # Fallback mode: the original plain square body
            self.stamper.shape('square')        # Body segments are squares as well
            self.stamper.color(color)           # Body segments share the player's color
            self.stamper.shapesize(0.65, 0.65)  # Slightly smaller than the head, leaving visible joints
        self.stamper.hideturtle()               # Hide the stamper itself; only its stamps are visible

        self.reset()                            # Initialize all per-match state values

    def reset(self):                            # Restore this snake to its starting match state
        self.head.goto(*self.start_pos)         # Teleport head back to its spawn point
        if not self.use_sprites:                # Plain-square fallback keeps using color changes
            self.head.color(self.color_main)    # Restore normal head color
        self.head.showturtle()                  # Make sure the head is visible again
        self.direction = self.start_dir         # Face the spawn direction
        self.facing = self.start_dir            # Last non-stop direction, used to pick the head sprite
        self.length = START_LENGTH              # Reset body length
        self.path = [self.start_pos]            # Path history used to position body segments
        self.hp = MAX_HP                        # Reset hearts
        self.score = 0                          # Reset score
        self.skill = 0                          # Reset skill bar to empty
        self.speed = BASE_SPEED                 # Reset movement speed
        self.stun = 0                           # Not stunned
        self.invuln = 0                         # Not currently immune
        self.boost_timer = 0                    # Speed Boost inactive
        self.invis_timer = 0                    # Invisibility inactive
        self.stamper.clearstamps()              # Remove leftover body stamps from the previous match

    def segments(self):                         # Compute body segment positions by walking the path history backwards
        points = []                             # Collected (x, y) coordinates, ordered head-side first
        target = SEG_SPACING                    # Distance behind the head where the next segment belongs
        travelled = 0.0                         # Distance accumulated so far while walking backwards
        prev = self.path[-1]                    # Start from the newest path point (the head position)
        for i in range(len(self.path) - 2, -1, -1): # Walk from the newest point towards the oldest
            cur = self.path[i]                  # The next older path point
            travelled += abs(cur[0] - prev[0]) + abs(cur[1] - prev[1]) # Movement is axis-aligned, so this is exact
            prev = cur                          # Advance the walk
            while travelled >= target and len(points) < self.length: # Passed the spot for one or more segments
                points.append(cur)              # Place a segment at this path point
                target += SEG_SPACING           # Move the goal further back for the following segment
            if len(points) >= self.length:      # Every segment has been placed
                break                           # Stop walking the history
        return points                           # Head-side segments first, tail last

    def turn(self, new_dir, opposite):          # Change direction while blocking instant 180-degree reversals
        if self.direction != opposite:          # Only allow the turn if it is not a direct reversal
            self.direction = new_dir            # Apply the new direction
            self.facing = new_dir               # Remember the facing so the head sprite matches

    def use_speed_boost(self):                  # Activate the Speed Boost skill
        if self.skill >= SKILL_COST and self.boost_timer == 0: # Require a charged bar and no boost already running
            self.skill -= SKILL_COST            # Spend skill bar
            self.boost_timer = SKILL_FRAMES     # Start the boost countdown

    def use_invisibility(self):                 # Activate the Invisibility skill
        if self.skill >= SKILL_COST and self.invis_timer == 0: # Require a charged bar and no cloak already running
            self.skill -= SKILL_COST            # Spend skill bar
            self.invis_timer = SKILL_FRAMES     # Start the invisibility countdown

    def tick_timers(self):                      # Advance every per-frame countdown for this snake
        if self.stun > 0:                       # Currently frozen?
            self.stun -= 1                      # Count down the stun
        if self.invuln > 0:                     # Currently immune?
            self.invuln -= 1                    # Count down the immunity
        if self.boost_timer > 0:                # Speed Boost running?
            self.boost_timer -= 1               # Count down the boost
        if self.invis_timer > 0:                # Invisibility running?
            self.invis_timer -= 1               # Count down the cloak
        self.speed = BOOST_SPEED if self.boost_timer > 0 else BASE_SPEED # Apply the correct movement speed

    def move(self):                             # Advance the head one step and record the new path point
        if self.stun > 0 or self.direction == 'stop': # Frozen or not moving yet?
            return                              # Skip movement this frame
        x, y = self.head.xcor(), self.head.ycor() # Read the current head position
        if self.direction == 'up':              # If moving up
            y += self.speed                     # Increase Y coordinate by speed value
        elif self.direction == 'down':          # If moving down
            y -= self.speed                     # Decrease Y coordinate by speed value
        elif self.direction == 'left':          # If moving left
            x -= self.speed                     # Decrease X coordinate by speed value
        elif self.direction == 'right':         # If moving right
            x += self.speed                     # Increase X coordinate by speed value

        bumped = False                          # Tracks whether this step was blocked by a wall or obstacle
        if x > ARENA_R or x < ARENA_L or y > ARENA_T or y < ARENA_B: # Outer wall collision (no death, per the design)
            bumped = True                       # Mark the step as blocked
        elif inside_obstacle(x, y, pad=6):      # Obstacle box collision -> snake is stunned, never killed
            bumped = True                       # Mark the step as blocked

        if bumped:                              # Blocked step: stay in place, freeze briefly and stop steering
            self.stun = STUN_FRAMES             # Apply the stun
            self.direction = 'stop'             # Clear the direction so the player must steer away
            return                              # Do not commit the blocked position

        self.head.goto(x, y)                    # Commit the new head position
        self.path.append((round(x), round(y)))  # Record the position for body-segment placement
        keep = int((self.length + 2) * SEG_SPACING / BASE_SPEED) + 8 # Frames of history needed to place every segment
        if len(self.path) > keep:               # Trim the history so memory stays flat over a long match
            del self.path[:-keep]               # Drop the oldest points

    def render(self):                           # Draw head and body for the current frame
        self.stamper.clearstamps()              # Clear last frame's body stamps
        cloaked = self.invis_timer > 0          # Is the Invisibility skill active right now?
        blinking = self.invuln > 0 and (self.invuln // 4) % 2 == 0 # Flicker while immune so hits are readable

        if self.use_sprites:                    # SPRITE MODE: body first, then the head, so the head sits on top
            self.head.hideturtle()              # The head turtle is only the position/collision anchor here
            if not cloaked:                     # Body segments are hidden entirely while cloaked
                self.stamper.shape(self.body_sprite) # Make sure the stamper carries the body image
                for pos in self.segments():     # Iterate over every computed segment position
                    self.stamper.goto(pos)      # Move the stamper to the segment position
                    self.stamper.stamp()        # Leave a stamp representing that body segment
            if not blinking:                    # Damage feedback: skip the head on flicker frames
                table = self.ghost_sprites if cloaked else self.head_sprites # Cloaked set or normal set
                self.stamper.shape(table.get(self.facing) or self.head_sprites[self.facing]) # Directional head
                self.stamper.goto(self.head.pos()) # Stamp the head at the anchor position
                self.stamper.stamp()            # Stamped last, so the head always draws above the body
            return                              # Sprite rendering is complete for this frame

        # FALLBACK MODE: original colored-square behaviour, used when no sprite files are present
        if cloaked:                             # Cloaked snakes are only faintly visible (still collidable)
            self.head.color(self.color_dim)     # Dim the head so the owner can still track it
        elif blinking:                          # Just took a hit?
            self.head.color('white')            # Flash the head white
        else:                                   # Normal state
            self.head.color(self.color_main)    # Use the player's normal color

        if not cloaked:                         # Body segments are hidden entirely while cloaked
            self.stamper.color(self.color_main) # Body stamps use the player's normal color
            for pos in self.segments():         # Iterate over every computed segment position
                self.stamper.goto(pos)          # Move the stamper to the segment position
                self.stamper.stamp()            # Leave a stamp representing that body segment

# Player 1 spawns on the left facing right; Player 2 spawns on the right facing left
p1 = Snake('P1', 'p1', '#22e0e0', '#0d3a3a', (-250, -35), 'right') # Instantiate Player 1 (WASD)
p2 = Snake('P2', 'p2', '#ffa22a', '#3a260d', (250, -35), 'left')   # Instantiate Player 2 (Arrow keys)
players = [p1, p2]                              # Convenience list for looping over both players

# ===========================================
# SECTION 6: FRUITS
# ===========================================
def random_free_spot():                         # Find a spawn point that is not inside an obstacle or a snake
    for _ in range(200):                        # Try a bounded number of times to avoid an infinite loop
        x = random.randint(ARENA_L + 30, ARENA_R - 30) # Random X inside the arena with a margin
        y = random.randint(ARENA_B + 30, ARENA_T - 30) # Random Y inside the arena with a margin
        if inside_obstacle(x, y, pad=20):       # Reject points sitting on or next to an obstacle box
            continue                            # Try another point
        too_close = False                       # Tracks proximity to either snake
        for pl in players:                      # Check both players
            if pl.head.distance(x, y) < 60:     # Reject points spawning right on top of a head
                too_close = True                # Mark as rejected
        if not too_close:                       # Point passed every check
            return x, y                         # Use this spawn point
    return 0, 0                                 # Fallback to the arena center if no free spot was found

fruit_sprite = load_shape('fruit')              # Fruit image, or None to fall back to a plain circle
fruits = []                                     # List of fruit Turtle objects
for _ in range(2):                              # Keep two fruits on the field at all times
    f = turtle.Turtle()                         # Instantiate a Turtle object representing a fruit
    f.penup()                                   # Lift pen so fruits never draw lines
    if fruit_sprite:                            # Sprite available
        f.shape(fruit_sprite)                   # Use the fruit image
    else:                                       # Fallback: the original plain circle
        f.shape('circle')                       # Fruits are drawn as circles
        f.color('red')                          # Fruits are red
        f.shapesize(0.7, 0.7)                   # Scale the fruit down to a compact pickup size
    f.goto(random_free_spot())                  # Place the fruit at a free spot
    fruits.append(f)                            # Register the fruit

# ===========================================
# SECTION 7: INPUT HANDLING
# ===========================================
def p1_up():    p1.turn('up', 'down')           # Player 1 steers up (W)
def p1_down():  p1.turn('down', 'up')           # Player 1 steers down (S)
def p1_left():  p1.turn('left', 'right')        # Player 1 steers left (A)
def p1_right(): p1.turn('right', 'left')        # Player 1 steers right (D)

def p2_up():    p2.turn('up', 'down')           # Player 2 steers up (Up arrow)
def p2_down():  p2.turn('down', 'up')           # Player 2 steers down (Down arrow)
def p2_left():  p2.turn('left', 'right')        # Player 2 steers left (Left arrow)
def p2_right(): p2.turn('right', 'left')        # Player 2 steers right (Right arrow)

wn.listen()                                     # Set screen focus to register user keyboard inputs
wn.onkeypress(p1_up, 'w')                       # Bind W to Player 1 up
wn.onkeypress(p1_down, 's')                     # Bind S to Player 1 down
wn.onkeypress(p1_left, 'a')                     # Bind A to Player 1 left
wn.onkeypress(p1_right, 'd')                    # Bind D to Player 1 right
wn.onkeypress(p2_up, 'Up')                      # Bind Up Arrow to Player 2 up
wn.onkeypress(p2_down, 'Down')                  # Bind Down Arrow to Player 2 down
wn.onkeypress(p2_left, 'Left')                  # Bind Left Arrow to Player 2 left
wn.onkeypress(p2_right, 'Right')                # Bind Right Arrow to Player 2 right
wn.onkeypress(p1.use_speed_boost, 'q')          # Player 1 skill 1: Speed Boost
wn.onkeypress(p1.use_invisibility, 'e')         # Player 1 skill 2: Invisibility
wn.onkeypress(p2.use_speed_boost, 'o')          # Player 2 skill 1: Speed Boost
wn.onkeypress(p2.use_invisibility, 'p')         # Player 2 skill 2: Invisibility

# ===========================================
# SECTION 8: COMBAT & SCORING RULES
# ===========================================
def apply_damage(victim):                       # Deal exactly 1 HP of damage and halve the victim's score
    if victim.invuln > 0:                       # Ignore the hit while the victim is still immune
        return False                            # Report that no damage was dealt
    victim.hp -= 1                              # Remove one heart
    victim.score = int(victim.score * SCORE_PENALTY) # Apply the -50% score penalty
    victim.invuln = INVULN_FRAMES               # Grant immunity frames so one touch cannot chain-hit
    victim.stun = STUN_FRAMES                   # Freeze the victim briefly as knockback feedback
    return True                                 # Report that damage was dealt

def resolve_attacks(attacker, defender):        # Apply the attack rules for one attacker/defender ordering
    if attacker.hp <= 0 or defender.hp <= 0:    # Skip if the match is already decided for either side
        return
    head = attacker.head                        # Shorthand for the attacking head

    if head.distance(defender.head) < HIT_RADIUS: # RULE: head hits enemy head -> enemy loses 1 HP, enemy score -50%
        apply_damage(defender)                  # Punish the defender
        return                                  # One hit per frame per ordering

    segs = defender.segments()                  # Current body segments of the defender (tail is the last entry)
    if not segs:                                # Defender has no rendered segments yet
        return

    if head.distance(segs[-1]) < HIT_RADIUS:    # RULE: head hits enemy tail -> enemy loses 1 HP, enemy score -50%
        apply_damage(defender)                  # Punish the defender
        return

    for pos in segs[:-1]:                       # RULE: head hits enemy body (not head/tail) -> ATTACKER is punished
        if head.distance(pos) < HIT_RADIUS:     # Attacker crashed into the defender's midsection
            apply_damage(attacker)              # Punish the attacker instead
            return

def resolve_self_collision(snake):              # Running into your own body stuns you (no death in this design)
    segs = snake.segments()                     # Current segment positions
    for pos in segs[2:]:                        # Skip the two segments directly behind the head
        if snake.head.distance(pos) < HIT_RADIUS - 2: # Head overlapped an older part of its own body
            snake.stun = STUN_FRAMES            # Apply the stun
            snake.direction = 'stop'            # Force the player to steer again
            return

def resolve_fruit(snake):                       # Handle fruit pickup for one snake
    for f in fruits:                            # Check every fruit on the field
        if snake.head.distance(f) < 18:         # Head is close enough to eat this fruit
            snake.score += FRUIT_SCORE          # Add score
            snake.length += GROW_PER_FRUIT      # Extend the snake body
            snake.skill = min(SKILL_MAX, snake.skill + SKILL_GAIN) # Charge the skill bar, capped at SKILL_MAX
            f.goto(random_free_spot())          # Respawn the fruit somewhere else

# ===========================================
# SECTION 9: HUD RENDERING
# ===========================================
hud = turtle.Turtle()                           # Dedicated Turtle object used to write HUD text every frame
hud.hideturtle()                                # Hide its cursor graphics
hud.penup()                                     # Lift pen so it never draws lines
hud.color('white')                              # HUD text is white by default

bar_pen = turtle.Turtle()                       # Dedicated Turtle object used to draw the skill bars
bar_pen.hideturtle()                            # Hide its cursor graphics
bar_pen.penup()                                 # Lift pen so repositioning never draws lines

HEART_FULL = load_shape('heart_full')           # Filled HP heart icon, or None to fall back to text
HEART_EMPTY = load_shape('heart_empty')         # Spent HP heart icon, or None to fall back to text
USE_HEART_ICONS = HEART_FULL is not None and HEART_EMPTY is not None # Icon mode available?

HEART_Y = 250                                   # Vertical center of the heart icon row
HEART_STEP = 22                                 # Horizontal spacing between heart icons
BAR_W, BAR_H = 132, 12                          # Skill bar dimensions in pixels
PANEL = {                                       # Per-player HUD panel geometry
    'p1': {'heart_x': -356, 'dir': 1, 'text_x': -356, 'align': 'left',  'bar_x': -358},  # Left panel
    'p2': {'heart_x': 356,  'dir': -1, 'text_x': 356, 'align': 'right', 'bar_x': 358 - BAR_W}, # Right panel
}

heart_icons = {}                                # Pools of reusable heart Turtle objects, one pool per player
if USE_HEART_ICONS:                             # Only build the pools when both icons loaded
    for pl in (p1, p2):                         # One pool per player
        pool = []                               # Icons for this player
        geo = PANEL[pl.key]                     # Panel geometry for this player
        for i in range(MAX_HP):                 # One reusable icon per maximum heart
            icon = turtle.Turtle()              # Instantiate a Turtle object to display one heart
            icon.penup()                        # Lift pen so it never draws lines
            icon.shape(HEART_FULL)              # Start as a filled heart
            icon.goto(geo['heart_x'] + geo['dir'] * i * HEART_STEP, HEART_Y) # Lay the row out inward
            pool.append(icon)                   # Register the icon
        heart_icons[pl.key] = pool              # Store this player's pool

def draw_skill_bar(left, bottom, ratio, color): # Draw one skill bar: gray frame plus a colored fill
    bar_pen.penup()                             # Make sure the pen is up before travelling
    bar_pen.goto(left, bottom)                  # Move to the bottom-left corner of the frame
    bar_pen.setheading(0)                       # Face east so the frame is axis-aligned
    bar_pen.pensize(2)                          # Frame line thickness
    bar_pen.color('#5a5a6b')                    # Frame color (neutral gray)
    bar_pen.pendown()                           # Start drawing the frame
    for _ in range(2):                          # Draw the rectangle as two identical corner pairs
        bar_pen.forward(BAR_W)                  # Bottom / top edge
        bar_pen.left(90)                        # Turn to the vertical edge
        bar_pen.forward(BAR_H)                  # Right / left edge
        bar_pen.left(90)                        # Turn back to horizontal
    bar_pen.penup()                             # Frame finished

    fill_w = (BAR_W - 4) * ratio                # Width of the filled portion, inset by the frame
    if fill_w >= 1:                             # Skip drawing an empty fill
        bar_pen.goto(left + 2, bottom + 2)      # Move inside the frame
        bar_pen.color(color)                    # Fill color matches the player
        bar_pen.pendown()                       # Start the filled shape
        bar_pen.begin_fill()                    # Record the shape so it can be filled
        for w, h in ((fill_w, BAR_H - 4), (fill_w, BAR_H - 4)): # Two passes draw the four sides
            bar_pen.forward(w)                  # Horizontal edge
            bar_pen.left(90)                    # Turn
            bar_pen.forward(h)                  # Vertical edge
            bar_pen.left(90)                    # Turn
        bar_pen.end_fill()                      # Close and fill the shape
        bar_pen.penup()                         # Fill finished

def draw_hud():                                 # Draw the full heads-up display for the current frame
    hud.clear()                                 # Erase last frame's HUD text
    bar_pen.clear()                             # Erase last frame's skill bars

    for pl in players:                          # Draw one stats panel per player
        geo = PANEL[pl.key]                     # Panel geometry for this player

        if USE_HEART_ICONS:                     # ICON MODE: show one heart image per HP point
            for i, icon in enumerate(heart_icons[pl.key]): # Walk this player's icon pool
                icon.shape(HEART_FULL if i < pl.hp else HEART_EMPTY) # Filled while the HP is still there
                icon.showturtle()               # Keep every icon visible so losses are readable
            score_x = geo['text_x'] + geo['dir'] * (MAX_HP * HEART_STEP + 4) # Score sits after the hearts
        else:                                   # FALLBACK MODE: original text hearts
            hud.color(pl.color_main)            # Match the text to the player color
            hud.goto(geo['text_x'], HEART_Y - 6) # Position the text hearts
            hud.write('<3 ' * max(0, pl.hp), align=geo['align'], font=('Courier', 13, 'bold')) # Text hearts
            score_x = geo['text_x'] + geo['dir'] * (MAX_HP * 26) # Score sits after the text hearts

        hud.color(pl.color_main)                # Player name and score use the player color
        hud.goto(score_x, HEART_Y - 7)          # Position the name + score line
        hud.write('{}  {}'.format(pl.name, pl.score), align=geo['align'], font=('Courier', 14, 'bold')) # Score

        ratio = max(0.0, min(1.0, pl.skill / SKILL_MAX)) # Skill bar fill fraction, clamped to 0..1
        draw_skill_bar(geo['bar_x'], 224, ratio, pl.color_main) # Draw the bar frame plus its fill

        tags = []                               # Active status tags for this player
        if pl.boost_timer > 0:                  # Speed Boost currently running?
            tags.append('BOOST')                # Show the boost tag
        if pl.invis_timer > 0:                  # Invisibility currently running?
            tags.append('CLOAK')                # Show the cloak tag
        if pl.stun > 0:                         # Currently stunned?
            tags.append('STUN')                 # Show the stun tag
        if tags:                                # Only write the line when something is active
            hud.color('#dddddd')                # Status tags are light gray so they stand out
            hud.goto(geo['bar_x'] + (BAR_W + 8 if geo['dir'] > 0 else -8), 224) # Just beside the bar
            hud.write(' '.join(tags), align='left' if geo['dir'] > 0 else 'right',
                      font=('Courier', 10, 'bold')) # Render the tags

    hud.color('gray')                           # Center hint text is gray
    hud.goto(0, 243)                            # Center of the top HUD strip
    hud.write('FIRST TO {}'.format(TARGET_SCORE), align='center', font=('Courier', 12, 'bold')) # Win condition
    hud.color('#4a4a4a')                        # Dim the control hint so it never distracts from the action
    hud.goto(0, -272)                           # Bottom control hint strip, kept inside the arena so it is never clipped
    hud.write('P1: WASD  Q=Boost E=Cloak     |     P2: Arrows  O=Boost P=Cloak',
              align='center', font=('Courier', 10, 'normal')) # Control reference for both players

# ===========================================
# SECTION 10: WIN CONDITION & RESULT SCREEN
# ===========================================
result_pen = turtle.Turtle()                    # Dedicated Turtle object used to render the result screen
result_pen.hideturtle()                         # Hide its cursor graphics
result_pen.penup()                              # Lift pen so it never draws lines

def check_win():                                # Return the winning Snake, 'draw', or None if the match continues
    if p1.hp <= 0 and p2.hp <= 0:               # Both players ran out of hearts on the same frame
        return 'draw'                           # The match is a draw
    if p1.hp <= 0:                              # Player 1 is out of hearts
        return p2                               # Player 2 wins
    if p2.hp <= 0:                              # Player 2 is out of hearts
        return p1                               # Player 1 wins
    if p1.score >= TARGET_SCORE and p2.score >= TARGET_SCORE: # Both crossed the target on the same frame
        return 'draw' if p1.score == p2.score else (p1 if p1.score > p2.score else p2) # Higher score wins
    if p1.score >= TARGET_SCORE:                # Player 1 reached the target score
        return p1                               # Player 1 wins
    if p2.score >= TARGET_SCORE:                # Player 2 reached the target score
        return p2                               # Player 2 wins
    return None                                 # No winner yet

def show_result(winner):                        # Render the end-of-match result screen
    global game_active                          # Access the global loop flag to stop the game loop
    game_active = False                         # Stop scheduling further game loop frames

    for pl in players:                          # Clear the arena so the result text is easy to read
        pl.head.hideturtle()                    # Hide both snake heads
        pl.stamper.clearstamps()                # Remove every body segment stamp
    for f in fruits:                            # Hide the fruits as well
        f.hideturtle()                          # Remove the fruit graphics
    obstacle_pen.clear()                        # Erase the obstacle boxes so the result text reads cleanly

    result_pen.clear()                          # Clear any previous result text
    result_pen.color('white')                   # Result heading is white
    result_pen.goto(0, 60)                      # Position the heading above center
    result_pen.write('RESULT', align='center', font=('Courier', 26, 'bold')) # Heading text

    if winner == 'draw':                        # Nobody won outright
        result_pen.goto(0, 15)                  # Position the outcome line
        result_pen.write('DRAW!', align='center', font=('Courier', 22, 'bold')) # Draw message
    else:                                       # One player won
        result_pen.color(winner.color_main)     # Color the outcome line with the winner's color
        result_pen.goto(0, 15)                  # Position the outcome line
        result_pen.write('{} WINS!'.format(winner.name), align='center', font=('Courier', 22, 'bold')) # Winner message

    result_pen.color('white')                   # Detail lines are white
    result_pen.goto(0, -30)                     # Position the per-player detail line
    result_pen.write('P1  score {}  hp {}     |     P2  score {}  hp {}'.format(
        p1.score, max(0, p1.hp), p2.score, max(0, p2.hp)),
        align='center', font=('Courier', 13, 'normal')) # Final score and HP for both players
    result_pen.goto(0, -80)                     # Position the restart hint
    result_pen.color('gray')                    # Restart hint is gray
    result_pen.write('Press R to play again', align='center', font=('Courier', 12, 'normal')) # Restart hint
    wn.update()                                 # Force an immediate redraw so the result is visible

def restart():                                  # Reset every entity and start a new match
    global game_active                          # Access the global loop flag to restart the loop
    if game_active:                             # Ignore the restart key while a match is still running
        return
    result_pen.clear()                          # Remove the result screen text
    build_obstacles()                           # Redraw the obstacle boxes for the new match
    for pl in players:                          # Reset both players
        pl.reset()                              # Restore hearts, score, skill bar, length and position
    for f in fruits:                            # Respawn every fruit
        f.goto(random_free_spot())              # Move the fruit to a fresh free spot
        f.showturtle()                          # Make the fruit visible again after the result screen
    game_active = True                          # Re-enable the game loop
    game_loop()                                 # Kick the loop back off

wn.onkeypress(restart, 'r')                     # Bind R to restart the match from the result screen

# ===========================================
# SECTION 11: MAIN GAME LOOP
# ===========================================
def game_loop():                                # Primary function executing every game tick (~60 FPS)
    global game_active                          # Access global active flag to check game state
    if not game_active:                         # Stop executing loop iterations if the match is over
        return

    # --- read input is event-driven (SECTION 7) and already applied to each snake's direction ---
    for pl in players:                          # Update both players in the same order every frame
        pl.tick_timers()                        # Advance stun / immunity / skill countdowns and apply speed
        pl.move()                               # Advance the head and record the new path point

    for pl in players:                          # Resolve pickups and self-collision per player
        resolve_fruit(pl)                       # Fruit -> add score, extend snake, charge skill bar
        resolve_self_collision(pl)              # Own body -> stunned (no death)

    resolve_attacks(p1, p2)                     # Apply the attack rules with Player 1 attacking
    resolve_attacks(p2, p1)                     # Apply the same rules with Player 2 attacking (symmetric)

    for pl in players:                          # Render both snakes for this frame
        pl.render()                             # Draw head plus every body segment
    draw_hud()                                  # Draw HP hearts, scores and skill bars

    winner = check_win()                        # Evaluate the win conditions
    if winner is not None:                      # Someone won or the match ended in a draw
        for pl in players:                      # Freeze both snakes on the result screen
            pl.direction = 'stop'               # Stop all movement
        show_result(winner)                     # Render the result screen and stop the loop
        return                                  # Exit this frame

    wn.update()                                 # Redraw all screen elements for the current frame
    wn.ontimer(game_loop, 16)                   # Schedule next execution of game_loop after 16ms (~60 FPS)

# Game Execution Entry Point
game_loop()                                     # Kickoff initial frame execution of game loop
wn.mainloop()                                   # Start turtle event listener loop to keep window open
