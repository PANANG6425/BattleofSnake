"""
sprites.py - loads GIF sprites into turtle's shape table.

turtle limitations that shape this file:
  * image shapes must be GIF (PNG is rejected), so a PNG drop-in is converted once
  * image shapes cannot rotate or scale, so each snake needs one head per direction
  * the registered shape NAME is the path string passed to addshape()

Every loader returns None when a file is missing or unreadable. Callers treat None as
"draw the plain colored square instead", so the game always runs even with no assets/.
"""

import os                                       # Filesystem checks
import turtle                                   # For the TurtleGraphicsError type

from config import USE_SPRITES                  # Master on/off switch
from screen import wn, ASSET_PATH               # The Screen (shape table lives on it) and assets/ path


def _png_to_gif(png_path, gif_path):            # Convert a dropped-in PNG to the GIF turtle needs
    try:
        from PIL import Image, ImageOps         # Pillow is optional and only needed for this path
    except ImportError:                         # No Pillow installed
        return False                            # Caller falls back to squares
    try:
        src = Image.open(png_path).convert('RGBA')            # Load the PNG with alpha
        alpha = src.split()[3].point(lambda v: 255 if v > 128 else 0) # GIF alpha is on/off only
        pal = src.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255) # Leave index 255 free
        pal.paste(255, mask=ImageOps.invert(alpha))            # Flag transparent pixels with index 255
        pal.save(gif_path, transparency=255)                   # Write the GIF next to the PNG
        return True                                            # Conversion succeeded
    except Exception:                           # Unreadable or corrupt PNG
        return False                            # Caller falls back to squares


def load_shape(name):                           # Register assets/<name>.gif and return its shape name
    if not USE_SPRITES:                         # Sprites disabled in config
        return None
    gif_path = os.path.join(ASSET_PATH, name + '.gif')  # Expected GIF path
    if not os.path.isfile(gif_path):            # No GIF yet
        png_path = os.path.join(ASSET_PATH, name + '.png') # Look for a PNG with the same name
        if not (os.path.isfile(png_path) and _png_to_gif(png_path, gif_path)): # Try converting it
            return None                         # Nothing usable: fall back to squares
    try:
        wn.addshape(gif_path)                   # Register the image with turtle
        return gif_path                         # The path IS the shape name from now on
    except turtle.TurtleGraphicsError:          # Unsupported or broken GIF
        return None                             # Fall back to squares


def load_direction_set(prefix):                 # Load the 4 directional sprites for one snake
    return {d: load_shape('{}_{}'.format(prefix, d))
            for d in ('up', 'down', 'left', 'right')} # dict keyed by direction name
