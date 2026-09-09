"""
screen.py - owns the single turtle Screen.

turtle's Screen is a singleton, so exactly one module should create it. Every other
module imports `wn` from here. Import this module before creating any Turtle object,
otherwise turtle builds a default window behind your back.
"""

import turtle                                   # The graphics library the whole game is built on
import os                                       # Used to build the assets/ path

from config import TITLE, BG_COLOR, WIN_W, WIN_H, ASSET_DIR # Window settings

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # Folder this file lives in
ASSET_PATH = os.path.join(BASE_DIR, ASSET_DIR)  # Absolute path to assets/, used by sprites and sounds

wn = turtle.Screen()                            # Create the one and only game window
wn.title(TITLE)                                 # Set the window title
wn.bgcolor(BG_COLOR)                            # Set the background color
wn.setup(width=WIN_W, height=WIN_H)             # Set the window size
wn.tracer(0)                                    # Turn off auto-redraw: we call wn.update() once per frame


def new_pen(color=None, visible=False):         # Helper: create a ready-to-use drawing turtle
    pen = turtle.Turtle()                       # Instantiate a Turtle object
    pen.penup()                                 # Lift the pen so moving never draws by accident
    if not visible:                             # Most pens are invisible cursors
        pen.hideturtle()                        # Hide the cursor graphic
    if color:                                   # Optional starting color
        pen.color(color)                        # Apply it
    return pen                                  # Hand the pen back to the caller
