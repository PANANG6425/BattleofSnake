"""
arena.py - the static world: outer walls and obstacle boxes.

Obstacle boxes are drawn with turtle (begin_fill / end_fill) and their bounding boxes
are cached in `obstacles` as (left, bottom, right, top) tuples for collision tests.
"""

from config import (BORDER_L, BORDER_R, BORDER_TOP, BORDER_BOTTOM, WALL_COLOR, # Wall geometry
                    OBSTACLE_SPOTS, OBSTACLE_COUNT, OBSTACLE_SIZE,             # Obstacle layout
                    OBSTACLE_EDGE, OBSTACLE_FILL)                              # Obstacle colors
from screen import new_pen                      # Helper that builds an invisible drawing turtle

_wall_pen = new_pen()                           # Turtle used once to draw the arena walls
_box_pen = new_pen()                            # Turtle used to draw and erase obstacle boxes

obstacles = []                                  # Collision bounds: list of (left, bottom, right, top)


def draw_border():                              # Draw the four outer walls one time at startup
    width = BORDER_R - BORDER_L                 # Horizontal wall length
    height = BORDER_TOP - BORDER_BOTTOM         # Vertical wall length
    _wall_pen.color(WALL_COLOR)                 # Wall color
    _wall_pen.pensize(6)                        # Wall thickness
    _wall_pen.penup()                           # Lift the pen before travelling
    _wall_pen.goto(BORDER_L, BORDER_TOP)        # Start at the top-left corner
    _wall_pen.setheading(0)                     # Face east
    _wall_pen.pendown()                         # Start drawing
    for _ in range(2):                          # Two identical corner pairs make a rectangle
        _wall_pen.forward(width)                # Top / bottom wall
        _wall_pen.right(90)                     # Turn to the vertical wall
        _wall_pen.forward(height)               # Right / left wall
        _wall_pen.right(90)                     # Turn back to horizontal
    _wall_pen.penup()                           # Done drawing


def _draw_box(cx, cy, size):                    # Draw one filled obstacle box centered on (cx, cy)
    half = size / 2                             # Half-size converts center to corner
    _box_pen.color(OBSTACLE_EDGE, OBSTACLE_FILL) # Outline color, fill color
    _box_pen.pensize(3)                         # Outline thickness
    _box_pen.penup()                            # Lift before travelling
    _box_pen.goto(cx - half, cy + half)         # Top-left corner of the box
    _box_pen.setheading(0)                      # Face east so the box is axis-aligned
    _box_pen.pendown()                          # Start drawing
    _box_pen.begin_fill()                       # Record the shape for filling
    for _ in range(4):                          # Four equal sides
        _box_pen.forward(size)                  # One side
        _box_pen.right(90)                      # Turn for the next
    _box_pen.end_fill()                         # Close and fill
    _box_pen.penup()                            # Done drawing
    obstacles.append((cx - half, cy - half, cx + half, cy + half)) # Cache the collision bounds


def build_obstacles():                          # (Re)create every obstacle box for a fresh match
    _box_pen.clear()                            # Erase previously drawn boxes
    obstacles.clear()                           # Forget the old collision bounds
    for cx, cy in OBSTACLE_SPOTS[:OBSTACLE_COUNT]: # Draw as many boxes as configured
        _draw_box(cx, cy, OBSTACLE_SIZE)        # Draw it and register its bounds


def clear_obstacles():                          # Erase the boxes without forgetting anything else
    _box_pen.clear()                            # Used by the result screen so text reads cleanly


def inside_obstacle(x, y, pad=0):               # Does the point (x, y) hit any obstacle box?
    for left, bottom, right, top in obstacles:  # Check every box
        if left - pad <= x <= right + pad and bottom - pad <= y <= top + pad: # Inside padded bounds
            return True                         # Collision
    return False                                # Clear
