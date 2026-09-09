"""
snake.py - the Snake entity. Instantiated once per player, which is what makes the
game local multiplayer: both players run identical code with different keys and sprites.

Body segments are NOT a list of turtles. move() records the head position every frame
into self.path, and _compute_segments() walks that history backwards accumulating
DISTANCE, placing one segment every SEG_SPACING pixels. Distance (not frame count) is
what keeps the body evenly spaced while Speed Boost is doubling the pixels per frame.
"""

import turtle                                   # Turtle objects for the head and the stamper

from config import (BASE_SPEED, BOOST_SPEED, SEG_SPACING, START_LENGTH, OPPOSITE, # Movement
                    ARENA_L, ARENA_R, ARENA_B, ARENA_T, OBSTACLE_PAD,             # World bounds
                    MAX_HP, STUN_FRAMES, BUMP_COOLDOWN, SKILL_MAX, SKILL_COST,    # Rules
                    SKILL_FRAMES)
import arena                                    # inside_obstacle() for box collision
import effects                                  # Particle bursts on bump / skill
from sounds import sfx                          # Sound effects
from sprites import load_shape, load_direction_set # Sprite loading with square fallback
from screen import new_pen                      # Helper for the stamper turtle


class Snake:
    def __init__(self, name, key, color, dim_color, start_pos, start_dir):
        self.name = name                        # HUD label ("P1" / "P2")
        self.key = key                          # Sprite file prefix ("p1" / "p2")
        self.color_main = color                 # Normal color (also the fallback square color)
        self.color_dim = dim_color              # Faint color used by the square fallback while cloaked
        self.start_pos = start_pos              # Spawn coordinates
        self.start_dir = start_dir              # Spawn facing

        # --- sprites: one head per direction, plus a faded ghost set for Invisibility ---
        self.head_sprites = load_direction_set('{}_head'.format(key))          # Normal heads
        self.ghost_sprites = {d: load_shape('{}_head_{}_ghost'.format(key, d)) # Cloaked heads
                              for d in ('up', 'down', 'left', 'right')}
        self.body_sprite = load_shape('{}_body'.format(key))                   # Body segment
        self.use_sprites = all(self.head_sprites.values()) and self.body_sprite is not None # All present?

        # --- head turtle: in sprite mode it is only the position/collision anchor ---
        self.head = turtle.Turtle()             # Turtle object tracking the head position
        self.head.penup()                       # Never draw a trail line
        if self.use_sprites:                    # Sprite mode
            self.head.shape(self.head_sprites[start_dir]) # Start facing the spawn direction
        else:                                   # Square fallback
            self.head.shape('square')           # Plain square head
            self.head.color(color)              # Player color
            self.head.shapesize(0.8, 0.8)       # About 16x16 px

        # --- one stamper turtle draws every body segment (and the head, in sprite mode) ---
        self.stamper = new_pen()                # Invisible turtle used only for stamping
        if self.use_sprites:                    # Sprite mode
            self.stamper.shape(self.body_sprite) # Carry the body image
        else:                                   # Square fallback
            self.stamper.shape('square')        # Plain square body
            self.stamper.color(color)           # Player color
            self.stamper.shapesize(0.65, 0.65)  # Slightly smaller than the head

        self.reset()                            # Initialize all per-match state

    # ===========================================
    # MATCH STATE
    # ===========================================
    def reset(self):                            # Restore this snake to its starting state
        self.head.goto(*self.start_pos)         # Back to the spawn point
        if not self.use_sprites:                # Square fallback recolors instead of swapping sprites
            self.head.color(self.color_main)    # Restore the normal color
        self.head.showturtle()                  # Visible again (sprite mode hides it during render)
        self.direction = self.start_dir         # Current movement direction
        self.facing = self.start_dir            # Last real direction, drives the head sprite
        self.length = START_LENGTH              # Body length in segments
        self.path = [self.start_pos]            # Head position history
        self._segs = []                         # Cached segment positions for this frame
        self.hp = MAX_HP                        # Hearts
        self.score = 0                          # Score
        self.skill = 0                          # Skill bar
        self.speed = BASE_SPEED                 # Pixels per frame
        self.stun = 0                           # Frames left frozen
        self.invuln = 0                         # Frames left immune
        self.bump_cd = 0                        # Frames before a wall/box can stun again
        self.self_hit_cd = 0                    # Frames before biting yourself can stun again
        self.boost_timer = 0                    # Speed Boost frames left
        self.invis_timer = 0                    # Invisibility frames left
        self.stamper.clearstamps()              # Remove stamps from the previous match

    # ===========================================
    # BODY GEOMETRY
    # ===========================================
    def _compute_segments(self):                # Walk the path backwards, one segment per SEG_SPACING px
        points = []                             # Segment positions, head-side first
        target = SEG_SPACING                    # Distance behind the head for the next segment
        travelled = 0.0                         # Distance accumulated while walking back
        prev = self.path[-1]                    # Newest point is the head
        for i in range(len(self.path) - 2, -1, -1): # From newest to oldest
            cur = self.path[i]                  # Next older point
            travelled += abs(cur[0] - prev[0]) + abs(cur[1] - prev[1]) # Axis-aligned, so this is exact
            prev = cur                          # Advance the walk
            while travelled >= target and len(points) < self.length: # Reached one or more segment spots
                points.append(cur)              # Place a segment here
                target += SEG_SPACING           # Next spot is one spacing further back
            if len(points) >= self.length:      # Body complete
                break
        return points                           # Tail is the last element

    def refresh_segments(self):                 # Recompute the cache once per frame
        self._segs = self._compute_segments()   # Called from the game loop right after move()

    def segments(self):                         # Read the cached segments
        return self._segs                       # Collision code and render both use this

    def tail(self):                             # Tail position, or None if the body is still forming
        return self._segs[-1] if self._segs else None

    # ===========================================
    # INPUT
    # ===========================================
    def turn(self, new_dir):                    # Steer, blocking instant 180-degree reversals
        # NOTE: this compares against `facing`, not `direction`. Comparing against
        # `direction` used to allow a full reversal whenever the snake was stopped,
        # which drove the head straight into its own neck and locked the game up.
        if OPPOSITE[new_dir] == self.facing:    # Trying to reverse onto its own body
            return                              # Ignore the input
        self.direction = new_dir                # Apply the new direction
        self.facing = new_dir                   # Remember it for the head sprite

    # ===========================================
    # SKILLS
    # ===========================================
    def use_speed_boost(self):                  # Spend skill bar for temporary speed
        if self.skill >= SKILL_COST and self.boost_timer == 0: # Charged, and not already boosting
            self.skill -= SKILL_COST            # Pay the cost
            self.boost_timer = SKILL_FRAMES     # Start the timer
            sfx.play('skill')                   # Sound feedback
            effects.burst_skill(self.head.xcor(), self.head.ycor(), self.color_main) # Visual feedback

    def use_invisibility(self):                 # Spend skill bar to hide the body
        if self.skill >= SKILL_COST and self.invis_timer == 0: # Charged, and not already cloaked
            self.skill -= SKILL_COST            # Pay the cost
            self.invis_timer = SKILL_FRAMES     # Start the timer
            sfx.play('skill')                   # Sound feedback
            effects.burst_skill(self.head.xcor(), self.head.ycor(), self.color_main) # Visual feedback

    def gain_skill(self, amount):               # Charge the bar, capped at SKILL_MAX
        self.skill = min(SKILL_MAX, self.skill + amount) # Never overfill

    # ===========================================
    # PER-FRAME UPDATE
    # ===========================================
    def tick_timers(self):                      # Count down every timer and apply the current speed
        for attr in ('stun', 'invuln', 'bump_cd', 'self_hit_cd', 'boost_timer', 'invis_timer'):
            value = getattr(self, attr)         # Read the timer
            if value > 0:                       # Only count down running timers
                setattr(self, attr, value - 1)  # Tick it
        self.speed = BOOST_SPEED if self.boost_timer > 0 else BASE_SPEED # Boost or normal speed

    def move(self):                             # Advance the head one step
        if self.stun > 0 or self.direction == 'stop': # Frozen, or never started moving
            return
        x, y = self.head.xcor(), self.head.ycor() # Current position
        if self.direction == 'up':              # Apply the direction
            y += self.speed
        elif self.direction == 'down':
            y -= self.speed
        elif self.direction == 'left':
            x -= self.speed
        elif self.direction == 'right':
            x += self.speed

        # Wall and obstacle boxes block movement but never kill.
        blocked = (x > ARENA_R or x < ARENA_L or y > ARENA_T or y < ARENA_B  # Outer wall
                   or arena.inside_obstacle(x, y, pad=OBSTACLE_PAD))        # Obstacle box
        if blocked:
            # IMPORTANT: `direction` is deliberately NOT cleared here.
            # Clearing it used to leave the snake standing still with the only escape
            # being a 180-degree turn into its own body - the "hit a wall and the game
            # loops forever" bug. Keeping the direction means the snake simply cannot
            # advance while it faces the wall, and either perpendicular turn frees it.
            if self.bump_cd == 0:               # Only stun once per bump, not every frame
                self.stun = STUN_FRAMES         # Brief freeze as feedback
                self.bump_cd = BUMP_COOLDOWN    # Block repeat stuns (also stops key-repeat spam)
                sfx.play('bump')                # Sound feedback
                effects.burst_bump(x, y)        # Dust puff at the impact point
            return                              # Position is not committed

        self.head.goto(x, y)                    # Commit the new head position
        self.path.append((round(x), round(y)))  # Record it for body placement
        keep = int((self.length + 2) * SEG_SPACING / BASE_SPEED) + 8 # History actually needed
        if len(self.path) > keep:               # Keep memory flat over a long match
            del self.path[:-keep]               # Drop the oldest points

    # ===========================================
    # RENDER
    # ===========================================
    def render(self):                           # Draw the body, then the head on top
        self.stamper.clearstamps()              # Wipe last frame
        cloaked = self.invis_timer > 0          # Invisibility active?
        blinking = self.invuln > 0 and (self.invuln // 4) % 2 == 0 # Flicker while immune

        if self.use_sprites:                    # SPRITE MODE
            self.head.hideturtle()              # The head turtle is just the anchor here
            if not cloaked:                     # Cloaked snakes show no body at all
                self.stamper.shape(self.body_sprite) # Body image
                for pos in self._segs:          # Every cached segment position
                    self.stamper.goto(pos)      # Move the stamper
                    self.stamper.stamp()        # Draw the segment
            if not blinking:                    # Skip the head on flicker frames
                table = self.ghost_sprites if cloaked else self.head_sprites # Which sprite set
                self.stamper.shape(table.get(self.facing) or self.head_sprites[self.facing])
                self.stamper.goto(self.head.pos()) # Head position
                # Stamped LAST on purpose: turtle canvas items stack in creation order,
                # so anything stamped after the body is what ends up drawn above it.
                self.stamper.stamp()            # Draw the head
            return                              # Sprite rendering done

        # SQUARE FALLBACK (no assets/ present)
        if cloaked:                             # Faint while cloaked
            self.head.color(self.color_dim)
        elif blinking:                          # White flash after a hit
            self.head.color('white')
        else:                                   # Normal
            self.head.color(self.color_main)
        if not cloaked:                         # Body squares
            self.stamper.color(self.color_main) # Player color
            for pos in self._segs:              # Every cached segment position
                self.stamper.goto(pos)          # Move the stamper
                self.stamper.stamp()            # Draw the segment

    def hide(self):                             # Remove this snake from the screen (result screen)
        self.head.hideturtle()                  # Hide the anchor / square head
        self.stamper.clearstamps()              # Remove every body and head stamp
