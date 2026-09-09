"""
character_select.py - fighting-game style card selector.

One screen per match: each player picks a CHARACTER from the roster and a POWER
(SPEED or STEALTH), then Enter starts. 1P mode shows one panel; 2P shows two.

Characters differ only in colour (see characters.py), so picking one never changes
the balance - it is a skin, and in 2P it is also how you tell the snakes apart.
That is why the two players cannot pick the same character: a card already taken by
the other player is drawn dimmed and ignores clicks.

Everything is clickable. Keyboard is a full second path so the screen is usable
without a mouse:
    P1   A / D  move card    W / S  pick power
    P2   Left / Right        Up / Down
"""

import turtle
from scene_manager import wn, go_to_scene, load_shape
from ui_helpers import (filled_rect, draw_label, inside_rect, shape_turtle,
                        header_strip, rounded_card)
from characters import CHARACTERS, DEFAULTS, by_key

POWERS = ('SPEED', 'STEALTH')
POWER_ICON = {'SPEED': 'speed_icon', 'STEALTH': 'stealth_icon'}

CARD_W, CARD_H = 128, 62                        # One character card
CARD_GAP_X, CARD_GAP_Y = 8, 8
POWER_BOX = 52                                  # One power button

PANEL_W, PANEL_H = 300, 424
PANEL_CY = -6

COL_PANEL_BG = '#141b24'
COL_CARD_BG = '#1b2430'
COL_CARD_EDGE = '#39424f'
COL_TAKEN_BG = '#101418'
COL_TAKEN_EDGE = '#23282f'
COL_MUTED = '#8a93a3'
COL_FAINT = '#4a4a4a'
SLOT_COLOR = {'P1': 'mediumseagreen', 'P2': 'steelblue'}


def character_select_scene(epoch, mode):
    from menu import menu_scene                 # local imports avoid circular imports at load time
    from snake_1p import game_1p_scene
    from snake_2p import game_2p_scene

    wn.title('Character Select')
    wn.bgcolor('#0b0f14')

    slots = ['P1'] if mode == '1P' else ['P1', 'P2']
    panel_cx = {'P1': 0} if mode == '1P' else {'P1': -158, 'P2': 158}

    # Pre-select something valid so Enter always has a legal choice, and so the two
    # players never start out holding the same character.
    chosen = {}
    for i, slot in enumerate(slots):
        chosen[slot] = {'char': DEFAULTS[i] if i < len(DEFAULTS) else CHARACTERS[i]['key'],
                        'power': POWERS[i % len(POWERS)]}

    # --- layout, computed once ---------------------------------------------------
    cols = 2
    rows = (len(CHARACTERS) + cols - 1) // cols
    grid_top = PANEL_CY + PANEL_H / 2 - 96      # y of the first card row's centre

    def card_pos(slot, index):
        r, c = divmod(index, cols)
        x = panel_cx[slot] + (c - (cols - 1) / 2) * (CARD_W + CARD_GAP_X)
        y = grid_top - r * (CARD_H + CARD_GAP_Y)
        return x, y

    def power_pos(slot, index):
        x = panel_cx[slot] + (index - (len(POWERS) - 1) / 2) * (POWER_BOX + 44)
        y = grid_top - rows * (CARD_H + CARD_GAP_Y) - 62
        return x, y

    def taken_by_other(slot, char_key):
        return any(s != slot and chosen[s]['char'] == char_key for s in slots)

    # --- redrawable layers -------------------------------------------------------
    # Static chrome is drawn once. Everything that changes on a pick lives on these
    # pens, which get cleared and redrawn instead of spawning new turtles per click.
    card_pen = turtle.Turtle(); card_pen.hideturtle(); card_pen.penup()
    text_pen = turtle.Turtle(); text_pen.hideturtle(); text_pen.penup()
    ready_pen = turtle.Turtle(); ready_pen.hideturtle(); ready_pen.penup()

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

    def write(pen, x, y, text, size, color, align='center'):
        pen.color(color)
        pen.goto(x, y)
        pen.write(text, align=align, font=('Courier', size, 'bold'))

    def redraw():
        """Repaint the selection state: card frames, names, power frames, ready line."""
        card_pen.clear()
        text_pen.clear()

        for slot in slots:
            sel_char = chosen[slot]['char']
            sel_power = chosen[slot]['power']

            for i, ch in enumerate(CHARACTERS):
                cx, cy = card_pos(slot, i)
                taken = taken_by_other(slot, ch['key'])
                selected = ch['key'] == sel_char

                if selected:
                    edge, width = SLOT_COLOR[slot], 4
                elif taken:
                    edge, width = COL_TAKEN_EDGE, 2
                else:
                    edge, width = COL_CARD_EDGE, 2
                box(card_pen, cx, cy, CARD_W, CARD_H, edge, width)

                # A colour chip stands in for a portrait: the characters differ only
                # by colour, so the chip IS the character.
                chip = ch['main'] if not taken else ch['dim']
                card_pen.color(chip, chip)
                card_pen.penup()
                card_pen.goto(cx - CARD_W / 2 + 14, cy - 11)
                card_pen.setheading(0)
                card_pen.pendown()
                card_pen.begin_fill()
                for _ in range(2):
                    card_pen.forward(22)
                    card_pen.left(90)
                    card_pen.forward(22)
                    card_pen.left(90)
                card_pen.end_fill()
                card_pen.penup()

                name_col = 'white' if selected else (COL_TAKEN_EDGE if taken else COL_MUTED)
                write(text_pen, cx + 14, cy - 8, ch['name'], 11, name_col)
                if taken:
                    write(text_pen, cx + 14, cy - 24, 'TAKEN', 7, COL_TAKEN_EDGE)

            for i, power in enumerate(POWERS):
                px, py = power_pos(slot, i)
                selected = power == sel_power
                box(card_pen, px, py, POWER_BOX, POWER_BOX,
                    'gold' if selected else COL_CARD_EDGE, 4 if selected else 2)
                write(text_pen, px, py - POWER_BOX / 2 - 16, power, 8,
                      'gold' if selected else COL_MUTED)

            picked = by_key(sel_char)
            write(text_pen, panel_cx[slot], PANEL_CY - PANEL_H / 2 + 16,
                  '{}  /  {}'.format(picked['name'], sel_power), 11, picked['main'])

        ready_pen.clear()
        write(ready_pen, 0, -282, 'PRESS ENTER TO START', 14, 'gold')
        wn.update()

    # --- static chrome -----------------------------------------------------------
    for slot in slots:
        cx = panel_cx[slot]
        rounded_card(cx, PANEL_CY, PANEL_W, PANEL_H, 16, COL_PANEL_BG, SLOT_COLOR[slot])
        header_strip(cx, PANEL_CY + PANEL_H / 2 - 34, PANEL_W, 34,
                     SLOT_COLOR[slot], slot, '#0b0f14')
        draw_label(cx, grid_top + CARD_H / 2 + 10, 'CHARACTER', 9, COL_MUTED)
        draw_label(cx, power_pos(slot, 0)[1] + POWER_BOX / 2 + 10, 'POWER', 9, COL_MUTED)

    # Power icons are shape turtles, so they are drawn once and float above the pens.
    for slot in slots:
        for i, power in enumerate(POWERS):
            px, py = power_pos(slot, i)
            shape_turtle(POWER_ICON[power], px, py, size=1.3)

    title = 'CHARACTER SELECT - 1 PLAYER' if mode == '1P' else 'CHARACTER SELECT - 2 PLAYERS'
    draw_label(0, 262, title, 18, 'white')
    if mode == '1P':
        draw_label(0, -250, 'Click a card, or  A / D = character   W / S = power', 9, COL_FAINT)
    else:
        draw_label(0, -244, 'P1  A / D = character   W / S = power', 9, COL_FAINT)
        draw_label(0, -262, 'P2  Left / Right = character   Up / Down = power', 9, COL_FAINT)
    draw_label(0, -294, 'ESC = back to menu', 8, COL_FAINT)

    # --- selection -------------------------------------------------------------
    def pick_char(slot, char_key):
        if slot not in chosen or taken_by_other(slot, char_key):
            return                              # A card the other player holds is not available
        chosen[slot]['char'] = char_key
        redraw()

    def pick_power(slot, power):
        if slot not in chosen:
            return
        chosen[slot]['power'] = power
        redraw()

    def step_char(slot, delta):
        if slot not in chosen:
            return
        order = [c['key'] for c in CHARACTERS]
        i = order.index(chosen[slot]['char'])
        for _ in range(len(order)):             # Walk past cards the other player holds
            i = (i + delta) % len(order)
            if not taken_by_other(slot, order[i]):
                chosen[slot]['char'] = order[i]
                redraw()
                return

    def step_power(slot, delta):
        if slot not in chosen:
            return
        i = POWERS.index(chosen[slot]['power'])
        chosen[slot]['power'] = POWERS[(i + delta) % len(POWERS)]
        redraw()

    def on_click(x, y):
        for slot in slots:
            for i, ch in enumerate(CHARACTERS):
                cx, cy = card_pos(slot, i)
                if inside_rect(x, y, cx, cy, CARD_W, CARD_H):
                    pick_char(slot, ch['key'])
                    return
            for i, power in enumerate(POWERS):
                px, py = power_pos(slot, i)
                if inside_rect(x, y, px, py, POWER_BOX + 12, POWER_BOX + 12):
                    pick_power(slot, power)
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
    if mode != '1P':
        wn.onkeypress(lambda: step_char('P2', -1), 'Left')
        wn.onkeypress(lambda: step_char('P2', 1), 'Right')
        wn.onkeypress(lambda: step_power('P2', -1), 'Up')
        wn.onkeypress(lambda: step_power('P2', 1), 'Down')
    else:
        wn.onkeypress(lambda: step_char('P1', -1), 'Left')
        wn.onkeypress(lambda: step_char('P1', 1), 'Right')
        wn.onkeypress(lambda: step_power('P1', -1), 'Up')
        wn.onkeypress(lambda: step_power('P1', 1), 'Down')
    wn.onkeypress(try_start, 'Return')
    wn.onkeypress(back_to_menu, 'Escape')

    redraw()
