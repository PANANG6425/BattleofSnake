"""
main.py - entry point.  Run this file:  python main.py

Layout (baseline kit sections):
    config.py    Section 3  every tunable number + character / power registries
    engine.py    Section 1  the one turtle Screen, sprites, scenes, drawing, sound
    entity.py    Section 2  the Snake both modes use + the power runtime
    screens.py              Main Menu and Character Select
    solo.py                 1 Player   - Sections 2, 3, 4, 5
    battle.py               2 Player   - Sections 2, 3, 4, 5
    make_sprites.py         sprite generator (a tool, not runtime; needs Pillow)

turtle + standard library only. Pillow is needed only to regenerate assets/, and no
audio is generated at all - see MANUAL.md section 6 to switch sound on.
"""

from engine import wn, go_to_scene
from audio import sfx
from screens import menu_scene

print(sfx.report())                             # One line, so silence is never a mystery
if sfx.backend == 'silent' or sfx._bad_wavs:    # Something is off - say exactly what
    print(sfx.diagnose())

go_to_scene(menu_scene)
wn.mainloop()
