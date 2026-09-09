"""
make_sprites.py - generates every GIF sprite the game needs into ./assets/

Run once:  python make_sprites.py

Why GIF: turtle can only register image shapes from .gif files, and it cannot
rotate or scale them, so each snake needs one sprite per facing direction.
Replace any file in assets/ with your own art of the same pixel size and the
game picks it up automatically - no code changes needed.
"""

import os                                       # For building the assets/ output path
from PIL import Image, ImageDraw, ImageOps      # Pillow: image creation, drawing and mask inversion

SS = 4                                          # Supersampling factor: draw big, then shrink for smooth edges
ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets') # Output folder

# Per-player palettes: (main, dark outline, light highlight, ghost main, ghost outline)
PALETTES = {
    'p1': ('#22e0e0', '#0b6a6a', '#b6ffff', '#0e3d3d', '#082424'), # Player 1: cyan family
    'p2': ('#ffa22a', '#8a4a00', '#ffe0a8', '#4a2f0c', '#241705'), # Player 2: orange family
}


def new_canvas(w, h):                           # Create a transparent supersampled RGBA canvas
    img = Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0)) # Fully transparent background
    return img, ImageDraw.Draw(img)             # Return the image plus a draw handle


def save_gif(img, w, h, path):                  # Downsample to final size and save as a transparent GIF
    small = img.resize((w, h), Image.LANCZOS)   # Shrink with high-quality filtering
    alpha = small.split()[3].point(lambda v: 255 if v > 128 else 0) # GIF only supports on/off transparency
    flat = small.convert('RGB')                 # Drop the alpha channel before quantizing
    pal = flat.convert('P', palette=Image.ADAPTIVE, colors=255) # Leave palette index 255 free
    pal.paste(255, mask=ImageOps.invert(alpha)) # Mark every transparent pixel with index 255
    pal.save(path, transparency=255)            # Save with index 255 declared transparent
    print('wrote', os.path.relpath(path, ASSET_DIR).ljust(24), '{}x{}'.format(w, h)) # Progress line


def rounded(draw, box, radius, fill, outline, width):  # Draw a rounded rectangle in supersampled space
    x0, y0, x1, y1 = [v * SS for v in box]      # Scale the box up to supersampled coordinates
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius * SS,
                           fill=fill, outline=outline, width=width * SS) # Body plus outline


def make_head(key, ghost=False):                # Build the head sprite (drawn facing right, then rotated)
    main, dark, light, gmain, gdark = PALETTES[key] # Unpack this player's palette
    body_col = gmain if ghost else main         # Ghost heads use the faded color
    edge_col = gdark if ghost else dark         # Ghost outlines are faded too
    size = 20                                   # Final sprite size in pixels

    img, d = new_canvas(size, size)             # Fresh transparent canvas
    rounded(d, (1, 2, 18, 17), 5, body_col, edge_col, 1) # Head capsule, slightly flattened vertically

    if not ghost:                               # Ghost heads stay featureless so they read as "cloaked"
        for eye_y in (6, 12):                   # Two eyes: one upper, one lower (sprite faces right)
            d.ellipse([12 * SS, (eye_y - 1) * SS, 16 * SS, (eye_y + 3) * SS],
                      fill='#ffffff', outline=edge_col, width=max(1, SS // 2)) # White eyeball
            d.ellipse([14 * SS, eye_y * SS, 15.6 * SS, (eye_y + 2) * SS], fill='#101018') # Dark pupil
        d.line([4 * SS, 6 * SS, 10 * SS, 6 * SS], fill=light, width=SS) # Highlight streak along the top

    return img, size                            # Return the drawing and its final pixel size


def make_body(key, ghost=False):                # Build one body-segment sprite
    main, dark, light, gmain, gdark = PALETTES[key] # Unpack this player's palette
    body_col = gmain if ghost else main         # Faded color for the ghost variant
    edge_col = gdark if ghost else dark         # Faded outline for the ghost variant
    size = 16                                   # Final sprite size in pixels

    img, d = new_canvas(size, size)             # Fresh transparent canvas
    rounded(d, (1, 1, 14, 14), 4, body_col, edge_col, 1) # Segment block
    if not ghost:                               # Scale detail only on the visible variant
        rounded(d, (4, 4, 11, 11), 2, light, None, 0) # Lighter inner scale marking
    return img, size                            # Return the drawing and its final pixel size


def make_heart(filled=True):                    # Build the HP heart icon (full or empty)
    size = 18                                   # Final sprite size in pixels
    img, d = new_canvas(size, size)             # Fresh transparent canvas
    fill = '#ff3355' if filled else '#3a3a46'   # Full hearts are red, spent hearts are dark gray
    edge = '#8a0f22' if filled else '#5c5c6b'   # Spent hearts keep a lighter gray outline
    w = max(1, SS)                              # Outline thickness in supersampled pixels

    d.ellipse([2 * SS, 2 * SS, 9 * SS, 9 * SS], fill=fill, outline=edge, width=w)  # Left lobe
    d.ellipse([8 * SS, 2 * SS, 15 * SS, 9 * SS], fill=fill, outline=edge, width=w) # Right lobe
    d.polygon([(2 * SS, 6 * SS), (15 * SS, 6 * SS), (8.5 * SS, 15 * SS)],
              fill=fill, outline=edge)          # Bottom point of the heart
    if filled:                                  # Add a small gloss dot to full hearts only
        d.ellipse([4 * SS, 4 * SS, 6 * SS, 6 * SS], fill='#ffb3c0') # Highlight
    return img, size                            # Return the drawing and its final pixel size


def make_fruit():                               # Build the fruit pickup sprite
    size = 16                                   # Final sprite size in pixels
    img, d = new_canvas(size, size)             # Fresh transparent canvas
    d.ellipse([2 * SS, 4 * SS, 14 * SS, 15 * SS], fill='#e8203a', outline='#7a0a18', width=SS) # Apple body
    d.ellipse([4 * SS, 6 * SS, 7 * SS, 9 * SS], fill='#ff8a9a')  # Glossy highlight
    d.line([8 * SS, 5 * SS, 9 * SS, 1 * SS], fill='#6b3a12', width=SS) # Stem
    d.polygon([(9 * SS, 3 * SS), (14 * SS, 1 * SS), (11 * SS, 6 * SS)], fill='#3fbf4a') # Leaf
    return img, size                            # Return the drawing and its final pixel size


def build_all():                                # Generate and write every sprite the game loads
    os.makedirs(ASSET_DIR, exist_ok=True)       # Make sure assets/ exists

    # Rotation applied to the right-facing artwork to produce each facing direction
    rotations = {'right': 0, 'up': 90, 'left': 180, 'down': 270}

    for key in ('p1', 'p2'):                    # Both players get a full sprite set
        for ghost in (False, True):             # Normal set plus the cloaked (Invisibility) set
            suffix = '_ghost' if ghost else ''  # Filename suffix for the cloaked variant
            head, hsize = make_head(key, ghost) # Draw the head once, facing right
            for direction, angle in rotations.items(): # Emit one file per facing direction
                turned = head.rotate(angle, resample=Image.BICUBIC, expand=False) # Rotate the artwork
                save_gif(turned, hsize, hsize,
                         os.path.join(ASSET_DIR, '{}_head_{}{}.gif'.format(key, direction, suffix)))
            body, bsize = make_body(key, ghost) # Draw the body segment
            save_gif(body, bsize, bsize,
                     os.path.join(ASSET_DIR, '{}_body{}.gif'.format(key, suffix)))

    heart, hs = make_heart(True)                # Full HP heart
    save_gif(heart, hs, hs, os.path.join(ASSET_DIR, 'heart_full.gif'))
    heart, hs = make_heart(False)               # Empty HP heart
    save_gif(heart, hs, hs, os.path.join(ASSET_DIR, 'heart_empty.gif'))
    fruit, fs = make_fruit()                    # Fruit pickup
    save_gif(fruit, fs, fs, os.path.join(ASSET_DIR, 'fruit.gif'))


if __name__ == '__main__':                      # Allow running this file directly
    build_all()                                 # Generate the whole sprite set
    print('\nDone. Sprites are in:', ASSET_DIR) # Tell the user where the files landed
