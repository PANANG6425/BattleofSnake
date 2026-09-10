"""
engine.py - SECTION 1: Screen Setup, plus everything shared by every screen:
sprite loading, scene switching and drawing helpers. Sound lives in audio.py.

turtle traps encoded here - each one cost a real bug, do not "simplify" them away:

  * turtle's Screen is a SINGLETON. This module creates the one and only Screen, so
    it must be imported before any Turtle is built.
  * A shape turtle's cursor is redrawn with tag_raise EVERY frame, so it always
    floats above pen drawings and write() text. Anything that needs text on top of
    it must be pen-drawn (filled_rect) with clicks hit-tested (inside_rect).
  * onclick() binds to turtle.turtle._item, which is a LIST for a compound shape:
    tag_bind then matches nothing for any shape with 2+ components. Hit-test
    screen clicks instead.
  * Shapes rotate by (heading - 90) because turtle's built-ins are authored nose-up.
    Shapes here are authored in screen coordinates, so display them via shape_turtle().
  * Image shapes cannot rotate, scale OR be tinted. Hence 4 head files per direction,
    file pixel size == game size, and colour baked into the art.
  * clear_all_turtles() must delete the canvas items and unregister the turtle, or
    every scene switch leaks ~26 turtles and ~78 canvas items forever.
"""

import math
import os
import tkinter
import tkinter.font as tkfont
import turtle

from config import (TITLE, BG_COLOR, WIN_W, WIN_H, ASSET_DIR as _ASSET_SUBDIR,
                    USE_SPRITES, FONT_CANDIDATES, WINDOW_ICON, BAR_FRAME,
                    BUTTON_FILL, TEXT_BRIGHT)

# ===========================================
# SECTION 1: SCREEN SETUP
# ===========================================
wn = turtle.Screen()
wn.title(TITLE)
wn.bgcolor(BG_COLOR)
wn.setup(width=WIN_W, height=WIN_H)
wn.tracer(0)                                    # Manual updates: one wn.update() per frame

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, _ASSET_SUBDIR)

_root = wn.getcanvas().winfo_toplevel()         # The real Tk window behind the Screen


def _pick_font():
    """First font in config.FONT_CANDIDATES that this machine actually has.

    tkinter silently substitutes a missing family, so asking Tk which families exist
    is the only way to know what you really got.
    """
    try:
        have = set(tkfont.families())
    except Exception:
        return FONT_CANDIDATES[-1]
    for name in FONT_CANDIDATES:
        if name in have:
            return name
    return FONT_CANDIDATES[-1]


FONT = _pick_font()                             # Every write() in the game uses this


def _set_window_icon():
    """Replace tkinter's feather with assets/<icon>, if one is there.

    .png / .gif go through iconphoto (Tk 8.6+). .ico only works through iconbitmap,
    and only on Windows. A missing or unreadable file is not an error - the default
    icon just stays.
    """
    for name in WINDOW_ICON:
        path = os.path.join(ASSET_DIR, name)
        if not os.path.isfile(path):
            continue
        if name.lower().endswith('.ico'):
            try:
                _root.iconbitmap(path)          # Windows only
                return name
            except Exception:
                continue
        try:
            photo = tkinter.PhotoImage(file=path)
            _root.iconphoto(True, photo)
            _root._game_icon = photo            # Keep a reference or Tk drops it
            return name
        except Exception:
            continue
    return None


WINDOW_ICON_USED = _set_window_icon()


def new_pen(color=None, visible=False):
    """An invisible, pen-up drawing turtle - the workhorse for all pen drawing."""
    pen = turtle.Turtle()
    pen.penup()
    if not visible:
        pen.hideturtle()
    if color:
        pen.color(color)
    return pen


# ===========================================
# SECTION 1B: SPRITE LOADING
# ===========================================
_shape_cache = {}                               # name -> registered path, or None


def load_shape(name):
    """Register assets/<name>.gif with turtle and return its shape name, else None.

    A .png is converted to .gif once (needs Pillow), because turtle only accepts GIF.
    Missing or broken files return None so callers can fall back to coloured squares.
    """
    if not USE_SPRITES:
        return None
    if name in _shape_cache:
        return _shape_cache[name]
    gif_path = os.path.join(ASSET_DIR, name + '.gif')
    if not os.path.isfile(gif_path):
        png_path = os.path.join(ASSET_DIR, name + '.png')
        if os.path.isfile(png_path):
            try:
                # Pillow is an OPTIONAL dependency, imported here and nowhere else in
                # the game. This branch only runs when someone drops a .png into
                # assets/ with no matching .gif; without Pillow the except below just
                # falls back to coloured squares. Pylance flags the import as
                # unresolved when Pillow is not installed - that is expected.
                from PIL import Image, ImageOps  # type: ignore[import-not-found]
                src = Image.open(png_path).convert('RGBA')
                alpha = src.split()[3].point(lambda v: 255 if v > 128 else 0)
                pal = src.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255)
                pal.paste(255, mask=ImageOps.invert(alpha))
                pal.save(gif_path, transparency=255)
            except Exception:
                _shape_cache[name] = None
                return None
        else:
            _shape_cache[name] = None
            return None
    try:
        wn.addshape(gif_path)
        _shape_cache[name] = gif_path
        return gif_path
    except Exception:
        # Deliberately broad. addshape() raises tkinter.TclError - NOT
        # TurtleGraphicsError - for a truncated GIF or a .png renamed .gif, which is
        # exactly what happens when someone drops in their own art. Catching only
        # TurtleGraphicsError let that crash the whole scene, and because the cache
        # was never written every retry crashed again.
        _shape_cache[name] = None
        return None


# ===========================================
# SECTION 1C: SCENE MANAGER
# ===========================================
# Every key used anywhere, unbound at the start of every scene so a leftover handler
# from the previous screen can never fire on the new one.
ALL_KEYS = ['Up', 'Down', 'Left', 'Right', 'w', 'a', 's', 'd',
            'q', 'e', 'o', 'p', 'r', 'm', 'x', 'space', 'Return', '1', '2', 'Escape']

STATE = {'epoch': 0}                            # Bumped on every switch; loops self-stop


def unbind_all_keys():
    for k in ALL_KEYS:
        wn.onkeypress(None, k)
    wn.onscreenclick(None)                      # Buttons hit-test screen clicks too


def clear_all_turtles():
    """Destroy every turtle from the previous scene.

    Hiding is not enough: a hidden turtle stays in wn._turtles forever and keeps its
    canvas items. Each turtle owns three - drawingLineItem, currentLineItem (clear()
    makes a FRESH one every call) and the cursor, which is a LIST for a compound
    shape. Missing any of them leaked, and missing the list left every compound shape
    painted on screen forever, because with tracer(0) hideturtle() only takes effect
    on the next update() - which never comes once the turtle is unregistered.
    """
    registry = getattr(wn, '_turtles', None)
    for t in list(turtle.turtles()):
        try:
            t.onclick(None)
            t.clear()
            t.hideturtle()
            t.penup()
        except Exception:
            pass

        doomed = list(getattr(t, 'items', ()))
        doomed += list(getattr(t, 'stampItems', ()))
        doomed.append(getattr(t, 'drawingLineItem', None))
        doomed.append(getattr(t, '_fillitem', None))
        cursor = getattr(t.turtle, '_item', None)
        if isinstance(cursor, (list, tuple)):
            doomed += list(cursor)
        else:
            doomed.append(cursor)

        for item in doomed:
            if item is None:
                continue
            try:
                wn._delete(item)                # Private API, guarded
            except Exception:
                pass
        if registry is not None:
            try:
                registry.remove(t)
            except ValueError:
                pass


def go_to_scene(builder, *args, **kwargs):
    """The one entry point for every scene transition."""
    STATE['epoch'] += 1
    unbind_all_keys()
    clear_all_turtles()
    wn.bgcolor(BG_COLOR)
    builder(STATE['epoch'], *args, **kwargs)


# ===========================================
# SECTION 1D: DRAWING HELPERS
# ===========================================
def draw_label(x, y, text_, size=14, color_='white'):
    t = new_pen()
    t.color(color_)
    t.goto(x, y)
    t.write(text_, align='center', font=(FONT, size, 'bold'))
    return t


def filled_rect(cx, cy, w, h, fill_color, border_color, border_w=3):
    """Pen-drawn rectangle. Use this, not a shape turtle, when text must sit on top."""
    t = new_pen()
    t.speed(0)
    t.color(border_color, fill_color)
    t.pensize(border_w)
    t.goto(cx - w / 2, cy - h / 2)
    t.setheading(0)
    t.pendown()
    t.begin_fill()
    for _ in range(2):
        t.forward(w)
        t.left(90)
        t.forward(h)
        t.left(90)
    t.end_fill()
    t.penup()
    return t


def rounded_card(cx, cy, w, h, corner, fill_color, border_color, border_w=3):
    """Card with 45-degree cut corners, standing in for rounded ones."""
    t = new_pen()
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
    t = new_pen()
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
    label = new_pen()
    label.color(text_color)
    label.goto(cx, cy + h / 2 - 10)
    label.write(text_, align='center', font=(FONT, 14, 'bold'))


def stroke_box(pen, cx, cy, w, h, edge, width):
    """Outline only, on a caller-owned pen so it can be cleared and redrawn."""
    pen.color(edge)
    pen.pensize(width)
    pen.penup()
    pen.goto(cx - w / 2, cy - h / 2)
    pen.setheading(0)
    pen.pendown()
    for _ in range(2):
        pen.forward(w)
        pen.left(90)
        pen.forward(h)
        pen.left(90)
    pen.penup()


def fill_box(pen, cx, cy, w, h, color, edge=None):
    """Filled rectangle on a caller-owned pen. edge defaults to the fill colour."""
    pen.color(edge or color, color)
    pen.penup()
    pen.goto(cx - w / 2, cy - h / 2)
    pen.setheading(0)
    pen.pendown()
    pen.begin_fill()
    for _ in range(2):
        pen.forward(w)
        pen.left(90)
        pen.forward(h)
        pen.left(90)
    pen.end_fill()
    pen.penup()


def write_at(pen, x, y, text_, size, color, align='center'):
    pen.color(color)
    pen.goto(x, y)
    pen.write(text_, align=align, font=(FONT, size, 'bold'))


def draw_skill_bar(pen, left, bottom, w, h, ratio, color):
    """Grey frame plus a filled bar. Shared by both game modes."""
    pen.penup()
    pen.goto(left, bottom)
    pen.setheading(0)
    pen.pensize(2)
    pen.color(BAR_FRAME)
    pen.pendown()
    for _ in range(2):
        pen.forward(w)
        pen.left(90)
        pen.forward(h)
        pen.left(90)
    pen.penup()
    fill_w = (w - 4) * max(0.0, min(1.0, ratio))
    if fill_w >= 1:
        pen.goto(left + 2, bottom + 2)
        pen.color(color)
        pen.pendown()
        pen.begin_fill()
        for _ in range(2):
            pen.forward(fill_w)
            pen.left(90)
            pen.forward(h - 4)
            pen.left(90)
        pen.end_fill()
        pen.penup()


def inside_rect(x, y, cx, cy, w, h):
    """Point-in-rectangle, for hit-testing screen clicks."""
    return abs(x - cx) <= w / 2 and abs(y - cy) <= h / 2


def shape_turtle(name, x, y, size=None):
    """Create a turtle that DISPLAYS a compound shape, correctly oriented.

    heading 90 cancels turtle's (heading - 90) shape rotation, which otherwise turns
    every screen-authored shape 90 degrees clockwise.
    """
    t = turtle.Turtle()
    t.penup()                                   # penup BEFORE goto, or the move draws
    t.setheading(90)
    try:
        t.shape(name)
    except turtle.TurtleGraphicsError:
        # An unregistered shape name. A new POWERS entry whose icon nobody drew yet used
        # to abort Character Select mid-build, leaving a dead half-drawn screen; a grey
        # placeholder keeps the registry "data only" as config.py promises.
        t.shape('square')
        t.color('#5a5a6b')
    if size is not None:
        t.shapesize(size, size)
    t.goto(x, y)
    return t


def icon_shape(name):
    """assets/<name>.gif if it exists, otherwise the drawn shape registered as `name`.

    Section 1E below registers a drawn icon under each name config.POWERS asks for.
    Dropping <name>.gif into assets/ therefore swaps in real art with no code or
    config change, and deleting the file puts the drawn icon straight back.

    Note the sizes are NOT interchangeable: shapesize() is ignored on an image shape,
    so a .gif icon appears at its own pixel size while the drawn one still scales.
    That is why import_assets.py writes the power icons at exactly one size.
    """
    return load_shape(name) or name


class ImageButton:
    """A clickable button - art from assets/<name>.gif, or a drawn box if it is missing.

    One object because a button is two things that have to agree: something visible
    and a rectangle to hit-test. turtle will not link them for you -

      * onclick() binds nothing at all on a shape with 2+ components, and an image
        shape is not clickable in a way that survives a scene rebuild, so clicks are
        hit-tested against `hit()` from wn.onscreenclick like every other button here
      * a shape turtle is raised above pen drawings every frame, so the fallback box
        is pen-drawn with its label on top, and the image variant has its label baked
        into the art instead
    """

    def __init__(self, name, cx, cy, w, h, label=None, color=TEXT_BRIGHT, fill=None):
        self.cx, self.cy, self.w, self.h = cx, cy, w, h
        sprite = load_shape(name)
        self.turtle = shape_turtle(sprite, cx, cy) if sprite else None
        if self.turtle is None:                 # No art: draw the button instead
            filled_rect(cx, cy, w, h, fill or BUTTON_FILL, color, 3)
            if label:
                draw_label(cx, cy - 7, label, 14, color)

    def hit(self, x, y):
        return inside_rect(x, y, self.cx, self.cy, self.w, self.h)

    def hide(self):
        if self.turtle is not None:
            self.turtle.hideturtle()


def click_router(*buttons_and_actions):
    """Turn (button, action) pairs into one wn.onscreenclick handler.

    Every screen needs the same loop, and getting it wrong means a dead button, so
    it lives here once.
    """
    def on_click(x, y):
        for button, action in buttons_and_actions:
            if button.hit(x, y):
                action()
                return
    return on_click


# ===========================================
# SECTION 1E: COMPOUND SHAPES
# ===========================================
def circle_points(radius, segments=10):
    return tuple((radius * math.cos(2 * math.pi * i / segments),
                  radius * math.sin(2 * math.pi * i / segments))
                 for i in range(segments))


def make_head_shape(skin_color, band_color1, band_color2):
    """Snake head facing right, used for the Character Select portrait."""
    head = turtle.Shape('compound')
    head.addcomponent(((-16, -6), (-10, -10), (0, -10), (10, -6),
                       (16, 0), (10, 6), (0, 10), (-10, 10), (-16, 6)), skin_color, 'black')
    head.addcomponent(((-16, -6), (-6, -8), (-6, -2), (-16, 0)), band_color1, band_color1)
    head.addcomponent(((-16, 0), (-6, -2), (-6, 4), (-16, 6)), band_color2, band_color2)
    eye = circle_points(2)
    head.addcomponent(tuple((x + 6, y + 5) for x, y in eye), 'black', 'black')
    head.addcomponent(tuple((x + 6, y - 5) for x, y in eye), 'black', 'black')
    return head


_bolt = turtle.Shape('compound')                # SPEED
_bolt.addcomponent(((-2, 10), (3, 10), (-1, 1), (5, 1), (-5, -10), (-2, -1), (-6, -1)),
                   'yellow', 'yellow')
wn.register_shape('speed_icon', _bolt)

_eye = turtle.Shape('compound')                 # STEALTH
_eye.addcomponent(((-10, 0), (-5, 6), (5, 6), (10, 0), (5, -6), (-5, -6)), 'white', 'white')
_eye.addcomponent(circle_points(3), 'black', 'black')
_eye.addcomponent(((-10, -8), (-8, -10), (10, 8), (8, 10)), 'red', 'red')
wn.register_shape('stealth_icon', _eye)

_shield = turtle.Shape('compound')              # SHIELD
_shield.addcomponent(((-9, 9), (9, 9), (9, -1), (0, -10), (-9, -1)), '#6fb7ff', '#1c4a7a')
_shield.addcomponent(((-4, 6), (4, 6), (4, 0), (0, -5), (-4, 0)), '#eaf5ff', '#eaf5ff')
wn.register_shape('shield_icon', _shield)

_phase = turtle.Shape('compound')               # PHASE: arrow through a wall
_phase.addcomponent(((-2, 10), (2, 10), (2, -10), (-2, -10)), '#5a5a6e', '#5a5a6e')
_phase.addcomponent(((-10, 2), (3, 2), (3, 5), (10, 0), (3, -5), (3, -2), (-10, -2)),
                    '#c86ef0', '#efd6ff')
wn.register_shape('phase_icon', _phase)

_feast = turtle.Shape('compound')               # FEAST: fruit with a sparkle
_feast.addcomponent(tuple((x, y - 1) for x, y in circle_points(8, 12)), '#e8203a', '#7a0a18')
_feast.addcomponent(((0, 7), (2, 11), (6, 9), (3, 13), (5, 16), (0, 14), (-4, 16),
                     (-2, 13), (-5, 9), (-2, 11)), '#ffe08a', '#ffe08a')
wn.register_shape('feast_icon', _feast)
