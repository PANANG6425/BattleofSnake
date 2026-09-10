"""
import_assets.py - turns the hand-drawn art in ../../Asset/ into GIFs the game can
actually load, and writes them into ./assets/.

Run:  python import_assets.py          (needs Pillow: pip install pillow)

This is a BUILD TOOL, exactly like make_sprites.py. The generated assets/*.gif are
committed, so the game itself never needs Pillow and never reads ../../Asset/.

WHY A CONVERTER IS NEEDED AT ALL
--------------------------------
The source art cannot be dropped into assets/ as-is. Three turtle limits decide
everything this file does:

  1. tkinter reads only the FIRST FRAME of an animated GIF. Every piece of source
     art is a 150-frame animation, so the frame has to be extracted here.
  2. turtle cannot SCALE an image shape - shapesize() is ignored. The pixel size of
     the file IS the size on screen, so each target slot needs its own resize. The
     skill art is 1200x1200 and the character art 2480x3508; unresized they would
     cover the whole window.
  3. GIF transparency is a single palette index, not an alpha channel. Anything with
     soft edges has to be thresholded to on/off transparency (same trick as
     make_sprites.save_gif).

Slots produced, and where each one is used:

    speed/stealth/shield/phase/feast _icon.gif   40x40   Character Select power boxes
    fruit_<name>.gif                             22x22   the fruit pickup (random one)
    btn_start / btn_playgame.gif                150x86   primary buttons
    btn_menu / btn_setting / btn_exit.gif       110x63   secondary buttons
    <character key>_portrait.gif                 80x80   Character Select card art
    icon.png + icon.ico                          48x48   window icon

Every one of these is OPTIONAL at runtime: engine.load_shape() returns None for a
missing file and each call site falls back to what the game drew before.
"""

import colorsys
import os
import shutil

# Build tool only. The game does not import this file, so Pillow stays optional.
from PIL import Image, ImageChops, ImageDraw, ImageOps  # type: ignore[import-not-found]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, 'assets')            # Output: what the game loads
SOURCE_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '..', 'Asset'))  # Input: the art

# ===========================================
# SOURCE -> SLOT MAPPING
# ===========================================
# The five drawings line up one-to-one with config.POWERS, so the file name on the
# left is simply the 'icon' key on the right. Renaming a power in config.py means
# renaming its entry here too - that is the only coupling.
POWER_ART = {
    'acceleration_skill.gif': 'speed_icon',     # SPEED
    'vanished_skill.gif':     'stealth_icon',   # STEALTH
    'shield_skill.gif':       'shield_icon',    # SHIELD
    'through_wall_skill.gif': 'phase_icon',     # PHASE
    'eating_skill.gif':       'feast_icon',     # FEAST
}
POWER_PX = 40                                   # Fits the 44px POWER box in screens.py

FRUIT_ART = ['Apple.gif', 'Banana.gif', 'Grape.gif', 'Guava.gif', 'Pineapple.gif']
FRUIT_PX = 22                                   # Just under FRUIT_REACH (18) x 2

# Buttons come in two sizes because turtle cannot scale: a primary size for the
# action a screen is really asking for, and a smaller one for everything else.
# btn_setting and btn_exit are imported but not placed by any screen yet - the
# Settings screen is not built. They cost nothing sitting in assets/ and are ready
# for whoever builds it (wireframe screen 6).
BUTTON_ART = {
    'Start.gif':    ('btn_start',    150, 86),
    'PlayGame.gif': ('btn_playgame', 150, 86),
    'Menu.gif':     ('btn_menu',     110, 63),
    'Setting.gif':  ('btn_setting',  110, 63),
    'Exit.gif':     ('btn_exit',     110, 63),
}

# The character posters are A4-shaped (2480x3508) and mostly empty paper, and there
# are only two of them for four characters - so each drawing is used twice, once as
# drawn and once with the COSTUME hue rotated (see recolour() for why only the
# costume moves). The two silhouettes are different enough - the Thai sash and
# collar against the Japanese kimono's grey band - that a recolour still reads as a
# different character rather than a palette swap.
#
# key -> (source file, hue rotation in degrees). The key must match a character key
# in config.CHARACTERS, because screens.py looks for assets/<key>_portrait.gif.
PORTRAIT_ART = {
    'p1': ('Snake_thai.gif',    0),             # SIAM    - red, as drawn
    'p2': ('Snake_japan.gif',   0),             # SAKURA  - blue, as drawn
    'p3': ('Snake_thai.gif',  130),             # NAGA    - green
    'p4': ('Snake_japan.gif',  60),             # KOI     - magenta
}
COSTUME_SAT = 0.30                              # See recolour()
# Full page width, cut just above the head: a near-square that keeps the costume,
# which is the only thing telling the two characters apart.
PORTRAIT_CROP = (0.0, 0.29, 1.0, 1.0)           # left, top, right, bottom as fractions
PORTRAIT_PX = 80

ICON_ART = 'Icon.ico'
ICON_PX = 48


# ===========================================
# HELPERS
# ===========================================
def source(name):
    return os.path.join(SOURCE_DIR, name)


def first_frame(path):
    """The first frame of a GIF as RGBA.

    tkinter would take this same frame and ignore the other 149, so extracting it
    here is not a downgrade - it is making explicit what turtle was going to do
    anyway, at a size and with a transparency mask that actually work.
    """
    img = Image.open(path)
    img.seek(0)
    return img.convert('RGBA')


def trim_transparent(img, pad=2):
    """Crop away fully transparent margins so the subject fills its slot.

    The fruit and button art are drawn on a big transparent canvas. Resizing without
    trimming first would shrink the empty space too, leaving a 22px fruit that is
    only 8px of actual fruit.
    """
    box = img.split()[3].getbbox()
    if box is None:
        return img
    left, top, right, bottom = box
    left, top = max(0, left - pad), max(0, top - pad)
    right, bottom = min(img.width, right + pad), min(img.height, bottom + pad)
    return img.crop((left, top, right, bottom))


def fit_into(img, w, h):
    """Scale to fit inside w x h without distorting, then centre on a transparent bed."""
    src = img.copy()
    src.thumbnail((w, h), Image.LANCZOS)
    bed = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    bed.paste(src, ((w - src.width) // 2, (h - src.height) // 2), src)
    return bed


def round_corners(img, radius):
    """Soften the corners of an opaque tile so it does not read as a black box.

    The skill drawings are full-bleed illustrations on solid black - there is no
    subject to cut out, because the black IS part of the art. Rounding the corners
    is what turns that square into something that looks placed on the card.
    """
    corner = Image.new('L', img.size, 0)
    ImageDraw.Draw(corner).rounded_rectangle([0, 0, img.width - 1, img.height - 1],
                                             radius=radius, fill=255)
    out = img.copy()
    # Keep whatever transparency the art already had, and clear the corners on top
    # of it - ImageChops.darker is just "the more transparent of the two wins".
    out.putalpha(ImageChops.darker(img.split()[3], corner))
    return out


def recolour(img, degrees, threshold=COSTUME_SAT):
    """Rotate the hue of the COSTUME only, leaving the snake and the paper alone.

    Saturation is what separates them, and it separates them cleanly: the outfit is
    strongly coloured (the Thai red is s=0.92, the Japanese blue s=1.0) while the
    snake's cream/pink skin and the cream page are barely tinted at all (s<0.25).
    So anything above `threshold` is costume and gets moved; everything else keeps
    its exact pixels, which is what stops a recolour from turning the snake itself
    green and giving away that it is the same drawing.

    Hue rotation rather than a colour swap because the costume is not flat - it has
    shading, an outline and a highlight, and rotating the hue carries all of them
    across together with their shading intact.
    """
    if not degrees:
        return img
    out = img.copy()
    px = out.load()
    step = degrees / 360.0
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if s <= threshold:
                continue
            r2, g2, b2 = colorsys.hsv_to_rgb((h + step) % 1.0, s, v)
            px[x, y] = (int(r2 * 255), int(g2 * 255), int(b2 * 255), a)
    return out


def save_gif(img, path):
    """Write RGBA as a GIF with index 255 declared transparent.

    Identical to make_sprites.save_gif - GIF has no alpha channel, only one
    see-through palette entry, so soft edges must be thresholded to on/off first.
    """
    alpha = img.split()[3].point(lambda v: 255 if v > 128 else 0)
    pal = img.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255)
    pal.paste(255, mask=ImageOps.invert(alpha))
    pal.save(path, transparency=255)
    print('wrote', os.path.basename(path).ljust(22), '{}x{}'.format(*img.size))


# ===========================================
# BUILDERS - one per slot kind
# ===========================================
def build_power_icons():
    for art, name in POWER_ART.items():
        path = source(art)
        if not os.path.isfile(path):
            print('skip ', art, '- not found')
            continue
        img = first_frame(path).resize((POWER_PX, POWER_PX), Image.LANCZOS)
        save_gif(round_corners(img, 6), os.path.join(ASSET_DIR, name + '.gif'))


def build_fruit():
    for art in FRUIT_ART:
        path = source(art)
        if not os.path.isfile(path):
            print('skip ', art, '- not found')
            continue
        name = 'fruit_' + os.path.splitext(art)[0].lower()
        img = fit_into(trim_transparent(first_frame(path)), FRUIT_PX, FRUIT_PX)
        save_gif(img, os.path.join(ASSET_DIR, name + '.gif'))


def build_buttons():
    for art, (name, w, h) in BUTTON_ART.items():
        path = source(art)
        if not os.path.isfile(path):
            print('skip ', art, '- not found')
            continue
        img = fit_into(trim_transparent(first_frame(path), pad=0), w, h)
        save_gif(img, os.path.join(ASSET_DIR, name + '.gif'))


def build_portraits():
    for key, (art, degrees) in PORTRAIT_ART.items():
        path = source(art)
        if not os.path.isfile(path):
            print('skip ', art, '- not found')
            continue
        img = first_frame(path)
        l, t, r, b = PORTRAIT_CROP
        img = img.crop((int(l * img.width), int(t * img.height),
                        int(r * img.width), int(b * img.height)))
        img = recolour(img, degrees)            # Costume only - see recolour()
        # The poster's cream paper is kept on purpose: it reads as a portrait tile on
        # the dark card, and cutting the snake out of a pastel background with GIF's
        # 1-bit transparency would leave a hard jagged edge.
        img = img.resize((PORTRAIT_PX, PORTRAIT_PX), Image.LANCZOS)
        save_gif(round_corners(img, 10),
                 os.path.join(ASSET_DIR, key + '_portrait.gif'))


def build_window_icon():
    """engine._set_window_icon() tries assets/icon.png first, then icon.ico.

    Both are written: .png goes through iconphoto and works on every platform, .ico
    only through iconbitmap and only on Windows - keeping both means the icon shows
    up wherever the game is run.
    """
    path = source(ICON_ART)
    if not os.path.isfile(path):
        print('skip ', ICON_ART, '- not found')
        return
    img = Image.open(path).convert('RGBA').resize((ICON_PX, ICON_PX), Image.LANCZOS)
    img.save(os.path.join(ASSET_DIR, 'icon.png'))
    print('wrote', 'icon.png'.ljust(22), '{}x{}'.format(*img.size))
    shutil.copyfile(path, os.path.join(ASSET_DIR, 'icon.ico'))
    print('wrote', 'icon.ico'.ljust(22), '(copied)')


def build_all():
    if not os.path.isdir(SOURCE_DIR):
        raise SystemExit('Source art not found: {}\n'
                         'Expected the repo layout  <repo>/Asset/  and  '
                         '<repo>/Code/snake_battle_2P/'.format(SOURCE_DIR))
    os.makedirs(ASSET_DIR, exist_ok=True)
    build_power_icons()
    build_fruit()
    build_buttons()
    build_portraits()
    build_window_icon()


if __name__ == '__main__':
    build_all()
    print('\nDone. Imported art is in:', ASSET_DIR)
