"""
Snake Battle - 1 Player and 2 Player local multiplayer, Python turtle only.

Run this file:  python snake_battle.py

Baseline kit layout, top to bottom:
    SECTION 1  Screen Setup .......... the one turtle Screen, sprites, scenes, drawing
    SECTION 2  Game Entities ......... the Snake both modes use, powers, fruit
    SECTION 3  Parameters & Physics .. every tunable number, characters, powers
    SECTION 4  Input Handling ........ inside each screen and each game mode
    SECTION 5  Main Game Loop ........ wn.ontimer(game_loop, FRAME_MS) in each mode

Sections 4 and 5 belong to a screen, not to the file, because this game has four of
them (Main Menu, Character Select, 1 Player, 2 Player Battle). Each one binds its own
keys and, for the two game modes, runs its own loop.

turtle + the standard library only. Pillow is needed only to regenerate the sprites
in assets/, and no audio is generated at all - drop .wav files into assets/sounds/
to switch sound on. See MANUAL.md.
"""

import math
import os
import random
import shutil
import subprocess
import tkinter
import tkinter.font as tkfont
import turtle
import wave


# =============================================================================
# SECTION 1: SCREEN SETUP
# =============================================================================
# Window, asset folder, font and icon - read by the Screen a few lines below, so
# they have to be declared before it. BG_COLOR and TEXT_BRIGHT are here for the
# same reason (TEXT_BRIGHT is a default argument of ImageButton); the rest of the
# colour theme lives with the other tunables in SECTION 3.

# ===========================================
# SECTION 1A: CONSTANTS THE SCREEN NEEDS
# ===========================================
WIN_W, WIN_H = 800, 600
TITLE = 'Snake Game'
FRAME_MS = 16                                   # ~60 FPS

ASSET_DIR = 'assets'
USE_SPRITES = True                              # False forces plain coloured squares

# Font: the FIRST name actually installed wins, so one list works on every machine.
# _pick_font() resolves it at startup and every write() uses the winner, FONT.
# Put your preferred font first; keep a generic monospace last as the safety net.
FONT_CANDIDATES = ['Consolas', 'Cascadia Mono', 'Courier New', 'DejaVu Sans Mono',
                   'Liberation Mono', 'Courier']

# Window icon, replacing tkinter's feather. First file found in assets/ wins.
# .png / .gif work everywhere (Tk 8.6+); .ico only on Windows. Drop your logo in
# assets/ under one of these names - if none exist the default feather stays.
WINDOW_ICON = ['icon.png', 'icon.gif', 'logo.png', 'logo.gif', 'icon.ico']
BG_COLOR = 'black'                              # Arena background
TEXT_BRIGHT = 'white'

# =============================================================================
# SECTION 1 NOTES: THE TURTLE TRAPS ENCODED BELOW
# =============================================================================
# sprite loading, scene switching and drawing helpers.
#
# turtle traps encoded here - each one cost a real bug, do not "simplify" them away:
#
#   * turtle's Screen is a SINGLETON. This module creates the one and only Screen, so
#     it must be imported before any Turtle is built.
#   * A shape turtle's cursor is redrawn with tag_raise EVERY frame, so it always
#     floats above pen drawings and write() text. Anything that needs text on top of
#     it must be pen-drawn (filled_rect) with clicks hit-tested (inside_rect).
#   * onclick() binds to turtle.turtle._item, which is a LIST for a compound shape:
#     tag_bind then matches nothing for any shape with 2+ components. Hit-test
#     screen clicks instead.
#   * Shapes rotate by (heading - 90) because turtle's built-ins are authored nose-up.
#     Shapes here are authored in screen coordinates, so display them via shape_turtle().
#   * Image shapes cannot rotate, scale OR be tinted. Hence 4 head files per direction,
#     file pixel size == game size, and colour baked into the art.
#   * clear_all_turtles() must delete the canvas items and unregister the turtle, or
#     every scene switch leaks ~26 turtles and ~78 canvas items forever.

_ASSET_SUBDIR = ASSET_DIR

# ===========================================
# SECTION 1B: THE SCREEN, FONT & WINDOW ICON
# ===========================================
wn = turtle.Screen()
wn.title(TITLE)
wn.bgcolor(BG_COLOR)
wn.setup(width=WIN_W, height=WIN_H)
wn.tracer(0)                                    # Manual updates: one wn.update() per frame

# Art lives in assets/. This file can sit either beside that folder or one level
# above it (next to snake_battle_2P/), so find it instead of assuming.
_HERE = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = _HERE
for _c in (_HERE, os.path.join(_HERE, 'snake_battle_2P')):
    if os.path.isdir(os.path.join(_c, _ASSET_SUBDIR)):
        BASE_DIR = _c
        break
ASSET_DIR = os.path.join(BASE_DIR, _ASSET_SUBDIR)

_root = wn.getcanvas().winfo_toplevel()         # The real Tk window behind the Screen


def _pick_font():
    """First font in FONT_CANDIDATES that this machine actually has.

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
# SECTION 1C: SPRITE LOADING
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
# SECTION 1D: SCENE MANAGER
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
# SECTION 1E: DRAWING HELPERS
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
        # placeholder keeps the POWERS registry "data only", as it promises.
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
# SECTION 1F: COMPOUND SHAPES
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

# =============================================================================
# SECTION 2: GAME ENTITIES INITIALIZATION
# =============================================================================
# The Snake both game modes use, plus the power runtime that drives it.
#
# Power state is ONE dict on the snake - {power key -> frames left} - so a new power
# in POWERS needs no new attribute here. The game asks about effects by KIND
# (powers_flag / powers_effect), never by power name.

DIRECTIONS = {'up': (0, 1), 'down': (0, -1), 'left': (-1, 0), 'right': (1, 0)}
OPPOSITE = {'up': 'down', 'down': 'up', 'left': 'right', 'right': 'left'}


# ===========================================
# SECTION 2A: POWER RUNTIME
# ===========================================
def powers_init(snake):
    snake.effects = {}


def powers_tick(snake):
    """Count every active effect down one frame."""
    for key in list(snake.effects):
        snake.effects[key] -= 1
        if snake.effects[key] <= 0:
            del snake.effects[key]


def powers_activate(snake):
    """Spend the bar and start the chosen power. True if it actually fired."""
    pw = snake.power
    if snake.effects.get(pw['key'], 0) > 0:     # Already running
        return False
    if snake.skill < pw['cost']:
        return False
    snake.skill -= pw['cost']
    snake.effects[pw['key']] = pw['duration']
    return True


def _active(snake):
    return [power(k) for k in snake.effects]


def powers_flag(snake, name):
    """True if any active power sets this boolean effect."""
    return any(p['effect'].get(name) for p in _active(snake))


def powers_effect(snake, name, default=1.0):
    """The strongest value any active power gives for this numeric effect."""
    values = [p['effect'][name] for p in _active(snake) if name in p['effect']]
    return max(values) if values else default


def powers_hud_tags(snake):
    return [p['hud'] for p in _active(snake)]


# ===========================================
# SECTION 2B: THE SNAKE
# ===========================================
class Snake:
    """One snake: sprites, movement, body layout and power state.

    `slot` is the seat ('P1' / 'P2') and drives which side of the HUD it uses.
    `char_key` is the chosen character and doubles as the sprite filename prefix -
    separate, because either seat can pick any character.

    Head and body sprites are decided SEPARATELY. turtle cannot tint an image shape,
    so a .gif carries its own colour; shipping head gifs but no <key>_body.gif keeps
    the body a coloured square that config.CHARACTERS can still recolour.
    """

    def __init__(self, slot, char_key, start_pos, start_dir, power_key,
                 base_speed, max_hp, head_scale=0.8, body_scale=0.65):
        ch = character(char_key)
        self.slot = slot
        self.name = slot
        self.char_name = ch['name']
        self.key = ch['key']
        self.color_main = ch['main']
        self.color_dim = ch['dim']
        self.start_pos = start_pos
        self.start_dir = start_dir
        self.base_speed = base_speed
        self.max_hp = max_hp
        self.head_scale = head_scale
        self.body_scale = body_scale

        self.power = power(power_key)
        self.skill_tag = self.power['tag']      # Short label for the HUD

        key = self.key
        self.head_sprites = {d: load_shape('{}_head_{}'.format(key, d)) for d in DIRECTIONS}
        self.ghost_sprites = {d: load_shape('{}_head_{}_ghost'.format(key, d)) for d in DIRECTIONS}
        self.body_sprite = load_shape('{}_body'.format(key))
        self.use_head_sprites = all(self.head_sprites.values())
        self.use_body_sprite = self.body_sprite is not None

        self.head = turtle.Turtle()
        self.head.penup()
        if self.use_head_sprites:
            self.head.shape(self.head_sprites[start_dir])
        else:
            self.head.shape('square')
            self.head.color(self.color_main)
            self.head.shapesize(head_scale, head_scale)

        # The stamper's shape is set per stamp group in render(), because body and
        # head can be different kinds (image vs coloured square).
        self.stamper = new_pen()
        self.reset()

    def reset(self):
        self.head.goto(*self.start_pos)
        if not self.use_head_sprites:
            self.head.color(self.color_main)
        self.head.showturtle()
        self.direction = self.start_dir
        self.facing = self.start_dir
        self.length = START_LENGTH
        self.path = [self.start_pos]
        self.hp = self.max_hp
        self.score = 0
        self.skill = 0
        self.speed = self.base_speed
        self.stun = 0
        self.invuln = 0
        self.self_hit_grace = 0                 # Frames a self hit cannot retrigger
        self.bite_grace = 0                     # Frames a BITE cannot punish this snake.
                                                # Set on the winner of a head clash: the
                                                # loser is stunned right there, so the
                                                # winner's head is left sitting on its
                                                # neck and would be charged for biting
                                                # the clash it just won.
        powers_init(self)
        self.stamper.clearstamps()

    # ---------- body layout ----------
    def segments(self):
        """Body positions, nearest the head first.

        Walks the path BACKWARDS accumulating distance rather than counting frames,
        or the body spreads apart while SPEED is active.
        """
        points = []
        target = SEG_SPACING
        travelled = 0.0
        prev = self.path[-1]
        for i in range(len(self.path) - 2, -1, -1):
            cur = self.path[i]
            travelled += abs(cur[0] - prev[0]) + abs(cur[1] - prev[1])
            prev = cur
            while travelled >= target and len(points) < self.length:
                points.append(cur)
                target += SEG_SPACING
            if len(points) >= self.length:
                break
        return points

    # ---------- input ----------
    def turn(self, new_dir):
        if self.direction != OPPOSITE[new_dir]:
            self.direction = new_dir
            self.facing = new_dir

    def use_power(self):
        """One key per player fires whichever power was picked."""
        return powers_activate(self)

    # ---------- per frame ----------
    def tick_timers(self):
        if self.stun > 0: self.stun -= 1
        if self.invuln > 0: self.invuln -= 1
        if self.self_hit_grace > 0: self.self_hit_grace -= 1
        if self.bite_grace > 0: self.bite_grace -= 1
        powers_tick(self)
        self.speed = self.base_speed * powers_effect(self, 'speed_mult', 1.0)

    def next_position(self):
        """Where the head would go this frame, without committing to it."""
        if self.stun > 0 or self.direction == 'stop':
            return None
        dx, dy = DIRECTIONS[self.direction]
        return self.head.xcor() + dx * self.speed, self.head.ycor() + dy * self.speed

    def commit(self, x, y):
        """Accept a move: place the head and trim the path to what segments() needs."""
        self.head.goto(x, y)
        self.path.append((round(x), round(y)))
        keep = int((self.length + 2) * SEG_SPACING / self.base_speed) + 8
        if len(self.path) > keep:
            del self.path[:-keep]

    def gain_fruit(self, score, grow, skill_gain):
        self.score += score
        self.length += grow
        self.skill = min(SKILL_MAX, self.skill + skill_gain)

    # ---------- drawing ----------
    def render(self):
        """Body first, head stamped LAST - canvas items keep creation order."""
        self.stamper.clearstamps()
        cloaked = powers_flag(self, 'cloak')
        blinking = self.invuln > 0 and (self.invuln // 4) % 2 == 0

        if not cloaked:                         # CLOAK hides the body entirely
            if self.use_body_sprite:
                self.stamper.shape(self.body_sprite)
            else:
                self.stamper.shape('square')
                self.stamper.color(self.color_main)     # Body colour from config
                self.stamper.shapesize(self.body_scale, self.body_scale)
            for pos in self.segments():
                self.stamper.goto(pos)
                self.stamper.stamp()

        if self.use_head_sprites:
            self.head.hideturtle()              # The sprite head is stamped, not shown
            if not blinking:                    # Blink = skip a frame after a hit
                use_ghost = cloaked and all(self.ghost_sprites.values())
                table = self.ghost_sprites if use_ghost else self.head_sprites
                self.stamper.shape(table[self.facing])
                self.stamper.goto(self.head.pos())
                self.stamper.stamp()
        else:
            self.head.showturtle()
            self.head.shape('square')
            self.head.shapesize(self.head_scale, self.head_scale)
            if cloaked:
                self.head.color(self.color_dim)
            elif blinking:
                self.head.color('white')
            else:
                self.head.color(self.color_main)

    def hide(self):
        self.head.hideturtle()
        self.stamper.clearstamps()


# ===========================================
# SECTION 2C: SHARED ENTITY BUILDERS
# ===========================================
_fruit_shapes = None                            # Resolved once, on the first fruit


def fruit_shapes():
    """Every fruit skin that actually loaded, best available first.

    Three tiers, so the game looks its best with the imported art and still runs
    with none of it: the config.FRUIT_VARIANTS drawings, then the single generated
    assets/fruit.gif, then nothing at all (make_fruit draws a red circle).
    """
    global _fruit_shapes
    if _fruit_shapes is None:
        _fruit_shapes = [s for s in (load_shape(n) for n in FRUIT_VARIANTS) if s]
        if not _fruit_shapes:
            plain = load_shape('fruit')
            _fruit_shapes = [plain] if plain else []
    return _fruit_shapes


def make_fruit():
    """One fruit turtle: a random fruit skin if any loaded, else a red circle."""
    shapes = fruit_shapes()
    f = turtle.Turtle()
    f.penup()
    if shapes:
        f.shape(random.choice(shapes))
    else:
        f.shape('circle')
        f.color('red')
        f.shapesize(0.7, 0.7)
    return f


def reroll_fruit(f):
    """Give a fruit a new random skin when it respawns. Cosmetic only.

    Called right after the fruit is moved. A no-op with one skin or none, so both
    game modes can call it unconditionally.
    """
    shapes = fruit_shapes()
    if len(shapes) > 1:
        f.shape(random.choice(shapes))

# =============================================================================
# SECTION 3: PARAMETERS & PHYSICS
# =============================================================================
# Every tunable number lives here, plus the two registries that make the game
# extensible without touching game code:
#
#     CHARACTERS  a skin: colour + sprite palette. Never affects balance.
#     POWERS      one power per player per match: cost, duration, effect.
#
# Nothing in this file imports anything, so it is safe to import from anywhere.

# ===========================================
# SECTION 3A: THEME - every colour in one place
# ===========================================
BG_MENU = '#0b0f14'                             # Menu / Character Select background

WALL_COLOR = 'gray'                             # Arena border
OBSTACLE_FILL = '#2b2b3a'
OBSTACLE_EDGE = '#5a5a6e'

BAR_FRAME = '#5a5a6b'                           # Skill bar outline
TEXT_MUTED = '#8a93a3'
TEXT_FAINT = '#4a4a4a'
TEXT_TAG = '#dddddd'                            # BOOST / CLOAK / STUN labels
TEXT_DIM = 'gray'                               # "FIRST TO 500", result hints
HIGHLIGHT = 'gold'                              # Selected power, PRESS ENTER

PANEL_BG = '#141b24'                            # Character Select panel
CARD_BG = '#0e141b'                             # Character card interior
CARD_EDGE = '#39424f'                           # Unselected outline
ARROW_COLOR = '#c7ccd4'                         # Flip arrows
BUTTON_FILL = '#1b2430'                         # Menu buttons
SLOT_COLOR = {'P1': 'mediumseagreen', 'P2': 'steelblue'}

# ===========================================
# SECTION 3B: SHARED GAMEPLAY (both modes)
# ===========================================
SEG_SPACING = 15                                # Pixels between body segment centres
WALL_MARGIN = 10                                # Half the head sprite: stops the snake
                                                # sinking into the border wall
START_LENGTH = 4
GROW_PER_FRUIT = 1
FRUIT_SCORE = 50
SKILL_MAX = 100

# Fruit skins. Purely cosmetic - every one is worth FRUIT_SCORE - and each respawn
# picks a fresh one at random. Names are assets/<name>.gif, written by
# import_assets.py from the drawings in ../../Asset/. Whichever files are missing
# are simply not offered; with none of them present the game falls back to
# assets/fruit.gif, and without that to a red circle.
FRUIT_VARIANTS = ['fruit_apple', 'fruit_banana', 'fruit_grape',
                  'fruit_guava', 'fruit_pineapple']

# ===========================================
# SECTION 3C: 1P MODE
# ===========================================
ARENA_1P = (-380, 380, -280, 235)               # left, right, bottom, top
                                                # top leaves room for the HUD bar
SPEED_1P = 4
SKILL_GAIN_1P = 20

# ===========================================
# SECTION 3D: 2P BATTLE MODE
# ===========================================
ARENA_2P = (-375, 375, -275, 205)               # Lower top edge: the HUD sits above it
SPEED_2P = 3                                    # Slower - two snakes share one arena
SKILL_GAIN_2P = 25

MAX_HP = 3
TARGET_SCORE = 800
ROUNDS_TO_WIN = 2                               # Rounds to take the match (best of 3)
MAX_ROUNDS = ROUNDS_TO_WIN * 2 - 1              # Hard stop: a match of all draws would
                                                # otherwise never reach ROUNDS_TO_WIN.
                                                # Level on rounds here -> MVP decides,
                                                # see match_champion()

# Every heart still standing at the end of a round is worth this much MVP on its own,
# so winning a round on hearts is never worth nothing even at a low score. MVP is
# score x hp + SURVIVE_BONUS x hp - see mvp_total().
SURVIVE_BONUS = 100

# --- The one place score changes hands --------------------------------------
# Collisions cost HEARTS, never points - except a head-to-head clash, where the snake
# that is AHEAD loses a heart and hands this share of its score to the snake behind.
# That is the whole reason to protect a lead by baiting instead of charging.
SCORE_TRANSFER = 0.5                            # 0.0 = no transfer, 1.0 = the lot

SELF_HIT_DAMAGE = 1                             # HP lost for running into your own body
                                                # (0 = stun only, the old behaviour)
STUN_FRAMES = 30                                # Frozen frames after a bump or self hit
SELF_HIT_GRACE_EXTRA = 40                       # Extra frames a self hit cannot retrigger
INVULN_FRAMES = 60                              # Immunity frames after taking damage
HIT_RADIUS = 12

OBSTACLE_COUNT = 6
OBSTACLE_SIZE = 60
OBSTACLE_SPOTS = [(-200, 65), (0, 65), (200, 65),
                  (-200, -135), (0, -135), (200, -135)]   # Symmetric 3x2 grid

FRUIT_COUNT_2P = 2
FRUIT_MIN_GAP = 40                              # Keep fruits apart

# ===========================================
# SECTION 3E: SOUND (no audio is generated - files are optional, see SoundManager)
# ===========================================
SOUND_ON = True                                 # X toggles in game
SOUND_DIR = 'sounds'                            # Subfolder of assets/ for .wav files
SOUND_VOLUME = 0.6                              # Only applied by the pygame backend
# Extra folders to search after assets/sounds/, relative to the code folder. The
# repo ships its .mp3 pack two levels up; change this if you move things.
EXTRA_SOUND_DIRS = ['../../sound_effect']
SOUND_DEBUG = False                             # True prints every playback failure

# ===========================================
# SECTION 3F: CHARACTER REGISTRY
# ===========================================
# All characters play IDENTICALLY - colour only. `key` is also the sprite filename
# prefix, so character 'p3' loads assets/p3_head_up.gif and assets/p3_body.gif.
# `palette` is (main, dark outline, light highlight, ghost main, ghost outline) and is
# used only to GENERATE sprites; `main` / `dim` are what the game draws with when a
# sprite file is missing. To add one: append an entry, run make_sprites.py.
# The roster is the two hand-drawn snakes, each in two colourways. Every one has a
# portrait at assets/<key>_portrait.gif; import_assets.PORTRAIT_ART decides which
# drawing and which hue rotation produces each, and `main` here is that costume's
# dominant colour so the arena sprite matches the card the player picked.
# Character Select falls back to the drawn head if a portrait file is missing, so
# nothing below depends on the art existing.
CHARACTERS = [
    {'key': 'p1', 'name': 'SIAM',   'main': '#e03131', 'dim': '#3f1010',   # Thai, red
     'palette': ('#e03131', '#7a1414', '#ffd0c0', '#4a1616', '#280b0b')},
    {'key': 'p2', 'name': 'SAKURA', 'main': '#4d6bff', 'dim': '#1b2450',   # Japan, blue
     'palette': ('#4d6bff', '#1b2f9a', '#cdd8ff', '#1f2a5e', '#111735')},
    {'key': 'p3', 'name': 'NAGA',   'main': '#2fd45a', 'dim': '#0f3a1c',   # Thai, green
     'palette': ('#2fd45a', '#12722c', '#c8ffd6', '#123d1e', '#0a2412')},
    {'key': 'p4', 'name': 'KOI',    'main': '#e04ce8', 'dim': '#3c0f40',   # Japan, magenta
     'palette': ('#e04ce8', '#7a1580', '#ffcdff', '#3f1044', '#240926')},
]
CHAR_DEFAULTS = ('p1', 'p2')                    # Pre-selected for P1 and P2:
                                                # Thai vs Japan, one of each drawing

# ===========================================
# SECTION 3G: POWER REGISTRY
# ===========================================
# `effect` IS the behaviour, written as EFFECT KINDS the game already applies:
#
#     speed_mult   float   head speed multiplier      (max of active)
#     score_mult   float   fruit score multiplier     (max of active)
#     cloak        bool    body hidden, head goes ghost
#     invincible   bool    incoming damage ignored
#     noclip       bool    obstacles and own body stop hurting
#
# A new power reusing these kinds is data only - append an entry, give it an icon,
# done. A genuinely new kind needs the key here plus one read via powers_flag() /
# powers_effect() at the one place that should honour it. Nothing hardcodes a name.
POWERS = [
    {'key': 'SPEED',   'name': 'SPEED',   'tag': 'SPD', 'hud': 'BOOST',
     'icon': 'speed_icon',   'blurb': 'Move twice as fast',
     'cost': 50, 'duration': 180, 'effect': {'speed_mult': 2.0}},
    {'key': 'STEALTH', 'name': 'STEALTH', 'tag': 'STL', 'hud': 'CLOAK',
     'icon': 'stealth_icon', 'blurb': 'Body vanishes, still solid',
     'cost': 50, 'duration': 180, 'effect': {'cloak': True}},
    {'key': 'SHIELD',  'name': 'SHIELD',  'tag': 'SHD', 'hud': 'SHIELD',
     'icon': 'shield_icon',  'blurb': 'Take no damage at all',
     'cost': 50, 'duration': 150, 'effect': {'invincible': True}},
    {'key': 'PHASE',   'name': 'PHASE',   'tag': 'PHS', 'hud': 'PHASE',
     'icon': 'phase_icon',   'blurb': 'Slip through boxes and your own tail',
     'cost': 50, 'duration': 150, 'effect': {'noclip': True}},
    {'key': 'FEAST',   'name': 'FEAST',   'tag': 'FST', 'hud': 'FEAST',
     'icon': 'feast_icon',   'blurb': 'Fruit is worth double',
     'cost': 40, 'duration': 240, 'effect': {'score_mult': 2.0}},
]
POWER_DEFAULTS = ('SPEED', 'STEALTH')           # Pre-selected for P1 and P2

# ===========================================
# SECTION 3H: LOOKUPS
# ===========================================
_CHAR_BY_KEY = {c['key']: c for c in CHARACTERS}
_POWER_BY_KEY = {p['key']: p for p in POWERS}


def character(key):
    """Look up a character, falling back to the first one for a bad key."""
    return _CHAR_BY_KEY.get(key, CHARACTERS[0])


def power(key):
    """Look up a power, falling back to the first one for a bad key."""
    return _POWER_BY_KEY.get(key, POWERS[0])

# =============================================================================
# SOUND EFFECTS (optional - the game is silent, not broken, without files)
# =============================================================================
# package is required.
#
# With no audio files present every play() is a no-op and the game runs unchanged, so
# this is safe to ship before any sound exists.
#
# TO SWITCH SOUND ON: put .wav files in assets/sounds/ named after the events below.
# On Windows those play through winsound, which is standard library - nothing to
# install. The repo's sound_effect/*.mp3 are only usable via the optional pygame
# backend, so without pygame they are ignored rather than half-played; report() says
# exactly that at startup.
#
# Nothing here may raise or block. A missing file, a broken file or a busy audio
# device must never take the game down with it.

# Code only: NO audio is generated and NO third-party package is required. With no
# audio files present every play() is a no-op and the game runs unchanged.
#
# To get sound: put .wav files in assets/sounds/ named after the events below. On
# Windows those play through winsound, which is standard library. The repo's
# sound_effect/*.mp3 are only usable via the optional pygame backend, so without it
# they are ignored rather than half-played - report() says so.
SOUND_PATH = os.path.join(ASSET_DIR, SOUND_DIR)
# Extra folders to search, resolved relative to this file. EXTRA_SOUND_DIRS
# keeps them configurable instead of hardcoding a path that walks out of the project.
EXTRA_PATHS = [os.path.abspath(os.path.join(BASE_DIR, d)) for d in EXTRA_SOUND_DIRS]

SOUND_EVENTS = {                                # event -> .mp3 candidates in the repo pack
    'eat':    ('eat_fruit.mp3', 'motion_eating.mp3'),
    'hit':    ('bomb.mp3',),
    'bump':   ('impact_wall.mp3',),
    'power':  ('increase_speed.mp3', 'skill_selection.mp3'),
    'score':  ('score.mp3',),
    'win':    ('result_fanfare.mp3',),
    'lose':   ('bomb.mp3',),
    'select': ('setting.mp3', 'skill_selection.mp3'),
    'start':  ('start_1.mp3', 'start_2.mp3', 'start_3.mp3'),
}
_WAV_NAMES = 'eat, hit, bump, power, score, win, lose, select, start'


def inspect_wav(path):
    """Is this .wav something winsound / the CLI players can actually play?

    Returns (ok, description). winsound needs plain PCM at 8 or 16 bits. The stdlib
    `wave` module refuses everything winsound refuses, which makes it a free
    pre-flight check:

        IEEE float32 .wav   -> "unknown extended format"   (Audacity's default export)
        MS ADPCM .wav       -> "unknown format: 2"
        an .mp3 renamed .wav-> "does not start with RIFF id"
        24-bit PCM          -> opens fine, but winsound will not play it

    This is why a file could be FOUND and still silent: PlaySound raised, and play()
    swallows exceptions on purpose so audio can never kill the game.
    """
    try:
        with wave.open(path) as w:
            ch, width, rate = w.getnchannels(), w.getsampwidth(), w.getframerate()
            comp = w.getcomptype()
        desc = '{} ch, {}-bit, {} Hz'.format(ch, width * 8, rate)
        if comp != 'NONE':
            return False, desc + ' compressed ({}) - needs plain PCM'.format(comp)
        if width not in (1, 2):
            return False, desc + ' - winsound needs 8 or 16-bit, not {}'.format(width * 8)
        return True, desc
    except wave.Error as e:
        return False, 'not a playable PCM wav: {}'.format(e)
    except Exception as e:
        return False, 'unreadable: {}: {}'.format(type(e).__name__, e)


class SoundManager:
    """The game only calls play(), toggle() and report()."""

    def __init__(self):
        self.enabled = SOUND_ON
        self.backend = 'silent'
        self._files = {}
        self._cache = {}
        self._cli = None
        self._winsound = None
        self._missing_mp3_support = False
        self._bad_wavs = {}                     # event -> why the file is unplayable
        self.last_error = None                  # first play() failure, for diagnose()
        self._find_files()
        self._pick_backend()

    def _find_files(self):
        """First hit wins, cheapest and most explicit name first.

        Every folder is searched for .wav BEFORE any .mp3, because .wav plays on the
        standard library and .mp3 needs the optional pygame backend. A .wav dropped
        into sound_effect/ next to the mp3 pack is therefore picked up and used - you
        do not have to move converted files into assets/sounds/ if you would rather
        convert them where they already are.
        """
        for event, candidates in SOUND_EVENTS.items():
            stems = [event] + [os.path.splitext(n)[0] for n in candidates]
            for path in self._search_order(event, stems, candidates):
                if os.path.isfile(path):
                    self._files[event] = path
                    break

    @staticmethod
    def _search_order(event, stems, candidates):
        """Every path to try for one event, in priority order."""
        yield os.path.join(SOUND_PATH, event + '.wav')       # 1. assets/sounds/eat.wav
        for folder in EXTRA_PATHS:                           # 2. sound_effect/eat.wav
            for stem in stems:                               #    then eat_fruit.wav
                yield os.path.join(folder, stem + '.wav')
        for name in candidates:                              # 3. the .mp3 pack (pygame)
            for folder in EXTRA_PATHS:
                yield os.path.join(folder, name)

    def _pick_backend(self):
        if not self._files:
            return
        needs_mp3 = any(p.lower().endswith('.mp3') for p in self._files.values())

        try:                                    # 1. pygame - optional, reads .mp3
            import pygame
            pygame.mixer.init()
            for event, path in self._files.items():
                try:
                    snd = pygame.mixer.Sound(path)
                    snd.set_volume(SOUND_VOLUME)
                    self._cache[event] = snd
                except Exception:
                    pass
            if self._cache:
                self.backend = 'pygame'
                return
        except Exception:
            self._cache.clear()

        # No pygame: drop .mp3 so we never hand one to a .wav-only backend.
        wavs = {e: p for e, p in self._files.items() if p.lower().endswith('.wav')}
        if not wavs:
            self._missing_mp3_support = needs_mp3
            return
        self._files = wavs

        # Drop .wav files the backends cannot play, and remember why. Without this a
        # float32 or ADPCM wav counted as "found", winsound raised, play() swallowed
        # it, and the status line claimed sound was working while nothing came out.
        good = {}
        for event, path in self._files.items():
            ok, desc = inspect_wav(path)
            if ok:
                good[event] = path
            else:
                self._bad_wavs[event] = (path, desc)
        self._files = good
        if not self._files:
            return

        try:                                    # 2. winsound - Windows stdlib
            import winsound
            self._winsound = winsound
            self.backend = 'winsound'
            return
        except Exception:
            pass

        for exe in ('afplay', 'paplay', 'aplay', 'ffplay'):   # 3. CLI players
            if shutil.which(exe):
                self._cli = exe
                self.backend = 'cli'
                return

    def play(self, event):
        """Never blocks, never raises. An audio glitch must not kill the game."""
        if not self.enabled or self.backend == 'silent':
            return
        path = self._files.get(event)
        if not path:
            return
        try:
            if self.backend == 'pygame':
                snd = self._cache.get(event)
                if snd is not None:
                    snd.play()
            elif self.backend == 'winsound':
                self._winsound.PlaySound(
                    path, self._winsound.SND_FILENAME | self._winsound.SND_ASYNC)
            elif self.backend == 'cli':
                args = [self._cli, path]
                if self._cli == 'ffplay':
                    args = [self._cli, '-nodisp', '-autoexit', '-loglevel', 'quiet', path]
                subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            if self.last_error is None:
                self.last_error = '{} on {}: {}: {}'.format(
                    self.backend, os.path.basename(path), type(e).__name__, e)
            if SOUND_DEBUG:
                print('SOUND ERROR:', self.last_error)

    def toggle(self):
        """Mute / unmute. Bound to X in both game modes."""
        self.enabled = not self.enabled
        return self.enabled

    def report(self):
        """One startup line, so silence is never a mystery."""
        if self.backend == 'silent':
            if self._missing_mp3_support:
                return ('SOUND: off - only .mp3 files were found, and .mp3 needs pygame. '
                        'Convert sound_effect/*.mp3 to .wav into assets/sounds/ ({}) - '
                        'then it plays on the standard library alone.'.format(_WAV_NAMES))
            if self._bad_wavs:
                return ('SOUND: off - {} file(s) found but not playable. Run '
                        'sfx.diagnose() or set SOUND_DEBUG=True in config.py for '
                        'details. Most likely they are not plain 16-bit PCM wav.'
                        .format(len(self._bad_wavs)))
            return ('SOUND: off - no audio files found. Put 16-bit PCM .wav files named '
                    '{} into assets/sounds/ (or into sound_effect/ next to the mp3s) '
                    '- no install needed.'.format(_WAV_NAMES))
        line = 'SOUND: {} events via {}'.format(len(self._files), self.backend)
        if self._bad_wavs:
            line += '  ({} file(s) skipped as unplayable - see sfx.diagnose())'.format(
                len(self._bad_wavs))
        return line

    def diagnose(self):
        """Multi-line report: every event, its file, its format, and the verdict.

        Print this when sound is missing. It answers the only question that matters:
        was the file found, and if so why is it not coming out of the speakers.
        """
        out = ['--- SOUND DIAGNOSIS ---',
               'backend        : {}'.format(self.backend),
               'muted          : {}'.format(not self.enabled),
               'wav folder     : {}'.format(SOUND_PATH),
               '  exists       : {}'.format(os.path.isdir(SOUND_PATH)),
               'extra folders  :']
        for f in EXTRA_PATHS:
            out.append('  {}  exists={}'.format(f, os.path.isdir(f)))
        out.append('')
        out.append('{:<8} {:<10} {}'.format('event', 'status', 'file / reason'))
        for event in SOUND_EVENTS:
            if event in self._files:
                ok, desc = inspect_wav(self._files[event])
                if self._files[event].lower().endswith('.mp3'):
                    desc = 'mp3 (pygame backend)'
                out.append('{:<8} {:<10} {}  [{}]'.format(
                    event, 'ready', os.path.basename(self._files[event]), desc))
            elif event in self._bad_wavs:
                path, why = self._bad_wavs[event]
                out.append('{:<8} {:<10} {}  <-- {}'.format(
                    event, 'UNUSABLE', os.path.basename(path), why))
            else:
                out.append('{:<8} {:<10} -'.format(event, 'missing'))
        if self._missing_mp3_support:
            out.append('')
            out.append('Only .mp3 was found. Without pygame nothing can play it.')
            out.append('Convert to 16-bit PCM wav instead:')
            out.append('  ffmpeg -i in.mp3 -c:a pcm_s16le -ac 1 -ar 22050 out.wav')
        if self._bad_wavs:
            out.append('')
            out.append('To fix an UNUSABLE file, re-encode it as plain 16-bit PCM:')
            out.append('  ffmpeg -i broken.wav -c:a pcm_s16le -ac 1 -ar 22050 fixed.wav')
            out.append('In Audacity: File > Export > WAV, choose')
            out.append('  "WAV (Microsoft) signed 16-bit PCM" - NOT 32-bit float.')
        if self.last_error:
            out.append('')
            out.append('first playback error: {}'.format(self.last_error))
        return '\n'.join(out)


sfx = SoundManager()                            # One shared instance for the whole game

# =============================================================================
# SCREENS: MAIN MENU, CHARACTER SELECT, RESULT SCREENS
# =============================================================================
# two 2P result screens (end of round, end of match).
#
# The menu and Character Select are Section 2 (entities) + Section 4 (input) with no
# game loop - they draw once and wait for a click or a key. The result screens are
# plain drawing functions that game_2p_scene() calls over its own arena.
#
# Clicks are hit-tested against rectangles through wn.onscreenclick rather than bound
# to turtles, for two reasons that are turtle limitations, not preference:
#   * a shape turtle is raised above pen drawings and text every frame, so a button
#     drawn as a shape would bury its own label
#   * onclick() silently binds nothing on a compound shape with 2+ components

# ===========================================
# SECTION 3: LAYOUT PARAMETERS (menus and result screens)
# ===========================================
BTN_W, BTN_H = 300, 80                          # Main menu mode buttons (pen-drawn:
                                                # "1 PLAYER" / "2 PLAYER BATTLE" is
                                                # not text any of the art carries)
# The two sizes import_assets.py writes the button art at. turtle cannot scale an
# image shape, so these numbers must match that file exactly or the hit box and the
# picture stop lining up.
BIG_BTN = (150, 86)                             # btn_start, btn_playgame
SMALL_BTN = (110, 63)                           # btn_menu, btn_setting, btn_exit
BTN_1P_Y, BTN_2P_Y = 60, -60

# Character Select, top to bottom inside a panel. Spaced so nothing overlaps:
#   header 180..208 | arrows 143..173 | card 9..127 | dots -4 | POWER label -24
#   power boxes -84..-40 | power name -104 | blurb -122 | summary -174
PANEL_W, PANEL_H = 300, 396
PANEL_CY = 10
HEADER_H = 28
CARD_W, CARD_H = 190, 118
CARD_CY = 68
ARROW_Y = 158
ARROW_DX = 128
ARROW_W, ARROW_H = 26, 30
ARROW_HIT = 46
DOTS_Y = -4
POWER_BOX = 44
POWER_GAP = 8
POWER_Y = -62

# Colours all come from the THEME block in SECTION 3, so the theme lives in one place.

# One scaled head shape per character, tinted with that character's own palette. A
# .gif sprite cannot be used for this: turtle cannot scale an image shape, so the
# 20x20 head would stay 20x20. Compound shapes do scale.
HEAD_SHAPE = {}
for _ch in CHARACTERS:
    _name = 'char_head_' + _ch['key']
    wn.register_shape(_name, make_head_shape(_ch['palette'][0], _ch['palette'][1],
                                             _ch['palette'][2]))
    HEAD_SHAPE[_ch['key']] = _name

# Hand-drawn card art, one optional file per character: assets/<key>_portrait.gif,
# 80x80, written by import_assets.py. A character with a portrait shows it instead of
# the drawn head, and the drawn head is what every other character keeps - so the two
# can be mixed and no character ever ends up with an empty card.
PORTRAIT = {c['key']: load_shape(c['key'] + '_portrait') for c in CHARACTERS}
PORTRAIT_CY = 82                                # Centre of an 80px portrait inside the
                                                # card (9..127), clear of the name line


# ===========================================
# MAIN MENU
# ===========================================
def menu_scene(epoch):
    wn.title('Snake Game - Main Menu')
    wn.bgcolor(BG_MENU)

    def enter_1p():
        go_to_scene(character_select_scene, '1P')

    def enter_2p():
        go_to_scene(character_select_scene, '2P')

    # SECTION 2: entities. Pen-drawn so the labels can sit on top.
    filled_rect(0, BTN_1P_Y, BTN_W, BTN_H, BUTTON_FILL, SLOT_COLOR['P1'])
    filled_rect(0, BTN_2P_Y, BTN_W, BTN_H, BUTTON_FILL, SLOT_COLOR['P2'])

    draw_label(0, 200, 'SNAKE GAME', 30, TEXT_BRIGHT)
    draw_label(0, 160, 'Choose a mode', 13, TEXT_MUTED)
    draw_label(0, BTN_1P_Y + 6, '1 PLAYER', 18, SLOT_COLOR['P1'])
    draw_label(0, BTN_1P_Y - 20, 'Classic snake + pick one power', 9, TEXT_MUTED)
    draw_label(0, BTN_2P_Y + 6, '2 PLAYER BATTLE', 18, SLOT_COLOR['P2'])
    draw_label(0, BTN_2P_Y - 20, 'P1: WASD   vs   P2: Arrow Keys', 9, TEXT_MUTED)
    draw_label(0, -180, 'Click a button, or press 1 / 2', 10, TEXT_FAINT)

    # SECTION 4: input. One handler hit-tests both buttons, so the whole 300x80 is live.
    def on_click(x, y):
        if inside_rect(x, y, 0, BTN_1P_Y, BTN_W, BTN_H):
            enter_1p()
        elif inside_rect(x, y, 0, BTN_2P_Y, BTN_W, BTN_H):
            enter_2p()

    wn.onscreenclick(on_click)
    wn.listen()
    wn.onkeypress(enter_1p, '1')
    wn.onkeypress(enter_2p, '2')
    wn.update()


# ===========================================
# CHARACTER SELECT
# ===========================================
def character_select_scene(epoch, mode):

    wn.title('Character Select')
    wn.bgcolor(BG_MENU)

    slots = ['P1'] if mode == '1P' else ['P1', 'P2']
    panel_cx = {'P1': 0} if mode == '1P' else {'P1': -158, 'P2': 158}

    # Pre-select something legal so Enter always works, and so the two players never
    # start out holding the same character.
    chosen = {}
    for i, slot in enumerate(slots):
        chosen[slot] = {
            'char': CHAR_DEFAULTS[i] if i < len(CHAR_DEFAULTS) else CHARACTERS[i]['key'],
            'power': POWER_DEFAULTS[i] if i < len(POWER_DEFAULTS) else POWERS[0]['key'],
        }

    def power_pos(slot, index):
        n = len(POWERS)
        return panel_cx[slot] + (index - (n - 1) / 2) * (POWER_BOX + POWER_GAP), POWER_Y

    def arrow_pos(slot, direction):
        return panel_cx[slot] + direction * ARROW_DX, ARROW_Y

    def taken_by_other(slot, char_key):
        return any(s != slot and chosen[s]['char'] == char_key for s in slots)

    # ===========================================
    # SECTION 2: GAME ENTITIES INITIALIZATION
    # ===========================================
    art_pen = new_pen()                         # cleared and redrawn on every pick
    text_pen = new_pen()
    chrome = new_pen()                          # drawn once
    portrait = {}

    def triangle(pen, cx, cy, w, h, direction, color):
        """Flip arrow: direction -1 points left, +1 points right."""
        pen.color(color, color)
        pen.penup()
        pen.goto(cx + direction * w / 2, cy)
        pen.pendown()
        pen.begin_fill()
        pen.goto(cx - direction * w / 2, cy + h / 2)
        pen.goto(cx - direction * w / 2, cy - h / 2)
        pen.goto(cx + direction * w / 2, cy)
        pen.end_fill()
        pen.penup()

    for slot in slots:
        cx = panel_cx[slot]
        rounded_card(cx, PANEL_CY, PANEL_W, PANEL_H, 16, PANEL_BG, SLOT_COLOR[slot])
        header_strip(cx, PANEL_CY + PANEL_H / 2 - HEADER_H, PANEL_W, HEADER_H,
                     SLOT_COLOR[slot], slot, BG_MENU)
        filled_rect(cx, CARD_CY, CARD_W, CARD_H, CARD_BG, SLOT_COLOR[slot], 3)
        triangle(chrome, *arrow_pos(slot, -1), ARROW_W, ARROW_H, -1, ARROW_COLOR)
        triangle(chrome, *arrow_pos(slot, 1), ARROW_W, ARROW_H, 1, ARROW_COLOR)
        draw_label(cx, POWER_Y + POWER_BOX / 2 + 16, 'POWER', 9, TEXT_MUTED)

    for slot in slots:
        # One turtle per card that swaps between a .gif portrait and the drawn head.
        # shapesize is set once for the drawn shape and simply ignored while an image
        # shape is on, which is what lets a single turtle serve both.
        portrait[slot] = shape_turtle(HEAD_SHAPE[CHARACTERS[0]['key']],
                                      panel_cx[slot] + 22, CARD_CY + 22, size=3.0)
        for i, pw in enumerate(POWERS):
            shape_turtle(icon_shape(pw['icon']), *power_pos(slot, i), size=1.1)

    title = 'CHARACTER SELECT - 1 PLAYER' if mode == '1P' else 'CHARACTER SELECT - 2 PLAYERS'
    draw_label(0, 272, title, 18, TEXT_BRIGHT)
    # One line, not two: the panels now reach y=-188 and the START button starts at
    # y=-213, so there is only room for a single row of hint text between them.
    if mode == '1P':
        draw_label(0, -206, 'Click the arrows, or  A / D = character   W / S = power',
                   9, TEXT_FAINT)
    else:
        draw_label(0, -206, 'P1  A / D  +  W / S        P2  Left / Right  +  Up / Down',
                   9, TEXT_FAINT)

    def redraw():
        """Repaint only what a pick changes: portrait, name, dots, power highlight."""
        art_pen.clear()
        text_pen.clear()
        for slot in slots:
            cx = panel_cx[slot]
            ch = character(chosen[slot]['char'])
            pw = power(chosen[slot]['power'])

            art = PORTRAIT.get(ch['key'])
            if art:                             # Hand-drawn card art fills the card
                portrait[slot].goto(cx, PORTRAIT_CY)
                portrait[slot].shape(art)
            else:                               # Drawn head plus a tapering tail
                portrait[slot].goto(cx + 22, CARD_CY + 22)
                portrait[slot].shape(HEAD_SHAPE[ch['key']])
                for i, (dx, dy) in enumerate(((-46, -14), (-72, -30), (-92, -50))):
                    fill_box(art_pen, cx + 22 + dx, CARD_CY + 22 + dy,
                             20 - i * 2, 20 - i * 2, ch['main'])
            write_at(text_pen, cx, CARD_CY - CARD_H / 2 + 12, ch['name'], 15, ch['main'])

            order = [c['key'] for c in CHARACTERS]
            here = order.index(ch['key'])
            for i in range(len(order)):
                dx = (i - (len(order) - 1) / 2) * 16
                fill_box(art_pen, cx + dx, DOTS_Y, 7, 7,
                         ch['main'] if i == here else CARD_EDGE)

            for i, opt in enumerate(POWERS):
                px, py = power_pos(slot, i)
                on = opt['key'] == pw['key']
                stroke_box(art_pen, px, py, POWER_BOX, POWER_BOX,
                           HIGHLIGHT if on else CARD_EDGE, 4 if on else 2)

            write_at(text_pen, cx, POWER_Y - POWER_BOX / 2 - 20, pw['name'], 12, HIGHLIGHT)
            write_at(text_pen, cx, POWER_Y - POWER_BOX / 2 - 38, pw['blurb'], 8, TEXT_MUTED)
            write_at(text_pen, cx, PANEL_CY - PANEL_H / 2 + 14,
                     '{}  /  {}'.format(ch['name'], pw['name']), 11, ch['main'])
        wn.update()

    # ===========================================
    # SECTION 4: INPUT HANDLING
    # ===========================================
    def step_char(slot, delta):
        if slot not in chosen:
            return
        order = [c['key'] for c in CHARACTERS]
        i = order.index(chosen[slot]['char'])
        for _ in range(len(order)):             # Skip whatever the other player holds
            i = (i + delta) % len(order)
            if not taken_by_other(slot, order[i]):
                chosen[slot]['char'] = order[i]
                sfx.play('select')
                redraw()
                return

    def step_power(slot, delta):
        if slot not in chosen:
            return
        order = [p['key'] for p in POWERS]
        i = order.index(chosen[slot]['power'])
        chosen[slot]['power'] = order[(i + delta) % len(order)]
        sfx.play('select')
        redraw()

    def pick_power(slot, power_key):
        if slot in chosen:
            chosen[slot]['power'] = power_key
            sfx.play('select')
            redraw()

    start_btn = ImageButton('btn_start', 0, -256, *BIG_BTN,
                            label='START', color=HIGHLIGHT)
    back_btn = ImageButton('btn_menu', -300, -256, *SMALL_BTN,
                           label='MENU', color=TEXT_MUTED)

    def on_click(x, y):
        if start_btn.hit(x, y):
            try_start()
            return
        if back_btn.hit(x, y):
            back_to_menu()
            return
        for slot in slots:
            for direction in (-1, 1):
                if inside_rect(x, y, *arrow_pos(slot, direction), ARROW_HIT, ARROW_HIT):
                    step_char(slot, direction)
                    return
            for i, pw in enumerate(POWERS):
                if inside_rect(x, y, *power_pos(slot, i),
                               POWER_BOX + POWER_GAP, POWER_BOX + 10):
                    pick_power(slot, pw['key'])
                    return
            if inside_rect(x, y, panel_cx[slot], CARD_CY, CARD_W, CARD_H):
                step_char(slot, 1)              # Clicking the card steps forward
                return

    def try_start():
        sfx.play('start')
        if mode == '1P':
            go_to_scene(game_1p_scene, chosen['P1']['char'], chosen['P1']['power'])
        else:
            go_to_scene(game_2p_scene,
                        chosen['P1']['char'], chosen['P1']['power'],
                        chosen['P2']['char'], chosen['P2']['power'])

    def back_to_menu():
        go_to_scene(menu_scene)

    wn.onscreenclick(on_click)
    wn.listen()
    wn.onkeypress(lambda: step_char('P1', -1), 'a')
    wn.onkeypress(lambda: step_char('P1', 1), 'd')
    wn.onkeypress(lambda: step_power('P1', -1), 'w')
    wn.onkeypress(lambda: step_power('P1', 1), 's')
    arrow_slot = 'P2' if mode != '1P' else 'P1'
    wn.onkeypress(lambda: step_char(arrow_slot, -1), 'Left')
    wn.onkeypress(lambda: step_char(arrow_slot, 1), 'Right')
    wn.onkeypress(lambda: step_power(arrow_slot, -1), 'Up')
    wn.onkeypress(lambda: step_power(arrow_slot, 1), 'Down')
    wn.onkeypress(try_start, 'Return')
    wn.onkeypress(back_to_menu, 'Escape')

    redraw()


# ===========================================
# RESULT SCREENS (2P) - drawn over the arena, not scenes of their own
# ===========================================
# `rounds` is the match ledger: one dict per round played, holding each player's
# score and the HP they finished the round with. MVP weights the two together:
#
#     MVP = score x HP left  +  SURVIVE_BONUS x HP left,  added up over every round
#
# so surviving a round counts as much as scoring in it, and a round you were knocked
# out of is worth nothing no matter how many points you banked (everything is x 0).
# The bonus is what stops a round won on hearts alone from being worth nothing.
# Round wins still decide the match; MVP only breaks a tie on rounds.


def scoreline(round_wins):
    return 'P1  {} - {}  P2'.format(round_wins['P1'], round_wins['P2'])


def _mvp(r, slot):
    """One round's MVP for one player."""
    hp = r['hp' + slot]
    return (r[slot] + SURVIVE_BONUS) * hp


def mvp_total(rounds, slot):
    return sum(_mvp(r, slot) for r in rounds)


def match_champion(round_wins, rounds):
    """Rounds decide it, MVP breaks a tie, still level is a drawn match.

    Returns 'P1' / 'P2', or None for a drawn match.
    """
    if round_wins['P1'] != round_wins['P2']:
        return 'P1' if round_wins['P1'] > round_wins['P2'] else 'P2'
    m1, m2 = mvp_total(rounds, 'P1'), mvp_total(rounds, 'P2')
    if m1 == m2:
        return None
    return 'P1' if m1 > m2 else 'P2'


def _cell(r, slot):
    """One player's round in the ledger, showing the whole sum."""
    hp = r['hp' + slot]
    return '{} x {} + {} = {}'.format(r[slot], hp, SURVIVE_BONUS * hp, _mvp(r, slot))


def draw_result(pen, p1, p2, round_wins, rounds, final, winner):
    """The only entry point: a round screen between rounds, the ledger at the end."""
    if final:
        _draw_match(pen, p1, p2, round_wins, rounds)
    else:
        _draw_round(pen, p1, p2, round_wins, rounds, winner)


def _draw_round(pen, p1, p2, round_wins, rounds, winner):
    """Between rounds: who took it, the tally, and what is left to play for."""
    last = rounds[-1]
    write_at(pen, 0, 150, 'ROUND {} OVER'.format(len(rounds)), 24, TEXT_BRIGHT)
    if winner == 'draw':
        write_at(pen, 0, 108, 'DRAW - NOBODY TAKES THE ROUND', 17, TEXT_BRIGHT)
    else:
        write_at(pen, 0, 108, '{} {} WINS THE ROUND'.format(
            winner.slot, winner.char_name), 18, winner.color_main)
    write_at(pen, 0, 50, scoreline(round_wins), 30, HIGHLIGHT)

    write_at(pen, 0, 0, 'score x hp + {} per hp left = MVP'.format(SURVIVE_BONUS),
             12, TEXT_MUTED)
    write_at(pen, -14, -28, 'P1  ' + _cell(last, 'P1'), 15, p1.color_main, 'right')
    write_at(pen, 14, -28, _cell(last, 'P2') + '  P2', 15, p2.color_main, 'left')
    if len(rounds) > 1:                         # Round 1 would only repeat the line above
        write_at(pen, 0, -62, 'MVP so far    P1 {}    |    P2 {}'.format(
            mvp_total(rounds, 'P1'), mvp_total(rounds, 'P2')), 13, TEXT_MUTED)
    write_at(pen, 0, -100, 'first to {} rounds takes the match'.format(ROUNDS_TO_WIN),
             12, TEXT_DIM)
    write_at(pen, 0, -130, 'Press R for round {}     |     M for Menu'.format(
        len(rounds) + 1), 12, TEXT_DIM)


def _draw_match(pen, p1, p2, round_wins, rounds):
    """End of the match: the champion, the tally, and the full MVP ledger.

    This is why the ledger keeps a record per round instead of a running sum - a
    summary that cannot show how the match got there is not a summary.
    """
    champ = match_champion(round_wins, rounds)
    who = {'P1': p1, 'P2': p2}.get(champ)
    mvp = {s: mvp_total(rounds, s) for s in ('P1', 'P2')}
    pts = {s: sum(r[s] for r in rounds) for s in ('P1', 'P2')}

    write_at(pen, 0, 172, 'MATCH RESULT', 26, TEXT_BRIGHT)
    if who is None:
        write_at(pen, 0, 134, 'A DRAWN MATCH - NOBODY TAKES IT', 18, TEXT_BRIGHT)
    else:
        write_at(pen, 0, 134, '{} {} WINS THE MATCH'.format(champ, who.char_name),
                 20, who.color_main)
    write_at(pen, 0, 86, scoreline(round_wins), 30, HIGHLIGHT)

    col_r, col_1, col_2, col_w = -350, -60, 215, 370        # Ledger column edges
    y = 40
    # Short headers on purpose: spelled out, the P1 column ran back past x=-380 and
    # printed on top of ROUND. The formula is written under the table anyway.
    write_at(pen, col_r, y, 'ROUND', 13, TEXT_MUTED, 'left')
    write_at(pen, col_1, y, 'P1  MVP', 13, p1.color_main, 'right')
    write_at(pen, col_2, y, 'P2  MVP', 13, p2.color_main, 'right')
    write_at(pen, col_w, y, 'WON BY', 13, TEXT_MUTED, 'right')
    for i, r in enumerate(rounds, 1):
        y -= 27
        took = {'P1': p1, 'P2': p2}.get(r['win'])
        write_at(pen, col_r, y, 'R{}'.format(i), 14, TEXT_BRIGHT, 'left')
        write_at(pen, col_1, y, _cell(r, 'P1'), 14, p1.color_main, 'right')
        write_at(pen, col_2, y, _cell(r, 'P2'), 14, p2.color_main, 'right')
        write_at(pen, col_w, y, 'DRAW' if took is None else took.char_name, 13,
                 TEXT_MUTED if took is None else took.color_main, 'right')
    y -= 20
    write_at(pen, col_r, y, '-' * 130, 13, TEXT_FAINT, 'left')   # Spans to col_w
    y -= 26
    lead = 'TIED' if mvp['P1'] == mvp['P2'] else ('P1' if mvp['P1'] > mvp['P2'] else 'P2')
    write_at(pen, col_r, y, 'MVP TOTAL', 15, HIGHLIGHT, 'left')
    write_at(pen, col_1, y, str(mvp['P1']), 15, p1.color_main, 'right')
    write_at(pen, col_2, y, str(mvp['P2']), 15, p2.color_main, 'right')
    write_at(pen, col_w, y, 'MVP: ' + lead, 13, HIGHLIGHT, 'right')

    y -= 34
    write_at(pen, 0, y, 'raw points   P1 {}   |   P2 {}'.format(pts['P1'], pts['P2']),
             12, TEXT_MUTED)
    y -= 24
    if round_wins['P1'] == round_wins['P2']:    # The only time MVP changes the outcome
        write_at(pen, 0, y, 'rounds level {} - {}  ->  MVP decides the match'.format(
            round_wins['P1'], round_wins['P2']), 12, HIGHLIGHT)
    else:
        write_at(pen, 0, y, 'MVP = (score + {}) x hp left, summed - it only breaks a '
                 'tie on rounds'.format(SURVIVE_BONUS), 11, TEXT_FAINT)
    write_at(pen, 0, y - 30, 'Press R for a NEW MATCH     |     M for Menu', 12, TEXT_DIM)

# =============================================================================
# 1 PLAYER MODE  (Sections 2, 3, 4, 5)
# =============================================================================
# Classic snake: no HP, no combat, no obstacles. The outer wall is fatal, and so is
# your own tail unless CLOAK, PHASE or SHIELD is running.
#
# Follows the baseline kit layout:
#     Section 2  Game Entities Initialization
#     Section 3  Parameters & Physics
#     Section 4  Input Handling
#     Section 5  Main Game Loop
# Section 1 (Screen Setup) is at the top of the file - turtle allows one Screen per process.

def game_1p_scene(epoch, char_key, power_key):

    # ===========================================
    # SECTION 3: PARAMETERS & PHYSICS
    # ===========================================
    ARENA_L, ARENA_R, ARENA_B, ARENA_T = ARENA_1P
    BORDER_PAD = 5
    # Keep the 20x20 head sprite from sinking into the border (see game_2p_scene)
    WALL_L, WALL_R = ARENA_L + WALL_MARGIN, ARENA_R - WALL_MARGIN
    WALL_B, WALL_T = ARENA_B + WALL_MARGIN, ARENA_T - WALL_MARGIN
    FRUIT_REACH = 18
    SPAWN_CLEAR = 60
    SELF_HIT_RADIUS = 10
    NO_HP = 1                                       # 1P has no hearts; Snake still needs a value

    # The skill bar must sit ABOVE the arena. It used to be at y 226-238 while the
    # arena reached y=260, so the snake drove straight through it and the bar repainted
    # over the snake every frame. ARENA_1P now tops out at 235, matching how the
    # 2P HUD lives above ARENA_2P.
    BAR_LEFT, BAR_BOTTOM = -70, 248
    BAR_W, BAR_H = 140, 12
    BODY_CLEAR = 24                                 # Keep fruit off the snake's own body
    HINT = 'Arrows = Move   SPACE = {}   R = Retry   X = Sound   M = Menu'

    ch = character(char_key)
    wn.title('Snake - 1 Player ({} / {})'.format(ch['name'], power_key))
    wn.bgcolor(BG_COLOR)

    # ===========================================
    # SECTION 2: GAME ENTITIES INITIALIZATION
    # ===========================================
    border = new_pen(WALL_COLOR)
    border.pensize(6)
    border.goto(ARENA_L - BORDER_PAD, ARENA_T + BORDER_PAD)
    border.pendown()
    for _ in range(2):
        border.forward(ARENA_R - ARENA_L + BORDER_PAD * 2)
        border.right(90)
        border.forward(ARENA_T - ARENA_B + BORDER_PAD * 2)
        border.right(90)
    border.penup()

    # The same Snake the battle mode uses, so sprites, body layout and powers behave
    # identically. 1P just starts stopped and ignores hp.
    me = Snake('P1', char_key, (0, 0), 'right', power_key, SPEED_1P, NO_HP)
    me.direction = 'stop'

    fruit = make_fruit()

    def random_free_spot():
        """Somewhere clear of the head AND the body.

        Checking only the head let fruit land on a segment further back, where
        collecting it means driving into your own tail - an unavoidable game over.
        """
        for _ in range(200):
            x = random.randint(ARENA_L + 30, ARENA_R - 30)
            y = random.randint(ARENA_B + 30, ARENA_T - 30)
            if me.head.distance(x, y) <= SPAWN_CLEAR:
                continue
            if any((pos[0] - x) ** 2 + (pos[1] - y) ** 2 < BODY_CLEAR ** 2
                   for pos in me.segments()):
                continue
            return x, y
        return 0, 0

    fruit.goto(random_free_spot())

    hud = new_pen(TEXT_BRIGHT)
    bar_pen = new_pen()
    result_pen = new_pen()
    alive = {'value': True}

    # ===========================================
    # SECTION 4: INPUT HANDLING
    # ===========================================
    def use_power():
        if me.use_power():
            sfx.play('power')
            draw_hud()
            wn.update()

    def retry():
        if alive['value']:                      # R only works after game over
            return
        go_to_scene(game_1p_scene, char_key, power_key)

    def to_menu():
        go_to_scene(menu_scene)

    wn.listen()
    for key, direction in (('Up', 'up'), ('Down', 'down'),
                           ('Left', 'left'), ('Right', 'right')):
        wn.onkeypress(lambda d=direction: me.turn(d), key)
    wn.onkeypress(use_power, 'space')
    wn.onkeypress(sfx.toggle, 'x')
    wn.onkeypress(retry, 'r')
    wn.onkeypress(to_menu, 'm')

    # ===========================================
    # SECTION 5A: HUD & GAME OVER
    # ===========================================
    def draw_hud():
        hud.clear()
        bar_pen.clear()
        hud.color(TEXT_BRIGHT)
        hud.goto(ARENA_L, 268)
        hud.write('SCORE: {}'.format(me.score), font=(FONT, 14, 'bold'))
        draw_skill_bar(bar_pen, BAR_LEFT, BAR_BOTTOM, BAR_W, BAR_H,
                       me.skill / SKILL_MAX, ch['main'])
        hud.color(HIGHLIGHT)
        hud.goto(0, 268)
        hud.write('  '.join(powers_hud_tags(me)), align='center', font=(FONT, 12, 'bold'))
        hud.color(TEXT_MUTED)
        hud.goto(ARENA_R, 268)
        hud.write('{} [{}]'.format(ch['name'], me.power['name']),
                  align='right', font=(FONT, 12, 'bold'))
        hud.color(TEXT_FAINT)
        hud.goto(0, -272)
        hud.write(HINT.format(me.power['name']), align='center', font=(FONT, 10, 'normal'))

    def game_over():
        alive['value'] = False
        me.hide()                               # Or the snake sits under the text
        fruit.hideturtle()
        result_pen.clear()
        result_pen.color(TEXT_BRIGHT)
        result_pen.goto(0, 30)
        result_pen.write('GAME OVER', align='center', font=(FONT, 26, 'bold'))
        result_pen.goto(0, -10)
        result_pen.write('Score: {}'.format(me.score), align='center', font=(FONT, 18, 'bold'))
        result_pen.color(TEXT_DIM)
        result_pen.goto(0, -50)
        result_pen.write('R = Retry     M = Menu', align='center', font=(FONT, 12, 'normal'))

        # The keys above still work; these are the same two actions as buttons.
        again = ImageButton('btn_playgame', -90, -170, 150, 86,
                            label='RETRY', color=HIGHLIGHT)
        back = ImageButton('btn_menu', 90, -170, 110, 63, label='MENU', color=TEXT_DIM)
        wn.onscreenclick(click_router((again, retry), (back, to_menu)))

        sfx.play('lose')
        wn.update()

    def hit_own_tail():
        """PHASE and SHIELD let you run over your own tail; CLOAK does not.

        CLOAK used to be exempt here but not in battle.py, which made STEALTH a
        strictly better PHASE in 1P - same cost, longer duration, plus it hides the
        body. `cloak` is not a collision effect kind (see config.py Section 3G), and
        its own blurb says "still solid", so only the declared kinds count.
        """
        if powers_flag(me, 'noclip') or powers_flag(me, 'invincible'):
            return False
        return any(me.head.distance(pos) < SELF_HIT_RADIUS for pos in me.segments()[2:])

    # ===========================================
    # SECTION 5: MAIN GAME LOOP
    # ===========================================
    sfx.play('start')

    def game_loop():
        if STATE['epoch'] != epoch or not alive['value']:
            return                              # A newer scene took over, or you died

        me.tick_timers()                        # 1. advance timers and speed
        nxt = me.next_position()
        if nxt is not None:
            x, y = nxt
            if x > WALL_R or x < WALL_L or y > WALL_T or y < WALL_B:
                game_over()                     # 2. the wall is fatal here
                return
            me.commit(x, y)

            if hit_own_tail():                  # 3. own tail is fatal too
                game_over()
                return

            if me.head.distance(fruit) < FRUIT_REACH:   # 4. pickup
                gain = int(FRUIT_SCORE * powers_effect(me, 'score_mult', 1.0))
                me.gain_fruit(gain, GROW_PER_FRUIT, SKILL_GAIN_1P)
                fruit.goto(random_free_spot())
                reroll_fruit(fruit)             # New spot, new fruit - looks only
                sfx.play('eat')

        me.render()                             # 5. draw
        draw_hud()
        wn.update()
        wn.ontimer(game_loop, FRAME_MS)

    game_loop()

# =============================================================================
# 2 PLAYER BATTLE MODE  (Sections 2, 3, 4, 5)
# =============================================================================
# Follows the baseline kit layout:
#     Section 2  Game Entities Initialization
#     Section 3  Parameters & Physics
#     Section 4  Input Handling
#     Section 5  Main Game Loop
# Section 1 (Screen Setup) is at the top of the file - turtle allows one Screen per process.

def game_2p_scene(epoch, p1_char, p1_power, p2_char, p2_power, wins=None, history=None):
    # ===========================================
    # SECTION 3: PARAMETERS & PHYSICS
    # ===========================================
    ARENA_L, ARENA_R, ARENA_B, ARENA_T = ARENA_2P
    BORDER_PAD = 5                                  # Border is drawn this far outside the arena
    # The head is a 20x20 sprite drawn centred, so allowing the CENTRE to reach the arena
    # edge let half the sprite sink into the wall. Pull the limits in by WALL_MARGIN.
    WALL_L, WALL_R = ARENA_L + WALL_MARGIN, ARENA_R - WALL_MARGIN
    WALL_B, WALL_T = ARENA_B + WALL_MARGIN, ARENA_T - WALL_MARGIN
    OBSTACLE_PAD = 6                                # Collision margin around a box
    FRUIT_REACH = 18                                # How close counts as eating
    SPAWN_CLEAR = 60                                # Keep fruit away from a head
    OBSTACLE_CLEAR = 20                             # Keep fruit out of a box
    BODY_CLEAR = 24                                 # Keep fruit off either snake's body

    HEART_Y = 250
    HEART_STEP = 22
    BAR_W, BAR_H = 132, 12
    BAR_Y = 224
    ICON_GAP = 22                                   # Power icon, just outside the skill bar
    ICON_SIZE = 0.9
    TAG_LIFT = 20                                   # STUN / power tag floats this far above
                                                    # the head - on the snake, where you are
                                                    # actually looking, not up in the HUD
    PANEL = {
        'P1': {'x': -356, 'dir': 1, 'align': 'left',  'bar_x': -358},
        'P2': {'x': 356,  'dir': -1, 'align': 'right', 'bar_x': 358 - BAR_W},
    }
    SPAWN = {'P1': ((-250, -35), 'right'), 'P2': ((250, -35), 'left')}
    HINT = 'P1: WASD Q=Power  |  P2: Arrows O=Power  |  X = Sound  M = Menu'

    """One round of a match.

    `wins` carries the round tally between rounds ({'P1': n, 'P2': n}) and `history`
    the per-round score ledger, so the final MATCH RESULT can add up a whole match
    even though each round starts the snakes back at 0.
    """

    wn.title('Snake Battle - Local Multiplayer (P1: WASD | P2: Arrow Keys)')
    wn.bgcolor(BG_COLOR)

    # ===========================================
    # SECTION 2: GAME ENTITIES INITIALIZATION
    # ===========================================
    border = new_pen(WALL_COLOR)
    border.pensize(6)
    border.goto(ARENA_L - BORDER_PAD, ARENA_T + BORDER_PAD)
    border.pendown()
    for _ in range(2):
        border.forward(ARENA_R - ARENA_L + BORDER_PAD * 2)
        border.right(90)
        border.forward(ARENA_T - ARENA_B + BORDER_PAD * 2)
        border.right(90)
    border.penup()

    obstacle_pen = new_pen()
    obstacle_pen.color(OBSTACLE_EDGE, OBSTACLE_FILL)
    obstacle_pen.pensize(3)
    obstacles = []

    def build_obstacles():
        obstacle_pen.clear()
        obstacles.clear()
        for cx, cy in OBSTACLE_SPOTS[:OBSTACLE_COUNT]:
            fill_box(obstacle_pen, cx, cy, OBSTACLE_SIZE, OBSTACLE_SIZE,
                     OBSTACLE_FILL, OBSTACLE_EDGE)
            half = OBSTACLE_SIZE / 2
            obstacles.append((cx - half, cy - half, cx + half, cy + half))

    def inside_obstacle(x, y, pad=0):
        for left, bottom, right, top in obstacles:
            if left - pad <= x <= right + pad and bottom - pad <= y <= top + pad:
                return True
        return False

    build_obstacles()

    p1 = Snake('P1', p1_char, *SPAWN['P1'], p1_power, SPEED_2P, MAX_HP)
    p2 = Snake('P2', p2_char, *SPAWN['P2'], p2_power, SPEED_2P, MAX_HP)
    players = [p1, p2]

    fruits = []

    def random_free_spot(skip=None):
        for _ in range(200):
            x = random.randint(ARENA_L + 30, ARENA_R - 30)
            y = random.randint(ARENA_B + 30, ARENA_T - 30)
            if inside_obstacle(x, y, pad=OBSTACLE_CLEAR):
                continue
            if any(pl.head.distance(x, y) < SPAWN_CLEAR for pl in players):
                continue
            # Heads are not enough: a fruit on a BODY segment costs the eater a heart
            # through resolve_self_collision. 1 Player has always checked this.
            if any((px - x) ** 2 + (py - y) ** 2 < BODY_CLEAR ** 2
                   for pl in players for px, py in pl.segments()):
                continue
            # Keep fruits apart, or two land together and one touch scores both.
            if any(f is not skip and f.distance(x, y) < FRUIT_MIN_GAP for f in fruits):
                continue
            return x, y
        return 0, 0

    for _ in range(FRUIT_COUNT_2P):
        f = make_fruit()
        f.goto(random_free_spot())
        fruits.append(f)

    hud = new_pen(TEXT_BRIGHT)
    bar_pen = new_pen()
    result_pen = new_pen()
    game_active = {'value': True}
    round_wins = dict(wins) if wins else {'P1': 0, 'P2': 0}
    rounds = list(history) if history else []   # One {'P1', 'P2', 'win'} per round played
    match_over = {'value': False}               # True once someone reaches ROUNDS_TO_WIN

    HEART_FULL = load_shape('heart_full')
    HEART_EMPTY = load_shape('heart_empty')
    USE_HEART_ICONS = HEART_FULL is not None and HEART_EMPTY is not None

    heart_icons = {}
    if USE_HEART_ICONS:
        for pl in players:
            geo = PANEL[pl.slot]
            pool = []
            for i in range(MAX_HP):
                icon = turtle.Turtle()
                icon.penup()
                icon.shape(HEART_FULL)
                icon.goto(geo['x'] + geo['dir'] * i * HEART_STEP, HEART_Y)
                pool.append(icon)
            heart_icons[pl.slot] = pool

    # The power each player CHOSE, pinned beside their bar. It never changes during a
    # round, so it is a plain shape turtle: no per-frame drawing, and it tells you what
    # your Q / O key will fire without reading any text.
    power_icons = []
    for pl in players:
        geo = PANEL[pl.slot]
        icon_x = geo['bar_x'] + (BAR_W + ICON_GAP if geo['dir'] > 0 else -ICON_GAP)
        power_icons.append(
            shape_turtle(pl.power['icon'], icon_x, BAR_Y + BAR_H / 2, size=ICON_SIZE))

    # ===========================================
    # SECTION 4: INPUT HANDLING
    # ===========================================
    def to_menu():
        go_to_scene(menu_scene)

    def do_restart():
        if game_active['value']:                # R only works on the result screen
            return
        # Carry the tally and the ledger into the next round, unless the match is
        # already decided - then R starts a fresh match at 0 - 0.
        done = match_over['value']
        go_to_scene(game_2p_scene, p1_char, p1_power, p2_char, p2_power,
                    None if done else round_wins, None if done else rounds)

    def fire(snake):
        def go():
            if snake.use_power():
                sfx.play('power')
        return go

    wn.listen()
    for key, direction in (('w', 'up'), ('s', 'down'), ('a', 'left'), ('d', 'right')):
        wn.onkeypress(lambda d=direction: p1.turn(d), key)
    for key, direction in (('Up', 'up'), ('Down', 'down'),
                           ('Left', 'left'), ('Right', 'right')):
        wn.onkeypress(lambda d=direction: p2.turn(d), key)
    # One power key per player, whatever power they picked. E and P are kept as
    # aliases for the old two-key layout.
    for key in ('q', 'e'):
        wn.onkeypress(fire(p1), key)
    for key in ('o', 'p'):
        wn.onkeypress(fire(p2), key)
    wn.onkeypress(sfx.toggle, 'x')
    wn.onkeypress(to_menu, 'm')
    wn.onkeypress(do_restart, 'r')

    # ===========================================
    # SECTION 5A: PHYSICS & COLLISION RULES
    # ===========================================
    def step(snake):
        """Move one snake. Walls and boxes stun; they never cost HP.

        Returns True only if the head actually moved, because a self hit can only
        NEWLY happen after a move - see game_loop.
        """
        nxt = snake.next_position()
        if nxt is None:                         # Stunned or stopped
            return False
        x, y = nxt
        bumped = False
        if x > WALL_R or x < WALL_L or y > WALL_T or y < WALL_B:
            bumped = True                       # The outer wall always stops you
        elif inside_obstacle(x, y, pad=OBSTACLE_PAD) and not powers_flag(snake, 'noclip'):
            bumped = True                       # PHASE slips through the boxes
        if bumped:
            snake.stun = STUN_FRAMES
            snake.direction = 'stop'
            sfx.play('bump')
            return False
        snake.commit(x, y)
        return True

    def punish(loser, hp=1):
        """One knockdown: HP only. Nothing here ever touches the score.

        Score moves in exactly ONE place in the whole game - a head-to-head clash,
        below. Everything else (a bite, your own body, and so the wall and boxes too)
        costs hearts alone, so a player can never be scored down for a collision they
        were not the aggressor in.

        Returns False when the hit was absorbed (immunity frames or SHIELD), which is
        also what stops a blocked clash from moving any score.
        """
        if loser.invuln > 0:
            return False
        if powers_flag(loser, 'invincible'):    # SHIELD
            return False
        loser.hp -= hp
        loser.invuln = INVULN_FRAMES
        loser.stun = STUN_FRAMES
        sfx.play('hit')
        return True

    def resolve_head_clash():
        """Head to head: the LOWER score WINS the clash and is PAID for it.

        The only score transfer in the game. The snake that is ahead loses a heart and
        hands over SCORE_TRANSFER of its score; the snake behind loses nothing and
        gains that score. Being in front is therefore dangerous, which is the point -
        it pushes the leader away from head-on fights and towards baiting instead.

        Called once per frame, not once per player, or the clash resolves twice.
        A level score costs both of them a heart, with no transfer either way.
        """
        if p1.hp <= 0 or p2.hp <= 0:
            return
        if p1.head.distance(p2.head) >= HIT_RADIUS:
            return
        # ONE clash per encounter. Without this the transfer flips who is ahead, so the
        # next frame - heads still touching, loser stunned in place - punished the snake
        # that had just WON the clash. Immunity frames on either side mean "still
        # recovering", and a clash needs two snakes that are both fit to fight.
        if p1.invuln > 0 or p2.invuln > 0:
            return
        if p1.score == p2.score:
            punish(p1)
            punish(p2)
            return
        loser, winner = (p1, p2) if p1.score > p2.score else (p2, p1)
        if punish(loser):                       # Ahead on score = you lose the clash
            share = int(loser.score * SCORE_TRANSFER)
            loser.score -= share
            winner.score += share
            # The loser is now stunned exactly where the heads met, so the winner's head
            # is touching its neck. Without this the very next resolve_bite() charged
            # the winner a heart for the clash it had just won - the opposite of the
            # rule that the lower score pays nothing.
            winner.bite_grace = STUN_FRAMES

    def resolve_bite(biter, victim):
        """Biting ANY part of the other snake costs the BITER a heart - and only that.

        Tail and body are treated the same on purpose. The old rule rewarded biting
        the tail, which fought against the point of the game: you want the enemy to
        take a bite out of you. No score changes hands here, whoever is ahead, so a
        bite is a pure HP punishment.
        """
        if biter.hp <= 0 or victim.hp <= 0:
            return
        if biter.bite_grace > 0:                # Just won a head clash - see there
            return
        for pos in victim.segments():
            if biter.head.distance(pos) < HIT_RADIUS:
                punish(biter)
                return

    def resolve_self_collision(snake):
        """Own body costs a stun and SELF_HIT_DAMAGE hp (set it to 0 for stun only).

        Two guards, both load-bearing:
          * the grace window, or this fires every frame while the head sits on its own
            body - that used to freeze the snake forever, and once self hits cost HP it
            drained every heart instead
          * the caller only asks when the head actually MOVED. A snake that bumped a
            wall while coiled has direction='stop' and never leaves its own body, so
            without that check it lost a heart every time the grace expired and died
            standing still.
        The direction is deliberately left alone so the snake coasts out of its own
        coil once the stun ends.
        """
        if snake.self_hit_grace > 0:
            return
        if powers_flag(snake, 'noclip'):        # PHASE
            return
        for pos in snake.segments()[2:]:        # Skip the 2 segments behind the head
            if snake.head.distance(pos) < HIT_RADIUS - 2:
                snake.stun = STUN_FRAMES
                snake.self_hit_grace = STUN_FRAMES + SELF_HIT_GRACE_EXTRA
                if SELF_HIT_DAMAGE:
                    punish(snake, SELF_HIT_DAMAGE)   # HP only, a fumble costs no score
                return

    def resolve_fruit(snake):
        for f in fruits:
            if snake.head.distance(f) < FRUIT_REACH:
                gain = int(FRUIT_SCORE * powers_effect(snake, 'score_mult', 1.0))
                snake.gain_fruit(gain, GROW_PER_FRUIT, SKILL_GAIN_2P)
                f.goto(random_free_spot(skip=f))
                reroll_fruit(f)                 # New spot, new fruit - looks only
                sfx.play('eat')
                return                          # One fruit per frame, per player

    def check_win():
        if p1.hp <= 0 and p2.hp <= 0:
            return 'draw'
        if p1.hp <= 0: return p2
        if p2.hp <= 0: return p1
        if p1.score >= TARGET_SCORE and p2.score >= TARGET_SCORE:
            return 'draw' if p1.score == p2.score else (p1 if p1.score > p2.score else p2)
        if p1.score >= TARGET_SCORE: return p1
        if p2.score >= TARGET_SCORE: return p2
        return None

    # ===========================================
    # SECTION 5B: HUD & END OF ROUND
    # ===========================================
    def draw_hud():
        hud.clear()
        bar_pen.clear()
        for pl in players:
            geo = PANEL[pl.slot]
            if USE_HEART_ICONS:
                for i, icon in enumerate(heart_icons[pl.slot]):
                    icon.shape(HEART_FULL if i < pl.hp else HEART_EMPTY)
                    icon.showturtle()
                score_x = geo['x'] + geo['dir'] * (MAX_HP * HEART_STEP + 4)
            else:
                write_at(hud, geo['x'], HEART_Y - 6, '<3 ' * max(0, pl.hp), 13,
                         pl.color_main, geo['align'])
                score_x = geo['x'] + geo['dir'] * (MAX_HP * 26)

            write_at(hud, score_x, HEART_Y - 7, '{} {} [{}] {}'.format(
                pl.slot, pl.char_name, pl.skill_tag, pl.score), 14,
                pl.color_main, geo['align'])

            draw_skill_bar(bar_pen, geo['bar_x'], BAR_Y, BAR_W, BAR_H,
                           pl.skill / SKILL_MAX, pl.color_main)

            # STUN and the active-power tag ride ABOVE THE SNAKE, not next to the bar.
            # Beside the bar they read as part of the skill meter, which is what made
            # STUN confusing; over the head they are unmistakably about the snake.
            tags = powers_hud_tags(pl)          # One label per running power
            if pl.stun > 0:
                tags.append('STUN')
            if tags:
                # Keep the label inside the arena: centred text runs off the side walls,
                # and near the ceiling it climbs into the skill-bar row, so flip it under
                # the head up there instead.
                tx = min(max(pl.head.xcor(), ARENA_L + 40), ARENA_R - 40)
                ty = pl.head.ycor()
                ty += TAG_LIFT if ty < ARENA_T - 40 else -TAG_LIFT - 8
                write_at(hud, tx, ty, ' '.join(tags), 10, TEXT_TAG)

        write_at(hud, 0, 249, scoreline(round_wins), 16, HIGHLIGHT)       # Round tally,  1 - 0
        write_at(hud, 0, 228, 'FIRST TO {}  -  BEST OF {}'.format(
            TARGET_SCORE, ROUNDS_TO_WIN * 2 - 1), 10, TEXT_DIM)
        write_at(hud, 0, -272, HINT, 10, TEXT_FAINT)

    def clear_field():
        """Take the arena off screen so a result can be drawn over it."""
        for pl in players:
            pl.hide()
        for f in fruits:
            f.hideturtle()
        obstacle_pen.clear()
        hud.clear()                             # Or the HUD stays under the result text
        bar_pen.clear()
        for pool in heart_icons.values():
            for icon in pool:
                icon.hideturtle()
        for icon in power_icons:                # Or they float over the result text
            icon.hideturtle()

    def show_result(winner):
        """End of a round: bank the round, then hand off to the result screen.

        The ledger records the HP each player FINISHED the round with, because the
        match summary weights score by survival (screens.py explains the maths).
        A knocked-out player banks hp 0, so that round scores them nothing.
        """
        game_active['value'] = False
        rounds.append({'P1': p1.score, 'P2': p2.score,
                       'hpP1': max(0, p1.hp), 'hpP2': max(0, p2.hp),
                       'win': '-' if winner == 'draw' else winner.slot})
        if winner != 'draw':                    # Credit the round BEFORE drawing
            round_wins[winner.slot] += 1
        # Rounds also run out: without the MAX_ROUNDS half, a match where every round
        # is a draw would never reach ROUNDS_TO_WIN and never end.
        match_over['value'] = (max(round_wins.values()) >= ROUNDS_TO_WIN
                               or len(rounds) >= MAX_ROUNDS)
        clear_field()
        result_pen.clear()
        draw_result(result_pen, p1, p2, round_wins, rounds,
                    match_over['value'], winner)

        # R and M still work; these are the same two actions as buttons, because a
        # result screen is the one place a player is not already holding the keys.
        again = ImageButton('btn_playgame', -90, -232, 150, 86,
                            label='NEXT' if not match_over['value'] else 'AGAIN',
                            color=HIGHLIGHT)
        back = ImageButton('btn_menu', 90, -232, 110, 63, label='MENU', color=TEXT_DIM)
        wn.onscreenclick(click_router((again, do_restart), (back, to_menu)))

        sfx.play('win')
        wn.update()

    # ===========================================
    # SECTION 5: MAIN GAME LOOP
    # ===========================================
    sfx.play('start')

    def game_loop():
        if STATE['epoch'] != epoch or not game_active['value']:
            return                              # A newer scene took over, or match ended

        moved = {}
        for pl in players:                      # 1. advance
            pl.tick_timers()
            moved[pl.slot] = step(pl)
        for pl in players:                      # 2. pickups and own body
            resolve_fruit(pl)
            if moved[pl.slot]:                  # A self hit needs a move to happen
                resolve_self_collision(pl)

        resolve_head_clash()                    # 3. combat
        resolve_bite(p1, p2)
        resolve_bite(p2, p1)

        for pl in players:                      # 4. draw
            pl.render()
        draw_hud()

        winner = check_win()                    # 5. win check
        if winner is not None:
            for pl in players:
                pl.direction = 'stop'
            show_result(winner)
            return

        wn.update()
        wn.ontimer(game_loop, FRAME_MS)

    game_loop()

# =============================================================================
# ENTRY POINT
# =============================================================================

print(sfx.report())                             # One line, so silence is never a mystery
if sfx.backend == 'silent' or sfx._bad_wavs:    # Something is off - say exactly what
    print(sfx.diagnose())

go_to_scene(menu_scene)
wn.mainloop()
