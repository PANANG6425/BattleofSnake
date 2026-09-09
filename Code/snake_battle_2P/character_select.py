"""
character_select.py - pick SPEED or STEALTH for each player before the match
starts. 1P mode shows one card (P1 only); 2P mode shows both.
"""

import turtle
from scene_manager import wn, go_to_scene
from ui_helpers import (rounded_card, header_strip, draw_label, draw_mini_snake,
                        shape_turtle, inside_rect)

HOTSPOT = 56                                    # Clickable square around each power icon

def character_select_scene(epoch, mode):
    from menu import menu_scene                 # local imports avoid circular imports at load time
    from snake_1p import game_1p_scene
    from snake_2p import game_2p_scene

    wn.title('Character Select')
    wn.bgcolor('#0b0f14')

    players = ['P1'] if mode == '1P' else ['P1', 'P2']
    selection = {p: None for p in players}
    box_turtles = {}
    hotspots = []                               # (player, power, cx, cy) for click hit-testing

    def make_icon_box(player, power, cx, cy, size=44):
        border = turtle.Turtle()
        border.hideturtle()
        border.penup()
        box_turtles[(player, power)] = (border, cx, cy, size)
        redraw_box(player, power, selected=False)

    def redraw_box(player, power, selected):
        border, cx, cy, size = box_turtles[(player, power)]
        border.clear()
        border.color('gold' if selected else '#3a3f47')
        border.pensize(4 if selected else 2)
        border.goto(cx - size / 2, cy - size / 2)
        border.setheading(0)
        border.pendown()
        for _ in range(4):
            border.forward(size)
            border.left(90)
        border.penup()

    ready_pen = turtle.Turtle()
    ready_pen.hideturtle()
    ready_pen.penup()

    def update_ready():
        ready_pen.clear()
        if all(selection[p] for p in players):
            ready_pen.color('gold')
            ready_pen.goto(0, -250)
            ready_pen.write('PRESS ENTER TO START', align='center', font=('Courier', 15, 'bold'))

    def select_power(player, power):
        selection[player] = power
        for pw in ('SPEED', 'STEALTH'):
            redraw_box(player, pw, selected=(pw == power))
        update_ready()
        wn.update()

    CARD_W, CARD_H = 220, 340
    CARD_Y = 20
    positions = {'P1': 0} if mode == '1P' else {'P1': -190, 'P2': 190}
    card_colors = {'P1': 'mediumseagreen', 'P2': 'steelblue'}
    head_shapes = {'P1': 'p1_head', 'P2': 'p2_head'}
    body_colors = {'P1': ['red', 'white', 'blue', 'red'], 'P2': ['navy', 'red', 'navy', 'navy']}

    def build_card(player):
        cx = positions[player]
        color_ = card_colors[player]
        rounded_card(cx, CARD_Y, CARD_W, CARD_H, 18, '#1b2430', color_)
        header_strip(cx, CARD_Y + CARD_H / 2 - 36, CARD_W, 36, color_, player, '#0b0f14')
        draw_mini_snake(cx - 10, CARD_Y + 90, head_shapes[player], body_colors[player])
        draw_label(cx, CARD_Y - 30, 'Choose your power', 11, '#8a93a3')

        # Icons are drawn, but the CLICK is handled by the screen-level hit test below.
        # turtle's onclick() binds to turtle.turtle._item, which is a LIST for a compound
        # shape: tag_bind then silently matches nothing for any shape with more than one
        # component. stealth_icon has three, so STEALTH could never be selected at all.
        make_icon_box(player, 'SPEED', cx - 45, CARD_Y - 90)
        shape_turtle('speed_icon', cx - 45, CARD_Y - 90, size=1.4)
        draw_label(cx - 45, CARD_Y - 118, 'SPEED', 9, '#c7ccd4')
        hotspots.append((player, 'SPEED', cx - 45, CARD_Y - 90))

        make_icon_box(player, 'STEALTH', cx + 45, CARD_Y - 90)
        shape_turtle('stealth_icon', cx + 45, CARD_Y - 90, size=1.4)
        draw_label(cx + 45, CARD_Y - 118, 'STEALTH', 9, '#c7ccd4')
        hotspots.append((player, 'STEALTH', cx + 45, CARD_Y - 90))

    for p in players:
        build_card(p)

    title = 'CHARACTER SELECT - 1 PLAYER' if mode == '1P' else 'CHARACTER SELECT - 2 PLAYERS'
    draw_label(0, 250, title, 20, 'white')
    draw_label(0, -280, 'ESC = back to menu', 9, '#4a4a4a')

    def try_start():
        if not all(selection[p] for p in players):
            return
        if mode == '1P':
            go_to_scene(game_1p_scene, selection['P1'])
        else:
            go_to_scene(game_2p_scene, selection['P1'], selection['P2'])

    def back_to_menu():
        go_to_scene(menu_scene)

    def on_click(x, y):
        for player, power, cx, cy in hotspots:
            if inside_rect(x, y, cx, cy, HOTSPOT, HOTSPOT):
                select_power(player, power)
                return

    wn.onscreenclick(on_click)

    wn.listen()
    wn.onkeypress(try_start, 'Return')
    wn.onkeypress(back_to_menu, 'Escape')
    wn.update()