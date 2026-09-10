"""
entity.py - SECTION 2: Game Entities Initialization

The Snake both game modes use, plus the power runtime that drives it.

Power state is ONE dict on the snake - {power key -> frames left} - so a new power
in config.POWERS needs no new attribute here. The game asks about effects by KIND
(powers_flag / powers_effect), never by power name.
"""

import random
import turtle

from config import (character, power, SEG_SPACING, START_LENGTH, SKILL_MAX,
                    FRUIT_VARIANTS)
from engine import load_shape, new_pen

DIRECTIONS = {'up': (0, 1), 'down': (0, -1), 'left': (-1, 0), 'right': (1, 0)}
OPPOSITE = {'up': 'down', 'down': 'up', 'left': 'right', 'right': 'left'}


# ===========================================
# SECTION 2A: POWER RUNTIME
# ===========================================
def powers_init(snake):
    snake.effects = {}


def powers_tick(snake):
    """Count every active effect down one frame."""
    for key in list(snake.effects):
        snake.effects[key] -= 1
        if snake.effects[key] <= 0:
            del snake.effects[key]


def powers_activate(snake):
    """Spend the bar and start the chosen power. True if it actually fired."""
    pw = snake.power
    if snake.effects.get(pw['key'], 0) > 0:     # Already running
        return False
    if snake.skill < pw['cost']:
        return False
    snake.skill -= pw['cost']
    snake.effects[pw['key']] = pw['duration']
    return True


def _active(snake):
    return [power(k) for k in snake.effects]


def powers_flag(snake, name):
    """True if any active power sets this boolean effect."""
    return any(p['effect'].get(name) for p in _active(snake))


def powers_effect(snake, name, default=1.0):
    """The strongest value any active power gives for this numeric effect."""
    values = [p['effect'][name] for p in _active(snake) if name in p['effect']]
    return max(values) if values else default


def powers_hud_tags(snake):
    return [p['hud'] for p in _active(snake)]


# ===========================================
# SECTION 2B: THE SNAKE
# ===========================================
class Snake:
    """One snake: sprites, movement, body layout and power state.

    `slot` is the seat ('P1' / 'P2') and drives which side of the HUD it uses.
    `char_key` is the chosen character and doubles as the sprite filename prefix -
    separate, because either seat can pick any character.

    Head and body sprites are decided SEPARATELY. turtle cannot tint an image shape,
    so a .gif carries its own colour; shipping head gifs but no <key>_body.gif keeps
    the body a coloured square that config.CHARACTERS can still recolour.
    """

    def __init__(self, slot, char_key, start_pos, start_dir, power_key,
                 base_speed, max_hp, head_scale=0.8, body_scale=0.65):
        ch = character(char_key)
        self.slot = slot
        self.name = slot
        self.char_name = ch['name']
        self.key = ch['key']
        self.color_main = ch['main']
        self.color_dim = ch['dim']
        self.start_pos = start_pos
        self.start_dir = start_dir
        self.base_speed = base_speed
        self.max_hp = max_hp
        self.head_scale = head_scale
        self.body_scale = body_scale

        self.power = power(power_key)
        self.skill_tag = self.power['tag']      # Short label for the HUD

        key = self.key
        self.head_sprites = {d: load_shape('{}_head_{}'.format(key, d)) for d in DIRECTIONS}
        self.ghost_sprites = {d: load_shape('{}_head_{}_ghost'.format(key, d)) for d in DIRECTIONS}
        self.body_sprite = load_shape('{}_body'.format(key))
        self.use_head_sprites = all(self.head_sprites.values())
        self.use_body_sprite = self.body_sprite is not None

        self.head = turtle.Turtle()
        self.head.penup()
        if self.use_head_sprites:
            self.head.shape(self.head_sprites[start_dir])
        else:
            self.head.shape('square')
            self.head.color(self.color_main)
            self.head.shapesize(head_scale, head_scale)

        # The stamper's shape is set per stamp group in render(), because body and
        # head can be different kinds (image vs coloured square).
        self.stamper = new_pen()
        self.reset()

    def reset(self):
        self.head.goto(*self.start_pos)
        if not self.use_head_sprites:
            self.head.color(self.color_main)
        self.head.showturtle()
        self.direction = self.start_dir
        self.facing = self.start_dir
        self.length = START_LENGTH
        self.path = [self.start_pos]
        self.hp = self.max_hp
        self.score = 0
        self.skill = 0
        self.speed = self.base_speed
        self.stun = 0
        self.invuln = 0
        self.self_hit_grace = 0                 # Frames a self hit cannot retrigger
        self.bite_grace = 0                     # Frames a BITE cannot punish this snake.
                                                # Set on the winner of a head clash: the
                                                # loser is stunned right there, so the
                                                # winner's head is left sitting on its
                                                # neck and would be charged for biting
                                                # the clash it just won.
        powers_init(self)
        self.stamper.clearstamps()

    # ---------- body layout ----------
    def segments(self):
        """Body positions, nearest the head first.

        Walks the path BACKWARDS accumulating distance rather than counting frames,
        or the body spreads apart while SPEED is active.
        """
        points = []
        target = SEG_SPACING
        travelled = 0.0
        prev = self.path[-1]
        for i in range(len(self.path) - 2, -1, -1):
            cur = self.path[i]
            travelled += abs(cur[0] - prev[0]) + abs(cur[1] - prev[1])
            prev = cur
            while travelled >= target and len(points) < self.length:
                points.append(cur)
                target += SEG_SPACING
            if len(points) >= self.length:
                break
        return points

    # ---------- input ----------
    def turn(self, new_dir):
        if self.direction != OPPOSITE[new_dir]:
            self.direction = new_dir
            self.facing = new_dir

    def use_power(self):
        """One key per player fires whichever power was picked."""
        return powers_activate(self)

    # ---------- per frame ----------
    def tick_timers(self):
        if self.stun > 0: self.stun -= 1
        if self.invuln > 0: self.invuln -= 1
        if self.self_hit_grace > 0: self.self_hit_grace -= 1
        if self.bite_grace > 0: self.bite_grace -= 1
        powers_tick(self)
        self.speed = self.base_speed * powers_effect(self, 'speed_mult', 1.0)

    def next_position(self):
        """Where the head would go this frame, without committing to it."""
        if self.stun > 0 or self.direction == 'stop':
            return None
        dx, dy = DIRECTIONS[self.direction]
        return self.head.xcor() + dx * self.speed, self.head.ycor() + dy * self.speed

    def commit(self, x, y):
        """Accept a move: place the head and trim the path to what segments() needs."""
        self.head.goto(x, y)
        self.path.append((round(x), round(y)))
        keep = int((self.length + 2) * SEG_SPACING / self.base_speed) + 8
        if len(self.path) > keep:
            del self.path[:-keep]

    def gain_fruit(self, score, grow, skill_gain):
        self.score += score
        self.length += grow
        self.skill = min(SKILL_MAX, self.skill + skill_gain)

    # ---------- drawing ----------
    def render(self):
        """Body first, head stamped LAST - canvas items keep creation order."""
        self.stamper.clearstamps()
        cloaked = powers_flag(self, 'cloak')
        blinking = self.invuln > 0 and (self.invuln // 4) % 2 == 0

        if not cloaked:                         # CLOAK hides the body entirely
            if self.use_body_sprite:
                self.stamper.shape(self.body_sprite)
            else:
                self.stamper.shape('square')
                self.stamper.color(self.color_main)     # Body colour from config
                self.stamper.shapesize(self.body_scale, self.body_scale)
            for pos in self.segments():
                self.stamper.goto(pos)
                self.stamper.stamp()

        if self.use_head_sprites:
            self.head.hideturtle()              # The sprite head is stamped, not shown
            if not blinking:                    # Blink = skip a frame after a hit
                use_ghost = cloaked and all(self.ghost_sprites.values())
                table = self.ghost_sprites if use_ghost else self.head_sprites
                self.stamper.shape(table[self.facing])
                self.stamper.goto(self.head.pos())
                self.stamper.stamp()
        else:
            self.head.showturtle()
            self.head.shape('square')
            self.head.shapesize(self.head_scale, self.head_scale)
            if cloaked:
                self.head.color(self.color_dim)
            elif blinking:
                self.head.color('white')
            else:
                self.head.color(self.color_main)

    def hide(self):
        self.head.hideturtle()
        self.stamper.clearstamps()


# ===========================================
# SECTION 2C: SHARED ENTITY BUILDERS
# ===========================================
_fruit_shapes = None                            # Resolved once, on the first fruit


def fruit_shapes():
    """Every fruit skin that actually loaded, best available first.

    Three tiers, so the game looks its best with the imported art and still runs
    with none of it: the config.FRUIT_VARIANTS drawings, then the single generated
    assets/fruit.gif, then nothing at all (make_fruit draws a red circle).
    """
    global _fruit_shapes
    if _fruit_shapes is None:
        _fruit_shapes = [s for s in (load_shape(n) for n in FRUIT_VARIANTS) if s]
        if not _fruit_shapes:
            plain = load_shape('fruit')
            _fruit_shapes = [plain] if plain else []
    return _fruit_shapes


def make_fruit():
    """One fruit turtle: a random fruit skin if any loaded, else a red circle."""
    shapes = fruit_shapes()
    f = turtle.Turtle()
    f.penup()
    if shapes:
        f.shape(random.choice(shapes))
    else:
        f.shape('circle')
        f.color('red')
        f.shapesize(0.7, 0.7)
    return f


def reroll_fruit(f):
    """Give a fruit a new random skin when it respawns. Cosmetic only.

    Called right after the fruit is moved. A no-op with one skin or none, so both
    game modes can call it unconditionally.
    """
    shapes = fruit_shapes()
    if len(shapes) > 1:
        f.shape(random.choice(shapes))
