"""
scene_manager.py - the ONE turtle window shared by every screen, plus the sprite
loader and the scene-switching helpers. Every other file imports `wn` from here
instead of creating its own window (turtle only allows one window per process).
"""

import turtle
import os

wn = turtle.Screen()                            # The single game window for the whole app
wn.title('Snake Game')
wn.bgcolor('black')
wn.setup(width=800, height=600)
wn.tracer(0)                                    # Manual screen updates for smooth, controllable frames

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
USE_SPRITES = True                              # Set False to force plain-square fallback everywhere

_shape_cache = {}                                # Memoizes already-registered sprite names -> path/None

def load_shape(name):                           # Register one GIF sprite with turtle, memoized
    if not USE_SPRITES:
        return None
    if name in _shape_cache:
        return _shape_cache[name]
    gif_path = os.path.join(ASSET_DIR, name + '.gif')
    if not os.path.isfile(gif_path):
        png_path = os.path.join(ASSET_DIR, name + '.png')
        if os.path.isfile(png_path):
            try:
                from PIL import Image, ImageOps
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
    except turtle.TurtleGraphicsError:
        _shape_cache[name] = None
        return None

# --- Scene manager ---
# Every key used anywhere in the app - unbound at the start of every scene so a
# leftover handler from the previous screen can never fire on the new one.
ALL_KEYS = ['Up', 'Down', 'Left', 'Right', 'w', 'a', 's', 'd',
            'q', 'e', 'o', 'p', 'r', 'm', 'space', 'Return', '1', '2', 'Escape']

STATE = {'epoch': 0}                            # Changes on every scene switch; loops check it to self-stop

def unbind_all_keys():
    for k in ALL_KEYS:
        wn.onkeypress(None, k)
    wn.onscreenclick(None)                      # Menu buttons hit-test screen clicks; drop that too

def clear_all_turtles():                        # Destroy every turtle from the previous scene
    """Every scene builds its own turtles. Hiding them is not enough: a hidden turtle
    stays in screen._turtles forever and keeps its canvas item, so each scene switch
    used to leak ~26 turtles and ~78 canvas items - the game got slower the longer you
    played. Wipe the drawings, drop the canvas item, then unregister the turtle."""
    registry = getattr(wn, '_turtles', None)    # The Screen's list of live turtles
    for t in list(turtle.turtles()):
        try:
            t.onclick(None)                     # Drop click handlers before the item goes away
            t.clear()                           # Remove its lines and stamps
            t.hideturtle()                      # Remove the cursor graphic
            t.penup()                           # Never draw on a later move
        except Exception:
            pass
        # clear() leaves the turtle holding a fresh empty line item, and the cursor
        # polygon is a canvas item of its own. Both outlive the turtle unless deleted
        # here, which is what kept the canvas item count climbing 52 per scene switch.
        doomed = list(getattr(t, 'items', ()))          # currentLineItem + any leftover lines
        doomed.append(getattr(t, 'drawingLineItem', None))  # The animation line, not listed in .items
        doomed.append(getattr(t, '_fillitem', None))    # An unfinished begin_fill(), if any
        doomed.append(getattr(t.turtle, '_item', None))  # The cursor polygon
        for item in doomed:
            if item is None:
                continue
            try:
                wn._delete(item)                # Private API, so guarded: worst case we just leak as before
            except Exception:
                pass
        if registry is not None:                # Unregister so turtles() stops growing
            try:
                registry.remove(t)
            except ValueError:
                pass

def go_to_scene(builder, *args, **kwargs):      # Central entry point for every scene transition
    STATE['epoch'] += 1                         # Any running loop from the old scene sees this and stops
    unbind_all_keys()
    clear_all_turtles()
    wn.bgcolor('black')
    builder(STATE['epoch'], *args, **kwargs)