"""
main.py - entry point. Run this file to start the game:  python main.py

Needs, in the same folder:
    game_config.py     every tunable number (arena, speeds, HP, scoring, sound)
    characters.py      the playable roster
    powers.py          the power registry
    scene_manager.py   the one turtle window, sprite loader, scene switching
    ui_helpers.py      shared drawing helpers and shape registration
    audio.py           sound effects (optional - silent if no audio files exist)
    menu.py, character_select.py, snake_1p.py, snake_2p.py
    make_sprites.py    sprite generator (only needed to regenerate assets/)

Sprites: assets/*.gif ships with the repo. Run `python make_sprites.py` (needs
Pillow) after adding a character to characters.py. Missing sprites are not fatal -
the game falls back to plain coloured squares.

Sound: nothing is generated. audio.py uses assets/sounds/*.wav if present, else the
repo's sound_effect/*.mp3 when pygame is installed, else stays silent. The line
printed at startup says which.
"""

from scene_manager import wn, go_to_scene
from menu import menu_scene
from audio import sfx

print(sfx.report())                             # One line so audio status is never a mystery

go_to_scene(menu_scene)                         # Start on the main menu
wn.mainloop()                                   # Keep the single window alive for the whole app
