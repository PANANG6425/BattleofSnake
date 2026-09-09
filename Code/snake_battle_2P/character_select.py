"""
character_select.py - fighting-game style card selector.

One big card per player showing the current character, with clickable arrows on
either side to flip through the roster, then a power row underneath. Enter starts.
1P mode shows one panel; 2P shows two.

The portrait is drawn with turtle only - a scaled compound shape tinted with the
character's colour, plus pen-drawn body segments. No image files are generated for
it, and none could be reused: turtle CANNOT scale an image shape, so the 20x20
.gif head stays 20x20 no matter what shapesize() says. A compound shape scales.

The roster and the power list are read from their registries (characters.py,
powers.py), and the layout is computed from their LENGTH, so adding a character or
a power needs no change here. Characters differ only in colour, so picking one
never changes the balance - it is a skin, and in 2P it is also how you tell the
snakes apart. That is why the two players cannot pick the same character: the
arrows skip a character the other player holds. Powers may be duplicated freely.

Everything is clickable. Keyboard is a full second path:
    P1   A / D  character    W / S  power
    P2   Left / Right        Up / Down
"""

import turtle
from scene_manager import wn, go_to_scene
from ui_helpers import (draw_label, inside_rect, shape_turtle, header_strip,
                        rounded_card, make_head_shape, filled_rect)
from characters import CHARACTERS, DEFAULTS as CHAR_DEFAULTS, by_key
from powers import POWERS, DEFAULTS as POWER_DEFAULTS, by_key as power_by_key

# Layout, top to bottom inside a panel. Every y here is spaced so nothing overlaps:
#   header 180..208 | arrows 143..173 | card 9..127 | dots -4 | POWER label -24
#   power boxes -84..-40 | power name -104 | blurb -122 | summary -174
PANEL_W, PANEL_H = 300, 396
PANEL_CY = 10
HEADER_H = 28

CARD_W, CARD_H = 190, 118                       # The one big character card
CARD_CY = 68
ARROW_Y = 158                                   # Flip arrows sit above the card
ARROW_DX = 128                                  # Distance from panel centre
ARROW_W, ARROW_H = 26, 30
ARROW_HIT = 46                                  # Clickable square around an arrow

DOTS_Y = -4                                     # Roster position dots, under the card
POWER_BOX = 44
POWER_GAP = 8
POWER_Y = -62

COL_PANEL_BG = '#141b24'
COL_CARD_BG = '#0e141b'
COL_CARD_EDGE = '#39424f'
COL_MUTED = '#8a93a3'
COL_FAINT = '#4a4a4a'
COL_ARROW = '#c7ccd4'
SLOT_COLOR = {'P1': 'mediumseagreen', 'P2': 'steelblue'}

# One scaled head shape per character, tinted with that character's colours. Names
# are stable so re-registering on a later visit to this screen is harmless.
HEAD_SHAPE = {}
for _ch in CHARACTERS:
    _name = 'char_head_' + _ch['key']
    _main, _dark, _light = _ch['palette'][0], _ch['palette'][1], _ch['palette'][2]
    wn.register_shape(_name, make_head_shape(_main, _dark, _light))
    HEAD_SHAPE[_ch['key']] = _name


def character_select_scene(epoch, mode):
    from menu import menu_scene                 # local imports avoid circular imports at load time
    from snake_1p import game_1p_scene
    from snake_2p import game_2p_scene

    wn.title('Character Select')
    wn.bgcolor('#0b0f14')

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
        x = panel_cx[slot] + (index - (n - 1) / 2) * (POWER_BOX + POWER_GAP)
        return x, POWER_Y

    def arrow_pos(slot, direction):
        return panel_cx[slot] + direction * ARROW_DX, ARROW_Y

    def taken_by_other(slot, char_key):
        return any(s != slot and chosen[s]['char'] == char_key for s in slots)

    # --- pens -------------------------------------------------------------------
    # Static chrome is drawn once. Everything that changes on a pick lives on these
    # pens, which are cleared and redrawn instead of spawning turtles per click.
    art_pen = turtle.Turtle(); art_pen.hideturtle(); art_pen.penup()
    text_pen = turtle.Turtle(); text_pen.hideturtle(); text_pen.penup()

    # The portraits are shape turtles, one per panel, whose shape is swapped on a
    # pick. They are created after the pens so they draw on top of the card.
    portrait = {}

    def box(pen, cx, cy, w, h, edge, width):
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

    def fill_square(pen, cx, cy, size, color):
        pen.color(color, color)
        pen.penup()
        pen.goto(cx - size / 2, cy - size / 2)
        pen.setheading(0)
        pen.pendown()
        pen.begin_fill()
        for _ in range(2):
            pen.forward(size)
            pen.left(90)
            pen.forward(size)
            pen.left(90)
        pen.end_fill()
        pen.penup()

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

    def write(pen, x, y, text, size, color, align='center'):
        pen.color(color)
        pen.goto(x, y)
        pen.write(text, align=align, font=('Courier', size, 'bold'))

    def draw_body_trail(pen, cx, cy, color):
        """A few segments trailing behind the portrait head, so it reads as a snake."""
        for i, (dx, dy) in enumerate(((-46, -14), (-72, -30), (-92, -50))):
            fill_square(pen, cx + dx, cy + dy, 20 - i * 2, color)

    def redraw():
        art_pen.clear()
        text_pen.clear()

        for slot in slots:
            cx = panel_cx[slot]
            ch = by_key(chosen[slot]['char'])
            power = power_by_key(chosen[slot]['power'])

            # Body trail inside the card, then the portrait shape floats above it.
            draw_body_trail(art_pen, cx + 22, CARD_CY + 22, ch['main'])
            portrait[slot].shape(HEAD_SHAPE[ch['key']])

            write(text_pen, cx, CARD_CY - CARD_H / 2 + 12, ch['name'], 15, ch['main'])

            # Dots showing where you are in the roster.
            order = [c['key'] for c in CHARACTERS]
            here = order.index(ch['key'])
            for i, key in enumerate(order):
                dx = (i - (len(order) - 1) / 2) * 16
                fill_square(art_pen, cx + dx, DOTS_Y, 7,
                            ch['main'] if i == here else COL_CARD_EDGE)

            for i, pw in enumerate(POWERS):
                px, py = power_pos(slot, i)
                selected = pw['key'] == power['key']
                box(art_pen, px, py, POWER_BOX, POWER_BOX,
                    'gold' if selected else COL_CARD_EDGE, 4 if selected else 2)

            write(text_pen, cx, POWER_Y - POWER_BOX / 2 - 20, power['name'], 12, 'gold')
            write(text_pen, cx, POWER_Y - POWER_BOX / 2 - 38, power['blurb'], 8, COL_MUTED)
            write(text_pen, cx, PANEL_CY - PANEL_H / 2 + 14,
                  '{}  /  {}'.format(ch['name'], power['name']), 11, ch['main'])

        wn.update()

    # --- static chrome -----------------------------------------------------------
    # The panel, the card frame and the flip arrows never change, so they are drawn
    # once on their own pens. Only the portrait, the name, the roster dots and the
    # power highlight are repainted on a pick.
    chrome = turtle.Turtle(); chrome.hideturtle(); chrome.penup()
    for slot in slots:
        cx = panel_cx[slot]
        rounded_card(cx, PANEL_CY, PANEL_W, PANEL_H, 16, COL_PANEL_BG, SLOT_COLOR[slot])
        header_strip(cx, PANEL_CY + PANEL_H / 2 - HEADER_H, PANEL_W, HEADER_H,
                     SLOT_COLOR[slot], slot, '#0b0f14')
        filled_rect(cx, CARD_CY, CARD_W, CARD_H, COL_CARD_BG, SLOT_COLOR[slot], 3)
        triangle(chrome, *arrow_pos(slot, -1), ARROW_W, ARROW_H, -1, COL_ARROW)
        triangle(chrome, *arrow_pos(slot, 1), ARROW_W, ARROW_H, 1, COL_ARROW)
        draw_label(cx, POWER_Y + POWER_BOX / 2 + 16, 'POWER', 9, COL_MUTED)

    for slot in slots:
        portrait[slot] = shape_turtle(HEAD_SHAPE[CHARACTERS[0]['key']],
                                      panel_cx[slot] + 22, CARD_CY + 22, size=3.0)
        for i, pw in enumerate(POWERS):
            px, py = power_pos(slot, i)
            shape_turtle(pw['icon'], px, py, size=1.1)

    title = 'CHARACTER SELECT - 1 PLAYER' if mode == '1P' else 'CHARACTER SELECT - 2 PLAYERS'
    draw_label(0, 272, title, 18, 'white')
    draw_label(0, -212, 'PRESS ENTER TO START', 14, 'gold')
    if mode == '1P':
        draw_label(0, -244, 'Click the arrows, or  A / D = character   W / S = power', 9, COL_FAINT)
    else:
        draw_label(0, -240, 'P1  A / D = character   W / S = power', 9, COL_FAINT)
        draw_label(0, -258, 'P2  Left / Right = character   Up / Down = power', 9, COL_FAINT)
    draw_label(0, -284, 'ESC = back to menu', 8, COL_FAINT)

    # --- selection ---------------------------------------------------------------
    def step_char(slot, delta):
        if slot not in chosen:
            return
        order = [c['key'] for c in CHARACTERS]
        i = order.index(chosen[slot]['char'])
        for _ in range(len(order)):             # Skip a character the other player holds
            i = (i + delta) % len(order)
            if not taken_by_other(slot, order[i]):
                chosen[slot]['char'] = order[i]
                redraw()
                return

    def step_power(slot, delta):
        if slot not in chosen:
            return
        order = [p['key'] for p in POWERS]
        i = order.index(chosen[slot]['power'])
        chosen[slot]['power'] = order[(i + delta) % len(order)]
        redraw()

    def pick_power(slot, power_key):
        if slot not in chosen:
            return
        chosen[slot]['power'] = power_key
        redraw()

    def on_click(x, y):
        for slot in slots:
            for direction in (-1, 1):
                ax, ay = arrow_pos(slot, direction)
                if inside_rect(x, y, ax, ay, ARROW_HIT, ARROW_HIT):
                    step_char(slot, direction)
                    return
            for i, pw in enumerate(POWERS):
                px, py = power_pos(slot, i)
                if inside_rect(x, y, px, py, POWER_BOX + POWER_GAP, POWER_BOX + 10):
                    pick_power(slot, pw['key'])
                    return
            # Clicking the card itself steps forward, so the whole card is a target.
            if inside_rect(x, y, panel_cx[slot], CARD_CY, CARD_W, CARD_H):
                step_char(slot, 1)
                return

    def try_start():
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
