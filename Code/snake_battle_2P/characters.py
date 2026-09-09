"""
characters.py - the playable roster, in one place.

All four characters play IDENTICALLY. They differ only in colour, so nothing here
affects balance: speed, HP, skills and hitboxes all live in the game scenes.

`key` is also the sprite filename prefix, so character `p3` loads
`assets/p3_head_up.gif`, `assets/p3_body.gif` and so on. `make_sprites.py` reads
`palette` from this same list, which keeps the artwork and the in-game fallback
colours from drifting apart.

`palette` is (main, dark outline, light highlight, ghost main, ghost outline) and is
only used to GENERATE sprites. `main` / `dim` are what the game draws with when a
sprite file is missing - `dim` is the cloaked (Invisibility) colour.

To add a character: append an entry, run `python make_sprites.py`, done. The
Character Select screen lays itself out from whatever length this list is.
"""

CHARACTERS = [
    {
        'key': 'p1', 'name': 'AQUA', 'tag': 'cyan',
        'main': '#22e0e0', 'dim': '#0d3a3a',
        'palette': ('#22e0e0', '#0b6a6a', '#b6ffff', '#0e3d3d', '#082424'),
    },
    {
        'key': 'p2', 'name': 'EMBER', 'tag': 'orange',
        'main': '#ffa22a', 'dim': '#3a260d',
        'palette': ('#ffa22a', '#8a4a00', '#ffe0a8', '#4a2f0c', '#241705'),
    },
    {
        'key': 'p3', 'name': 'VENOM', 'tag': 'green',
        'main': '#5ce65c', 'dim': '#123d12',
        'palette': ('#5ce65c', '#186b18', '#c9ffc9', '#123d12', '#0a240a'),
    },
    {
        'key': 'p4', 'name': 'ROYAL', 'tag': 'violet',
        'main': '#c86ef0', 'dim': '#341044',
        'palette': ('#c86ef0', '#5e1f7a', '#eecbff', '#341044', '#1d0926'),
    },
]

DEFAULTS = ('p1', 'p2')                         # Pre-selected character for P1 and P2

_BY_KEY = {c['key']: c for c in CHARACTERS}


def by_key(key):
    """Look a character up by key, falling back to the first one for a bad key."""
    return _BY_KEY.get(key, CHARACTERS[0])


def keys():
    return [c['key'] for c in CHARACTERS]
