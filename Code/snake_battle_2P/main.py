"""
main.py - entry point. Run this file to start the game:  python main.py

Needs, in the same folder:
    scene_manager.py, ui_helpers.py, menu.py, character_select.py,
    snake_1p.py, snake_2p.py, make_sprites.py

Run make_sprites.py once first to generate ./assets/*.gif (optional - falls
back to plain colored squares if the assets folder is missing).
"""

from scene_manager import wn, go_to_scene
from menu import menu_scene

go_to_scene(menu_scene)                         # Start on the main menu
wn.mainloop()                                   # Keep the single window alive for the whole app