"""
solo.py - 1 Player mode.  Arrows to move, SPACE for your power.

Classic snake: no HP, no combat, no obstacles. The outer wall is fatal, and so is
your own tail unless CLOAK, PHASE or SHIELD is running.

Follows the baseline kit layout:
    Section 2  Game Entities Initialization
    Section 3  Parameters & Physics
    Section 4  Input Handling
    Section 5  Main Game Loop
Section 1 (Screen Setup) is owned by engine.py - turtle allows one Screen per process.
"""

import random

from config import (character, ARENA_1P, SPEED_1P, WALL_MARGIN, GROW_PER_FRUIT,
                    FRUIT_SCORE, SKILL_MAX, SKILL_GAIN_1P, FRAME_MS, BG_COLOR,
                    WALL_COLOR, TEXT_BRIGHT, TEXT_MUTED, TEXT_FAINT, TEXT_DIM,
                    HIGHLIGHT)
from engine import wn, go_to_scene, new_pen, STATE, FONT, draw_skill_bar
from audio import sfx
from entity import Snake, make_fruit, powers_flag, powers_effect, powers_hud_tags

# ===========================================
# SECTION 3: PARAMETERS & PHYSICS
# ===========================================
ARENA_L, ARENA_R, ARENA_B, ARENA_T = ARENA_1P
BORDER_PAD = 5
# Keep the 20x20 head sprite from sinking into the border (see battle.py)
WALL_L, WALL_R = ARENA_L + WALL_MARGIN, ARENA_R - WALL_MARGIN
WALL_B, WALL_T = ARENA_B + WALL_MARGIN, ARENA_T - WALL_MARGIN
FRUIT_REACH = 18
SPAWN_CLEAR = 60
SELF_HIT_RADIUS = 10
NO_HP = 1                                       # 1P has no hearts; Snake still needs a value

# The skill bar must sit ABOVE the arena. It used to be at y 226-238 while the
# arena reached y=260, so the snake drove straight through it and the bar repainted
# over the snake every frame. config.ARENA_1P now tops out at 235, matching how the
# 2P HUD lives above ARENA_2P.
BAR_LEFT, BAR_BOTTOM = -70, 248
BAR_W, BAR_H = 140, 12
BODY_CLEAR = 24                                 # Keep fruit off the snake's own body
HINT = 'Arrows = Move   SPACE = {}   R = Retry   X = Sound   M = Menu'


def game_1p_scene(epoch, char_key, power_key):
    from screens import menu_scene             # local import avoids a circular import

    ch = character(char_key)
    wn.title('Snake - 1 Player ({} / {})'.format(ch['name'], power_key))
    wn.bgcolor(BG_COLOR)

    # ===========================================
    # SECTION 2: GAME ENTITIES INITIALIZATION
    # ===========================================
    border = new_pen(WALL_COLOR)
    border.pensize(6)
    border.goto(ARENA_L - BORDER_PAD, ARENA_T + BORDER_PAD)
    border.pendown()
    for _ in range(2):
        border.forward(ARENA_R - ARENA_L + BORDER_PAD * 2)
        border.right(90)
        border.forward(ARENA_T - ARENA_B + BORDER_PAD * 2)
        border.right(90)
    border.penup()

    # The same Snake the battle mode uses, so sprites, body layout and powers behave
    # identically. 1P just starts stopped and ignores hp.
    me = Snake('P1', char_key, (0, 0), 'right', power_key, SPEED_1P, NO_HP)
    me.direction = 'stop'

    fruit = make_fruit()

    def random_free_spot():
        """Somewhere clear of the head AND the body.

        Checking only the head let fruit land on a segment further back, where
        collecting it means driving into your own tail - an unavoidable game over.
        """
        for _ in range(200):
            x = random.randint(ARENA_L + 30, ARENA_R - 30)
            y = random.randint(ARENA_B + 30, ARENA_T - 30)
            if me.head.distance(x, y) <= SPAWN_CLEAR:
                continue
            if any((pos[0] - x) ** 2 + (pos[1] - y) ** 2 < BODY_CLEAR ** 2
                   for pos in me.segments()):
                continue
            return x, y
        return 0, 0

    fruit.goto(random_free_spot())

    hud = new_pen(TEXT_BRIGHT)
    bar_pen = new_pen()
    result_pen = new_pen()
    alive = {'value': True}

    # ===========================================
    # SECTION 4: INPUT HANDLING
    # ===========================================
    def use_power():
        if me.use_power():
            sfx.play('power')
            draw_hud()
            wn.update()

    def retry():
        if alive['value']:                      # R only works after game over
            return
        go_to_scene(game_1p_scene, char_key, power_key)

    def to_menu():
        go_to_scene(menu_scene)

    wn.listen()
    for key, direction in (('Up', 'up'), ('Down', 'down'),
                           ('Left', 'left'), ('Right', 'right')):
        wn.onkeypress(lambda d=direction: me.turn(d), key)
    wn.onkeypress(use_power, 'space')
    wn.onkeypress(sfx.toggle, 'x')
    wn.onkeypress(retry, 'r')
    wn.onkeypress(to_menu, 'm')

    # ===========================================
    # SECTION 5A: HUD & GAME OVER
    # ===========================================
    def draw_hud():
        hud.clear()
        bar_pen.clear()
        hud.color(TEXT_BRIGHT)
        hud.goto(ARENA_L, 268)
        hud.write('SCORE: {}'.format(me.score), font=(FONT, 14, 'bold'))
        draw_skill_bar(bar_pen, BAR_LEFT, BAR_BOTTOM, BAR_W, BAR_H,
                       me.skill / SKILL_MAX, ch['main'])
        hud.color(HIGHLIGHT)
        hud.goto(0, 268)
        hud.write('  '.join(powers_hud_tags(me)), align='center', font=(FONT, 12, 'bold'))
        hud.color(TEXT_MUTED)
        hud.goto(ARENA_R, 268)
        hud.write('{} [{}]'.format(ch['name'], me.power['name']),
                  align='right', font=(FONT, 12, 'bold'))
        hud.color(TEXT_FAINT)
        hud.goto(0, -272)
        hud.write(HINT.format(me.power['name']), align='center', font=(FONT, 10, 'normal'))

    def game_over():
        alive['value'] = False
        me.hide()                               # Or the snake sits under the text
        fruit.hideturtle()
        result_pen.clear()
        result_pen.color(TEXT_BRIGHT)
        result_pen.goto(0, 30)
        result_pen.write('GAME OVER', align='center', font=(FONT, 26, 'bold'))
        result_pen.goto(0, -10)
        result_pen.write('Score: {}'.format(me.score), align='center', font=(FONT, 18, 'bold'))
        result_pen.color(TEXT_DIM)
        result_pen.goto(0, -50)
        result_pen.write('R = Retry     M = Menu', align='center', font=(FONT, 12, 'normal'))
        sfx.play('lose')
        wn.update()

    def hit_own_tail():
        """PHASE and SHIELD let you run over your own tail; CLOAK does not.

        CLOAK used to be exempt here but not in battle.py, which made STEALTH a
        strictly better PHASE in 1P - same cost, longer duration, plus it hides the
        body. `cloak` is not a collision effect kind (see config.py Section 3G), and
        its own blurb says "still solid", so only the declared kinds count.
        """
        if powers_flag(me, 'noclip') or powers_flag(me, 'invincible'):
            return False
        return any(me.head.distance(pos) < SELF_HIT_RADIUS for pos in me.segments()[2:])

    # ===========================================
    # SECTION 5: MAIN GAME LOOP
    # ===========================================
    sfx.play('start')

    def game_loop():
        if STATE['epoch'] != epoch or not alive['value']:
            return                              # A newer scene took over, or you died

        me.tick_timers()                        # 1. advance timers and speed
        nxt = me.next_position()
        if nxt is not None:
            x, y = nxt
            if x > WALL_R or x < WALL_L or y > WALL_T or y < WALL_B:
                game_over()                     # 2. the wall is fatal here
                return
            me.commit(x, y)

            if hit_own_tail():                  # 3. own tail is fatal too
                game_over()
                return

            if me.head.distance(fruit) < FRUIT_REACH:   # 4. pickup
                gain = int(FRUIT_SCORE * powers_effect(me, 'score_mult', 1.0))
                me.gain_fruit(gain, GROW_PER_FRUIT, SKILL_GAIN_1P)
                fruit.goto(random_free_spot())
                sfx.play('eat')

        me.render()                             # 5. draw
        draw_hud()
        wn.update()
        wn.ontimer(game_loop, FRAME_MS)

    game_loop()
