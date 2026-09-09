"""
menu.py - main menu scene. Click a button (or press 1 / 2) to go to
Character Select for that mode.
"""

from scene_manager import wn, go_to_scene
from ui_helpers import draw_label, filled_rect, inside_rect

BTN_W, BTN_H = 300, 80                          # Button size, shared by the drawing and the hit test
BTN_1P_Y = 60                                   # Center y of the 1 PLAYER button
BTN_2P_Y = -60                                  # Center y of the 2 PLAYER button

def menu_scene(epoch):
    from character_select import character_select_scene   # local import avoids a circular import at load time

    wn.title('Snake Game - Main Menu')
    wn.bgcolor('#0b0f14')

    def enter_1p():
        go_to_scene(character_select_scene, '1P')

    def enter_2p():
        go_to_scene(character_select_scene, '2P')

    # Buttons are pen-drawn rectangles, not shape turtles: a shape turtle is raised
    # above everything on every redraw, which would bury the labels below.
    filled_rect(0, BTN_1P_Y, BTN_W, BTN_H, '#1b2430', 'mediumseagreen')
    filled_rect(0, BTN_2P_Y, BTN_W, BTN_H, '#1b2430', 'steelblue')

    draw_label(0, 200, 'SNAKE GAME', 30, 'white')
    draw_label(0, 160, 'Choose a mode', 13, '#8a93a3')
    draw_label(0, BTN_1P_Y + 6, '1 PLAYER', 18, 'mediumseagreen')
    draw_label(0, BTN_1P_Y - 20, 'Classic snake + pick one power', 9, '#8a93a3')
    draw_label(0, BTN_2P_Y + 6, '2 PLAYER BATTLE', 18, 'steelblue')
    draw_label(0, BTN_2P_Y - 20, 'P1: WASD   vs   P2: Arrow Keys', 9, '#8a93a3')
    draw_label(0, -180, 'Click a button, or press 1 / 2', 10, '#4a4a4a')

    # One screen-level click handler hit-tests both buttons. The old code put an
    # onclick on a turtle whose button shape was never applied, so only the few
    # pixels of the default arrow cursor were actually clickable.
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
