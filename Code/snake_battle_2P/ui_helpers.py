"""
ui_helpers.py - reusable drawing helpers (cards, labels, mini snake preview,
button shapes) plus the one-time shape registrations used by menu.py and
character_select.py.
"""

import turtle
import math
from scene_manager import wn

def rounded_card(cx, cy, w, h, corner, fill_color, border_color, border_w=3):
    """Background card with 45-degree cut corners (stand-in for rounded corners)."""
    t = turtle.Turtle()
    t.hideturtle()
    t.penup()
    t.speed(0)
    t.color(border_color, fill_color)
    t.pensize(border_w)
    diag = corner * 1.41421
    t.goto(cx - w / 2 + corner, cy - h / 2)
    t.setheading(0)
    t.pendown()
    t.begin_fill()
    for _ in range(2):
        t.forward(w - 2 * corner)
        t.left(45); t.forward(diag); t.left(45)
        t.forward(h - 2 * corner)
        t.left(45); t.forward(diag); t.left(45)
    t.end_fill()
    return t

def header_strip(cx, cy, w, h, color_, text_, text_color='white'):
    t = turtle.Turtle()
    t.hideturtle()
    t.penup()
    t.color(color_, color_)
    t.goto(cx - w / 2, cy)
    t.setheading(0)
    t.pendown()
    t.begin_fill()
    for _ in range(2):
        t.forward(w)
        t.left(90)
        t.forward(h)
        t.left(90)
    t.end_fill()
    label = turtle.Turtle()
    label.hideturtle()
    label.penup()
    label.color(text_color)
    label.goto(cx, cy + h / 2 - 10)
    label.write(text_, align='center', font=('Courier', 14, 'bold'))

def draw_label(x, y, text_, size=14, color_='white'):
    t = turtle.Turtle()
    t.hideturtle()
    t.penup()
    t.color(color_)
    t.goto(x, y)
    t.write(text_, align='center', font=('Courier', size, 'bold'))
    return t

def circle_points(radius, segments=10):
    return tuple(
        (radius * math.cos(2 * math.pi * i / segments),
         radius * math.sin(2 * math.pi * i / segments))
        for i in range(segments)
    )

def make_head_shape(skin_color, band_color1, band_color2):
    head = turtle.Shape('compound')
    outline = ((-16, -6), (-10, -10), (0, -10), (10, -6),
               (16, 0), (10, 6), (0, 10), (-10, 10), (-16, 6))
    head.addcomponent(outline, skin_color, 'black')
    band1 = ((-16, -6), (-6, -8), (-6, -2), (-16, 0))
    band2 = ((-16, 0), (-6, -2), (-6, 4), (-16, 6))
    head.addcomponent(band1, band_color1, band_color1)
    head.addcomponent(band2, band_color2, band_color2)
    eye = circle_points(2)
    head.addcomponent(tuple((x + 6, y + 5) for x, y in eye), 'black', 'black')
    head.addcomponent(tuple((x + 6, y - 5) for x, y in eye), 'black', 'black')
    return head

def draw_mini_snake(cx, cy, head_shape, body_colors):
    head = turtle.Turtle()
    head.shape(head_shape)
    head.shapesize(2.4, 2.4)
    head.penup()
    head.goto(cx, cy)
    offsets = [(-24, -8), (-42, -22), (-52, -40), (-52, -60)]
    for (dx, dy), color_ in zip(offsets, body_colors):
        seg = turtle.Turtle()
        seg.shape('square')
        seg.shapesize(1.1, 1.1)
        seg.color(color_)
        seg.penup()
        seg.goto(cx + dx, cy + dy)

def register_rect_shape(name, w, h, fill, border):
    """Rectangle compound shape used for clickable menu buttons."""
    shape = turtle.Shape('compound')
    poly = ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))
    shape.addcomponent(poly, fill, border)
    wn.register_shape(name, shape)

# --- One-time global shape registration (runs once, the first time this module is imported) ---
wn.register_shape('p1_head', make_head_shape('mediumseagreen', 'red', 'white'))
wn.register_shape('p2_head', make_head_shape('steelblue', 'navy', 'white'))

_bolt = turtle.Shape('compound')
_bolt.addcomponent(((-2, 10), (3, 10), (-1, 1), (5, 1), (-5, -10), (-2, -1), (-6, -1)),
                    'yellow', 'yellow')
wn.register_shape('speed_icon', _bolt)

_eye = turtle.Shape('compound')
_eye.addcomponent(((-10, 0), (-5, 6), (5, 6), (10, 0), (5, -6), (-5, -6)), 'white', 'white')
_eye.addcomponent(circle_points(3), 'black', 'black')
_eye.addcomponent(((-10, -8), (-8, -10), (10, 8), (8, 10)), 'red', 'red')
wn.register_shape('stealth_icon', _eye)