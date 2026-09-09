"""
screens.py - every screen that is not gameplay: Main Menu, Character Select, and the
two 2P result screens (end of round, end of match).

The menu and Character Select are Section 2 (entities) + Section 4 (input) with no
game loop - they draw once and wait for a click or a key. The result screens are
plain drawing functions that battle.py calls over its own arena.

Clicks are hit-tested against rectangles through wn.onscreenclick rather than bound
to turtles, for two reasons that are turtle limitations, not preference:
  * a shape turtle is raised above pen drawings and text every frame, so a button
    drawn as a shape would bury its own label
  * onclick() silently binds nothing on a compound shape with 2+ components
"""

from config import (CHARACTERS, CHAR_DEFAULTS, POWERS, POWER_DEFAULTS,
                    character, power, BG_MENU, PANEL_BG, CARD_BG, CARD_EDGE,
                    ARROW_COLOR, BUTTON_FILL, SLOT_COLOR, TEXT_BRIGHT, TEXT_MUTED,
                    TEXT_FAINT, TEXT_DIM, HIGHLIGHT, ROUNDS_TO_WIN)
from engine import (wn, go_to_scene, new_pen, draw_label, filled_rect, rounded_card,
                    header_strip, inside_rect, shape_turtle, stroke_box, fill_box,
                    write_at, make_head_shape)
from audio import sfx

# ===========================================
# SECTION 3: LAYOUT PARAMETERS
# ===========================================
BTN_W, BTN_H = 300, 80                          # Main menu buttons
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

# Colours all come from config.py Section 3A2, so the theme lives in one place.

# One scaled head shape per character, tinted with that character's own palette. A
# .gif sprite cannot be used for this: turtle cannot scale an image shape, so the
# 20x20 head would stay 20x20. Compound shapes do scale.
HEAD_SHAPE = {}
for _ch in CHARACTERS:
    _name = 'char_head_' + _ch['key']
    wn.register_shape(_name, make_head_shape(_ch['palette'][0], _ch['palette'][1],
                                             _ch['palette'][2]))
    HEAD_SHAPE[_ch['key']] = _name


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
    from solo import game_1p_scene             # local imports avoid circular imports
    from battle import game_2p_scene

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
        portrait[slot] = shape_turtle(HEAD_SHAPE[CHARACTERS[0]['key']],
                                      panel_cx[slot] + 22, CARD_CY + 22, size=3.0)
        for i, pw in enumerate(POWERS):
            shape_turtle(pw['icon'], *power_pos(slot, i), size=1.1)

    title = 'CHARACTER SELECT - 1 PLAYER' if mode == '1P' else 'CHARACTER SELECT - 2 PLAYERS'
    draw_label(0, 272, title, 18, TEXT_BRIGHT)
    draw_label(0, -212, 'PRESS ENTER TO START', 14, HIGHLIGHT)
    if mode == '1P':
        draw_label(0, -244, 'Click the arrows, or  A / D = character   W / S = power',
                   9, TEXT_FAINT)
    else:
        draw_label(0, -240, 'P1  A / D = character   W / S = power', 9, TEXT_FAINT)
        draw_label(0, -258, 'P2  Left / Right = character   Up / Down = power', 9, TEXT_FAINT)
    draw_label(0, -284, 'ESC = back to menu', 8, TEXT_FAINT)

    def redraw():
        """Repaint only what a pick changes: portrait, name, dots, power highlight."""
        art_pen.clear()
        text_pen.clear()
        for slot in slots:
            cx = panel_cx[slot]
            ch = character(chosen[slot]['char'])
            pw = power(chosen[slot]['power'])

            for i, (dx, dy) in enumerate(((-46, -14), (-72, -30), (-92, -50))):
                fill_box(art_pen, cx + 22 + dx, CARD_CY + 22 + dy,
                         20 - i * 2, 20 - i * 2, ch['main'])
            portrait[slot].shape(HEAD_SHAPE[ch['key']])
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

    def on_click(x, y):
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
#     MVP = score x HP left,  added up over every round
#
# so surviving a round counts as much as scoring in it, and a round you were knocked
# out of is worth nothing no matter how many points you banked (score x 0 = 0).
# Round wins still decide the match; MVP only breaks a tie on rounds.


def scoreline(round_wins):
    return 'P1  {} - {}  P2'.format(round_wins['P1'], round_wins['P2'])


def mvp_total(rounds, slot):
    return sum(r[slot] * r['hp' + slot] for r in rounds)


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
    return '{} x {} = {}'.format(r[slot], r['hp' + slot], r[slot] * r['hp' + slot])


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

    write_at(pen, 0, 0, 'score x hp left = MVP', 12, TEXT_MUTED)
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
    write_at(pen, col_r, y, 'ROUND', 13, TEXT_MUTED, 'left')
    write_at(pen, col_1, y, 'P1   score x hp = MVP', 13, p1.color_main, 'right')
    write_at(pen, col_2, y, 'P2   score x hp = MVP', 13, p2.color_main, 'right')
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
        write_at(pen, 0, y, 'MVP = score x hp left, summed - it only breaks a tie on '
                 'rounds', 11, TEXT_FAINT)
    write_at(pen, 0, y - 30, 'Press R for a NEW MATCH     |     M for Menu', 12, TEXT_DIM)
