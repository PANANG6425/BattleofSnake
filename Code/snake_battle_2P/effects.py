"""
effects.py - tiny particle system for hit / eat / skill feedback.

One stamper turtle draws every particle: clearstamps() wipes last frame, then one
stamp per live particle. Particles are plain dicts (x, y, dx, dy, life, color, size)
so there is no class overhead and the whole list can be rebuilt each frame.
"""

import math                                     # For the circular burst directions
import random                                   # For per-particle jitter

from config import (FX_MAX, FX_LIFE, FX_GRAVITY, FX_EAT_COUNT, # Effect tuning
                    FX_HIT_COUNT, FX_BUMP_COUNT, FX_SKILL_COUNT)
from screen import new_pen                      # Helper that builds an invisible drawing turtle

_pen = new_pen()                                # The single turtle used to stamp all particles
_pen.shape('square')                            # Particles are small squares
_particles = []                                 # Live particle list


def _spawn(x, y, color, count, speed, life, size): # Shared burst builder
    for i in range(count):                      # One particle per requested count
        if len(_particles) >= FX_MAX:           # Respect the hard cap
            return                              # Silently drop the extras
        angle = (2 * math.pi) * (i / count) + random.uniform(-0.3, 0.3) # Spread around a circle
        spd = speed * random.uniform(0.5, 1.2)  # Vary the speed so it looks organic
        _particles.append({
            'x': x, 'y': y,                     # Start at the event position
            'dx': math.cos(angle) * spd,        # Horizontal velocity
            'dy': math.sin(angle) * spd,        # Vertical velocity
            'life': life,                       # Frames remaining
            'max_life': life,                   # Used to fade the size out
            'color': color,                     # Particle color
            'size': size,                       # Starting size multiplier
        })


def burst_eat(x, y):                            # Fruit pickup: small bright pop
    _spawn(x, y, '#ff5566', FX_EAT_COUNT, 2.6, FX_LIFE, 0.32)   # Red fruit shards
    _spawn(x, y, '#ffe08a', FX_EAT_COUNT // 2, 1.6, FX_LIFE, 0.22) # Warm sparkle


def burst_hit(x, y):                            # Damage: bigger, faster, white hot
    _spawn(x, y, '#ffffff', FX_HIT_COUNT, 4.2, FX_LIFE + 6, 0.4) # White flash shards
    _spawn(x, y, '#ff3355', FX_HIT_COUNT // 2, 3.0, FX_LIFE + 4, 0.3) # Red follow-up


def burst_bump(x, y):                           # Wall / obstacle bump: dull gray puff
    _spawn(x, y, '#9aa0b0', FX_BUMP_COUNT, 1.8, FX_LIFE - 4, 0.26) # Dust


def burst_skill(x, y, color):                   # Skill activation: ring in the player color
    _spawn(x, y, color, FX_SKILL_COUNT, 3.4, FX_LIFE, 0.3)      # Colored ring


def update_and_draw():                          # Advance every particle and redraw the whole set
    _pen.clearstamps()                          # Remove last frame's particle stamps
    if not _particles:                          # Nothing to do
        return
    alive = []                                  # Particles that survive this frame
    for p in _particles:                        # Walk every live particle
        p['life'] -= 1                          # Age it
        if p['life'] <= 0:                      # Dead particles are dropped
            continue
        p['x'] += p['dx']                       # Apply horizontal velocity
        p['y'] += p['dy']                       # Apply vertical velocity
        p['dy'] -= FX_GRAVITY                   # Optional downward pull
        p['dx'] *= 0.92                         # Drag, so the burst slows down
        p['dy'] *= 0.92                         # Drag on the vertical axis too
        fade = p['life'] / p['max_life']        # 1.0 when new, approaching 0 when dying
        _pen.color(p['color'])                  # Set the particle color
        _pen.shapesize(max(0.08, p['size'] * fade)) # Shrink as it fades
        _pen.goto(p['x'], p['y'])               # Move the stamper into place
        _pen.stamp()                            # Draw this particle
        alive.append(p)                         # Keep it for next frame
    _particles[:] = alive                       # Replace the list contents in place


def clear():                                    # Wipe every particle (used on restart / result screen)
    _particles.clear()                          # Drop the data
    _pen.clearstamps()                          # Drop the graphics
