"""
menu.py - main menu scene. Click a button (or press 1 / 2) to go to
Character Select for that mode.
"""

import turtle
from scene_manager import wn, go_to_scene
from ui_helpers import draw_label, register_rect_shape

def menu_scene(epoch):
    from character_select import character_select_scene   # local import avoids a circular import at load time

    wn.title('Snake Game - Main Menu')
    wn.bgcolor('#0b0f14')

    draw_label(0, 200, 'SNAKE GAME', 30, 'white')
    draw_label(0, 160, 'Choose a mode', 13, '#8a93a3')

    register_rect_shape('btn_1p', 300, 80, '#1b2430', 'mediumseagreen')
    register_rect_shape('btn_2p', 300, 80, '#1b2430', 'steelblue')

    def enter_1p():
        go_to_scene(character_select_scene, '1P')

    def enter_2p():
        go_to_scene(character_select_scene, '2P')

    b1 = turtle.Turtle()
    b1.penup()
    b1.goto(0, 60)
    b1.onclick(lambda x, y: enter_1p())
    draw_label(0, 66, '1 PLAYER', 18, 'mediumseagreen')
    draw_label(0, 40, 'Classic snake + pick one power', 9, '#8a93a3')


    b2 = turtle.Turtle()
    b2.goto(0, -60)
    b2.onclick(lambda x, y: enter_2p())
    draw_label(0, -54, '2 PLAYER BATTLE', 18, 'steelblue')
    draw_label(0, -80, 'P1: WASD   vs   P2: Arrow Keys', 9, '#8a93a3')

    draw_label(0, -180, 'Click a button, or press 1 / 2', 10, '#4a4a4a')

    wn.listen()
    wn.onkeypress(enter_1p, '1')
    wn.onkeypress(enter_2p, '2')
    wn.update()