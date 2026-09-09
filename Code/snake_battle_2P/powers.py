"""
powers.py - the power registry. Adding a power is a DATA change, not surgery.

Each player picks exactly one power at Character Select and fires it with a single
key (P1: Q, P2: O), so the number of powers is not limited by free keys.

--------------------------------------------------------------------------------
HOW A POWER WORKS

A power is a dict. `effect` is the whole behaviour, expressed as EFFECT KINDS that
the game already knows how to apply:

    speed_mult   float  head speed is multiplied by this        (max of active)
    score_mult   float  fruit is worth this much more           (max of active)
    cloak        bool   body hidden, head swapped to the ghost sprite
    invincible   bool   incoming damage is ignored
    noclip       bool   obstacles and your own body stop hurting

To add a 6th power that reuses these kinds, append an entry and give it an icon -
no game code changes at all. To add a power that needs a NEW kind of effect, add
the key here and read it at the one place in the game that should honour it, via
`flag()` or `effect()`. Nothing else hardcodes a power name.

Balance numbers stay here so `game_config.py` keeps the arena/HP/scoring values and
this file keeps the powers.
"""

POWERS = [
    {
        'key': 'SPEED', 'name': 'SPEED', 'tag': 'SPD', 'hud': 'BOOST',
        'icon': 'speed_icon', 'blurb': 'Move twice as fast',
        'cost': 50, 'duration': 180,
        'effect': {'speed_mult': 2.0},
    },
    {
        'key': 'STEALTH', 'name': 'STEALTH', 'tag': 'STL', 'hud': 'CLOAK',
        'icon': 'stealth_icon', 'blurb': 'Body vanishes, still solid',
        'cost': 50, 'duration': 180,
        'effect': {'cloak': True},
    },
    {
        'key': 'SHIELD', 'name': 'SHIELD', 'tag': 'SHD', 'hud': 'SHIELD',
        'icon': 'shield_icon', 'blurb': 'Take no damage at all',
        'cost': 50, 'duration': 150,
        'effect': {'invincible': True},
    },
    {
        'key': 'PHASE', 'name': 'PHASE', 'tag': 'PHS', 'hud': 'PHASE',
        'icon': 'phase_icon', 'blurb': 'Slip through boxes and your own tail',
        'cost': 50, 'duration': 150,
        'effect': {'noclip': True},
    },
    {
        'key': 'FEAST', 'name': 'FEAST', 'tag': 'FST', 'hud': 'FEAST',
        'icon': 'feast_icon', 'blurb': 'Fruit is worth double',
        'cost': 40, 'duration': 240,
        'effect': {'score_mult': 2.0},
    },
]

DEFAULTS = ('SPEED', 'STEALTH')                 # Pre-selected power for P1 and P2

_BY_KEY = {p['key']: p for p in POWERS}


def by_key(key):
    """Look a power up by key, falling back to the first one for a bad key."""
    return _BY_KEY.get(key, POWERS[0])


def keys():
    return [p['key'] for p in POWERS]


# --------------------------------------------------------------------------
# Runtime state
#
# A snake carries `effects`: {power key -> frames remaining}. That is the only
# per-power state, so a new power needs no new attribute on the snake.
# --------------------------------------------------------------------------

def init(snake):
    """Give a snake (or reset it to) an empty effect set."""
    snake.effects = {}


def tick(snake):
    """Count every active effect down by one frame. Call once per frame."""
    for key in list(snake.effects):
        snake.effects[key] -= 1
        if snake.effects[key] <= 0:
            del snake.effects[key]


def activate(snake):
    """Spend the skill bar and start the snake's chosen power.

    Returns True if it fired, so the caller can play a sound only when it did.
    """
    power = snake.power
    if snake.effects.get(power['key'], 0) > 0:  # Already running
        return False
    if snake.skill < power['cost']:             # Bar not full enough
        return False
    snake.skill -= power['cost']
    snake.effects[power['key']] = power['duration']
    return True


def active_powers(snake):
    """Every power currently running on this snake."""
    return [by_key(k) for k in snake.effects]


def flag(snake, name):
    """True if any active power sets this boolean effect."""
    return any(p['effect'].get(name) for p in active_powers(snake))


def effect(snake, name, default=1.0):
    """The strongest value any active power gives for this numeric effect."""
    values = [p['effect'][name] for p in active_powers(snake) if name in p['effect']]
    return max(values) if values else default


def hud_tags(snake):
    """Short labels for the powers running right now, for the stats panel."""
    return [p['hud'] for p in active_powers(snake)]
