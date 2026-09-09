"""
hud.py - the stats panel above the arena, plus the stun bar that floats over each snake.

The panel lives in the strip above ARENA_T so snakes and fruits can never cover it.
The stun bar is drawn LAST every frame (after the snakes) so it always sits on top.
"""

from config import (MAX_HP, SKILL_MAX, STUN_FRAMES, TARGET_SCORE,   # Values shown
                    HEART_Y, HEART_STEP, BAR_W, BAR_H, BAR_Y,       # Panel geometry
                    BAR_FRAME, HINT_COLOR, FONT,                    # Panel styling
                    STUN_BAR_W, STUN_BAR_H, STUN_BAR_LIFT,          # Stun bar geometry
                    STUN_BAR_FILL, STUN_BAR_BG)                     # Stun bar colors
from screen import new_pen                      # Helper that builds an invisible drawing turtle
from sprites import load_shape                  # Heart icons with text fallback
from sounds import sfx                          # Shown as the SOUND indicator

_text = new_pen('white')                        # Writes every piece of HUD text
_bar = new_pen()                                # Draws the two skill bars
_over = new_pen()                               # Draws the floating stun bars over the snakes

HEART_FULL = load_shape('heart_full')           # Filled heart icon, or None
HEART_EMPTY = load_shape('heart_empty')         # Spent heart icon, or None
USE_HEART_ICONS = HEART_FULL is not None and HEART_EMPTY is not None # Icon mode available?

# Mirrored panel geometry: P1 grows to the right from the left edge, P2 to the left
PANEL = {
    'p1': {'x': -356, 'dir': 1,  'align': 'left',  'bar_x': -358},
    'p2': {'x': 356,  'dir': -1, 'align': 'right', 'bar_x': 358 - BAR_W},
}

_heart_icons = {}                               # key -> list of reusable heart turtles


def build(players):                             # Create the heart icon pools once at startup
    if not USE_HEART_ICONS:                     # Text fallback needs no turtles
        return
    for pl in players:                          # One pool per player
        geo = PANEL[pl.key]                     # This player's panel geometry
        pool = []                               # Icons for this player
        for i in range(MAX_HP):                 # One reusable icon per maximum heart
            icon = new_pen(visible=True)        # Visible turtle showing one heart
            icon.shape(HEART_FULL)              # Start as a filled heart
            icon.goto(geo['x'] + geo['dir'] * i * HEART_STEP, HEART_Y) # Lay the row out inward
            pool.append(icon)                   # Register it
        _heart_icons[pl.key] = pool             # Store the pool


def _rect(pen, left, bottom, width, height, fill=None, frame=None): # Draw one rectangle
    if width < 1:                               # Nothing to draw
        return
    pen.penup()                                 # Lift before travelling
    pen.goto(left, bottom)                      # Bottom-left corner
    pen.setheading(0)                           # Face east
    if frame:                                   # Optional outline
        pen.pensize(2)                          # Outline thickness
        pen.color(frame)                        # Outline color
    if fill:                                    # Optional fill
        pen.pensize(1)                          # Thin edge so the fill keeps its exact size
        pen.color(fill)                         # Fill color
        pen.begin_fill()                        # Start recording the shape
    pen.pendown()                               # Start drawing
    for _ in range(2):                          # Two corner pairs make a rectangle
        pen.forward(width)                      # Horizontal edge
        pen.left(90)                            # Turn
        pen.forward(height)                     # Vertical edge
        pen.left(90)                            # Turn
    if fill:                                    # Close the filled shape
        pen.end_fill()                          # Fill it
    pen.penup()                                 # Done


def _skill_bar(left, ratio, color):             # Frame plus proportional fill
    _rect(_bar, left, BAR_Y, BAR_W, BAR_H, frame=BAR_FRAME)          # Empty frame
    _rect(_bar, left + 2, BAR_Y + 2, (BAR_W - 4) * ratio, BAR_H - 4, fill=color) # Filled portion


def draw_panel(players):                        # Redraw the whole stats panel
    _text.clear()                               # Wipe last frame's text
    _bar.clear()                                # Wipe last frame's bars

    for pl in players:                          # One panel per player
        geo = PANEL[pl.key]                     # Panel geometry

        if USE_HEART_ICONS:                     # ICON MODE
            for i, icon in enumerate(_heart_icons[pl.key]): # Walk the pool
                icon.shape(HEART_FULL if i < pl.hp else HEART_EMPTY) # Full while the HP is there
                icon.showturtle()               # Keep every slot visible so losses are readable
            score_x = geo['x'] + geo['dir'] * (MAX_HP * HEART_STEP + 4) # Score sits after the hearts
        else:                                   # TEXT FALLBACK
            _text.color(pl.color_main)          # Player color
            _text.goto(geo['x'], HEART_Y - 6)   # Position the text hearts
            _text.write('<3 ' * max(0, pl.hp), align=geo['align'], font=(FONT, 13, 'bold'))
            score_x = geo['x'] + geo['dir'] * (MAX_HP * 26) # Score sits after the text hearts

        _text.color(pl.color_main)              # Name and score in the player color
        _text.goto(score_x, HEART_Y - 7)        # Position the line
        _text.write('{}  {}'.format(pl.name, pl.score), align=geo['align'], font=(FONT, 14, 'bold'))

        ratio = max(0.0, min(1.0, pl.skill / SKILL_MAX)) # Clamp the skill fraction
        _skill_bar(geo['bar_x'], ratio, pl.color_main)   # Draw the bar

        tags = []                               # Active skill tags (STUN now lives over the snake)
        if pl.boost_timer > 0:                  # Speed Boost running
            tags.append('BOOST')
        if pl.invis_timer > 0:                  # Invisibility running
            tags.append('CLOAK')
        if tags:                                # Only write when something is active
            _text.color('#dddddd')              # Light gray
            _text.goto(geo['bar_x'] + (BAR_W + 8 if geo['dir'] > 0 else -8), BAR_Y) # Beside the bar
            _text.write(' '.join(tags), align='left' if geo['dir'] > 0 else 'right',
                        font=(FONT, 10, 'bold'))

    _text.color('gray')                         # Center strip
    _text.goto(0, 243)                          # Above the arena, centered
    _text.write('FIRST TO {}'.format(TARGET_SCORE), align='center', font=(FONT, 12, 'bold'))
    _text.color(HINT_COLOR)                     # Dim control hints
    _text.goto(0, -272)                         # Inside the arena bottom so it is never clipped
    _text.write('P1: WASD  Q=Boost E=Cloak     |     P2: Arrows  O=Boost P=Cloak     |     M=' + sfx.status(),
                align='center', font=(FONT, 10, 'normal'))


def draw_stun_bars(players):                    # Floating stun bar above each stunned snake
    _over.clear()                               # Wipe last frame's bars
    for pl in players:                          # Check both players
        if pl.stun <= 0:                        # Not stunned: nothing to draw
            continue
        ratio = min(1.0, pl.stun / STUN_FRAMES) # Remaining stun as a fraction
        left = pl.head.xcor() - STUN_BAR_W / 2  # Center the bar on the head
        bottom = pl.head.ycor() + STUN_BAR_LIFT # Float it above the head
        _rect(_over, left, bottom, STUN_BAR_W, STUN_BAR_H, fill=STUN_BAR_BG)          # Empty track
        _rect(_over, left, bottom, STUN_BAR_W * ratio, STUN_BAR_H, fill=STUN_BAR_FILL) # Remaining stun


def clear_overlay():                            # Remove the stun bars (result screen / restart)
    _over.clear()                               # Wipe the graphics
