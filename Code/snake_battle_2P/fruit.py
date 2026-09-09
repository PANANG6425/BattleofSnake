"""
fruit.py - the fruit pickups and where they are allowed to spawn.
"""

import random                                   # Random spawn positions

from config import (ARENA_L, ARENA_R, ARENA_B, ARENA_T, FRUIT_COUNT) # Spawn bounds and count
import arena                                    # inside_obstacle() so fruit never spawns in a box
from screen import new_pen                      # Helper that builds a turtle
from sprites import load_shape                  # Fruit image with circle fallback

_fruit_sprite = load_shape('fruit')             # None when assets/ is missing
fruits = []                                     # Every fruit Turtle object


def random_free_spot(players):                  # Pick a point clear of obstacles and both snakes
    for _ in range(200):                        # Bounded attempts: never loop forever
        x = random.randint(ARENA_L + 30, ARENA_R - 30) # Random X inside the arena, with a margin
        y = random.randint(ARENA_B + 30, ARENA_T - 30) # Random Y inside the arena, with a margin
        if arena.inside_obstacle(x, y, pad=20): # Too close to an obstacle box
            continue                            # Try again
        if any(p.head.distance(x, y) < 60 for p in players): # Right on top of a player
            continue                            # Try again
        return x, y                             # This point is good
    return 0, -35                               # Fallback: the middle corridor


def spawn_fruits(players):                      # Create the fruit turtles once at startup
    for _ in range(FRUIT_COUNT):                # One turtle per fruit
        f = new_pen(visible=True)               # Fruits are visible turtles
        if _fruit_sprite:                       # Sprite available
            f.shape(_fruit_sprite)              # Use the apple image
        else:                                   # Fallback
            f.shape('circle')                   # Plain circle
            f.color('red')                      # Red
            f.shapesize(0.7, 0.7)               # Compact pickup size
        f.goto(random_free_spot(players))       # Place it somewhere legal
        fruits.append(f)                        # Register it
    return fruits                               # Hand the list back


def respawn(f, players):                        # Move one eaten fruit somewhere else
    f.goto(random_free_spot(players))           # New legal position
    f.showturtle()                              # Make sure it is visible (result screen hides them)


def respawn_all(players):                       # Reset every fruit (used on restart)
    for f in fruits:                            # Walk every fruit
        respawn(f, players)                     # Move and show it


def hide_all():                                 # Hide every fruit (used by the result screen)
    for f in fruits:                            # Walk every fruit
        f.hideturtle()                          # Remove its graphic
