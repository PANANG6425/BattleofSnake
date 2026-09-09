"""
battle.py - 2 Player Battle mode.  P1: WASD + Q      P2: Arrows + O

Follows the baseline kit layout:
    Section 2  Game Entities Initialization
    Section 3  Parameters & Physics
    Section 4  Input Handling
    Section 5  Main Game Loop
Section 1 (Screen Setup) is owned by engine.py - turtle allows one Screen per process.
"""

import random
import turtle

from config import (ARENA_2P, SPEED_2P, WALL_MARGIN, GROW_PER_FRUIT, FRUIT_SCORE,
                    SKILL_MAX, SKILL_GAIN_2P, MAX_HP, TARGET_SCORE, ROUNDS_TO_WIN,
                    DEATH_SCORE_PENALTY, SCORE_TRANSFER, SELF_HIT_DAMAGE, STUN_FRAMES,
                    SELF_HIT_GRACE_EXTRA, INVULN_FRAMES, HIT_RADIUS, OBSTACLE_COUNT,
                    OBSTACLE_SIZE, OBSTACLE_SPOTS, FRUIT_COUNT_2P, FRUIT_MIN_GAP,
                    FRAME_MS, BG_COLOR, WALL_COLOR, OBSTACLE_FILL, OBSTACLE_EDGE,
                    TEXT_BRIGHT, TEXT_TAG, TEXT_DIM, TEXT_FAINT, HIGHLIGHT)
from engine import (wn, go_to_scene, load_shape, new_pen, STATE, FONT,
                    draw_skill_bar, fill_box)
from audio import sfx
from entity import Snake, make_fruit, powers_flag, powers_effect, powers_hud_tags

# ===========================================
# SECTION 3: PARAMETERS & PHYSICS
# ===========================================
ARENA_L, ARENA_R, ARENA_B, ARENA_T = ARENA_2P
BORDER_PAD = 5                                  # Border is drawn this far outside the arena
# The head is a 20x20 sprite drawn centred, so allowing the CENTRE to reach the arena
# edge let half the sprite sink into the wall. Pull the limits in by WALL_MARGIN.
WALL_L, WALL_R = ARENA_L + WALL_MARGIN, ARENA_R - WALL_MARGIN
WALL_B, WALL_T = ARENA_B + WALL_MARGIN, ARENA_T - WALL_MARGIN
OBSTACLE_PAD = 6                                # Collision margin around a box
FRUIT_REACH = 18                                # How close counts as eating
SPAWN_CLEAR = 60                                # Keep fruit away from a head
OBSTACLE_CLEAR = 20                             # Keep fruit out of a box

HEART_Y = 250
HEART_STEP = 22
BAR_W, BAR_H = 132, 12
BAR_Y = 224
PANEL = {
    'P1': {'x': -356, 'dir': 1, 'align': 'left',  'bar_x': -358},
    'P2': {'x': 356,  'dir': -1, 'align': 'right', 'bar_x': 358 - BAR_W},
}
SPAWN = {'P1': ((-250, -35), 'right'), 'P2': ((250, -35), 'left')}
HINT = 'P1: WASD Q=Power  |  P2: Arrows O=Power  |  X = Sound  M = Menu'


def game_2p_scene(epoch, p1_char, p1_power, p2_char, p2_power, wins=None):
    """One round. `wins` carries the round tally between rounds ({'P1': n, 'P2': n})."""
    from screens import menu_scene             # local import avoids a circular import

    wn.title('Snake Battle - Local Multiplayer (P1: WASD | P2: Arrow Keys)')
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

    obstacle_pen = new_pen()
    obstacle_pen.color(OBSTACLE_EDGE, OBSTACLE_FILL)
    obstacle_pen.pensize(3)
    obstacles = []

    def build_obstacles():
        obstacle_pen.clear()
        obstacles.clear()
        for cx, cy in OBSTACLE_SPOTS[:OBSTACLE_COUNT]:
            fill_box(obstacle_pen, cx, cy, OBSTACLE_SIZE, OBSTACLE_SIZE,
                     OBSTACLE_FILL, OBSTACLE_EDGE)
            half = OBSTACLE_SIZE / 2
            obstacles.append((cx - half, cy - half, cx + half, cy + half))

    def inside_obstacle(x, y, pad=0):
        for left, bottom, right, top in obstacles:
            if left - pad <= x <= right + pad and bottom - pad <= y <= top + pad:
                return True
        return False

    build_obstacles()

    p1 = Snake('P1', p1_char, *SPAWN['P1'], p1_power, SPEED_2P, MAX_HP)
    p2 = Snake('P2', p2_char, *SPAWN['P2'], p2_power, SPEED_2P, MAX_HP)
    players = [p1, p2]

    fruits = []

    def random_free_spot(skip=None):
        for _ in range(200):
            x = random.randint(ARENA_L + 30, ARENA_R - 30)
            y = random.randint(ARENA_B + 30, ARENA_T - 30)
            if inside_obstacle(x, y, pad=OBSTACLE_CLEAR):
                continue
            if any(pl.head.distance(x, y) < SPAWN_CLEAR for pl in players):
                continue
            # Keep fruits apart, or two land together and one touch scores both.
            if any(f is not skip and f.distance(x, y) < FRUIT_MIN_GAP for f in fruits):
                continue
            return x, y
        return 0, 0

    for _ in range(FRUIT_COUNT_2P):
        f = make_fruit()
        f.goto(random_free_spot())
        fruits.append(f)

    hud = new_pen(TEXT_BRIGHT)
    bar_pen = new_pen()
    result_pen = new_pen()
    game_active = {'value': True}
    round_wins = dict(wins) if wins else {'P1': 0, 'P2': 0}
    match_over = {'value': False}               # True once someone reaches ROUNDS_TO_WIN

    HEART_FULL = load_shape('heart_full')
    HEART_EMPTY = load_shape('heart_empty')
    USE_HEART_ICONS = HEART_FULL is not None and HEART_EMPTY is not None

    heart_icons = {}
    if USE_HEART_ICONS:
        for pl in players:
            geo = PANEL[pl.slot]
            pool = []
            for i in range(MAX_HP):
                icon = turtle.Turtle()
                icon.penup()
                icon.shape(HEART_FULL)
                icon.goto(geo['x'] + geo['dir'] * i * HEART_STEP, HEART_Y)
                pool.append(icon)
            heart_icons[pl.slot] = pool

    # ===========================================
    # SECTION 4: INPUT HANDLING
    # ===========================================
    def to_menu():
        go_to_scene(menu_scene)

    def do_restart():
        if game_active['value']:                # R only works on the result screen
            return
        # Carry the tally into the next round, unless the match is already decided -
        # then R starts a fresh match at 0 - 0.
        carry = None if match_over['value'] else round_wins
        go_to_scene(game_2p_scene, p1_char, p1_power, p2_char, p2_power, carry)

    def fire(snake):
        def go():
            if snake.use_power():
                sfx.play('power')
        return go

    wn.listen()
    for key, direction in (('w', 'up'), ('s', 'down'), ('a', 'left'), ('d', 'right')):
        wn.onkeypress(lambda d=direction: p1.turn(d), key)
    for key, direction in (('Up', 'up'), ('Down', 'down'),
                           ('Left', 'left'), ('Right', 'right')):
        wn.onkeypress(lambda d=direction: p2.turn(d), key)
    # One power key per player, whatever power they picked. E and P are kept as
    # aliases for the old two-key layout.
    for key in ('q', 'e'):
        wn.onkeypress(fire(p1), key)
    for key in ('o', 'p'):
        wn.onkeypress(fire(p2), key)
    wn.onkeypress(sfx.toggle, 'x')
    wn.onkeypress(to_menu, 'm')
    wn.onkeypress(do_restart, 'r')

    # ===========================================
    # SECTION 5A: PHYSICS & COLLISION RULES
    # ===========================================
    def step(snake):
        """Move one snake. Walls and boxes stun; they never cost HP.

        Returns True only if the head actually moved, because a self hit can only
        NEWLY happen after a move - see game_loop.
        """
        nxt = snake.next_position()
        if nxt is None:                         # Stunned or stopped
            return False
        x, y = nxt
        bumped = False
        if x > WALL_R or x < WALL_L or y > WALL_T or y < WALL_B:
            bumped = True                       # The outer wall always stops you
        elif inside_obstacle(x, y, pad=OBSTACLE_PAD) and not powers_flag(snake, 'noclip'):
            bumped = True                       # PHASE slips through the boxes
        if bumped:
            snake.stun = STUN_FRAMES
            snake.direction = 'stop'
            sfx.play('bump')
            return False
        snake.commit(x, y)
        return True

    def punish(loser, winner=None):
        """One knockdown: the loser drops an HP and score, some of it to the winner.

        This is the whole economy of the game. Biting is PUNISHED, so the snake in
        front wants to dangle its body in front of the other one's mouth, and the
        snake behind has to resist taking the bait.
        """
        if loser.invuln > 0:
            return False
        if powers_flag(loser, 'invincible'):    # SHIELD
            return False
        loser.hp -= 1
        loser.score = max(0, loser.score - DEATH_SCORE_PENALTY)
        if winner is not None:
            share = int(loser.score * SCORE_TRANSFER)
            loser.score -= share
            winner.score += share
        loser.invuln = INVULN_FRAMES
        loser.stun = STUN_FRAMES
        sfx.play('hit')
        return True

    def resolve_head_clash():
        """Head to head: the LOWER score wins and takes nothing.

        Called once per frame, not once per player, or the clash resolves twice.
        A tie costs both of them, with no transfer.
        """
        if p1.hp <= 0 or p2.hp <= 0:
            return
        if p1.head.distance(p2.head) >= HIT_RADIUS:
            return
        if p1.score == p2.score:
            punish(p1)
            punish(p2)
            return
        loser, winner = (p1, p2) if p1.score > p2.score else (p2, p1)
        punish(loser, winner)                   # Ahead on score = you lose the clash

    def resolve_bite(biter, victim):
        """Biting ANY part of the other snake punishes the BITER.

        Tail and body are treated the same on purpose. The old rule rewarded biting
        the tail, which fought against the point of the game: you want the enemy to
        take a bite out of you.
        """
        if biter.hp <= 0 or victim.hp <= 0:
            return
        for pos in victim.segments():
            if biter.head.distance(pos) < HIT_RADIUS:
                punish(biter, victim)
                return

    def resolve_self_collision(snake):
        """Own body costs a stun and SELF_HIT_DAMAGE hp (set it to 0 for stun only).

        Two guards, both load-bearing:
          * the grace window, or this fires every frame while the head sits on its own
            body - that used to freeze the snake forever, and once self hits cost HP it
            drained every heart instead
          * the caller only asks when the head actually MOVED. A snake that bumped a
            wall while coiled has direction='stop' and never leaves its own body, so
            without that check it lost a heart every time the grace expired and died
            standing still.
        The direction is deliberately left alone so the snake coasts out of its own
        coil once the stun ends.
        """
        if snake.self_hit_grace > 0:
            return
        if powers_flag(snake, 'noclip'):        # PHASE
            return
        for pos in snake.segments()[2:]:        # Skip the 2 segments behind the head
            if snake.head.distance(pos) < HIT_RADIUS - 2:
                snake.stun = STUN_FRAMES
                snake.self_hit_grace = STUN_FRAMES + SELF_HIT_GRACE_EXTRA
                if SELF_HIT_DAMAGE:
                    punish(snake)               # No winner: nobody profits from this
                return

    def resolve_fruit(snake):
        for f in fruits:
            if snake.head.distance(f) < FRUIT_REACH:
                gain = int(FRUIT_SCORE * powers_effect(snake, 'score_mult', 1.0))
                snake.gain_fruit(gain, GROW_PER_FRUIT, SKILL_GAIN_2P)
                f.goto(random_free_spot(skip=f))
                sfx.play('eat')
                return                          # One fruit per frame, per player

    def check_win():
        if p1.hp <= 0 and p2.hp <= 0:
            return 'draw'
        if p1.hp <= 0: return p2
        if p2.hp <= 0: return p1
        if p1.score >= TARGET_SCORE and p2.score >= TARGET_SCORE:
            return 'draw' if p1.score == p2.score else (p1 if p1.score > p2.score else p2)
        if p1.score >= TARGET_SCORE: return p1
        if p2.score >= TARGET_SCORE: return p2
        return None

    # ===========================================
    # SECTION 5B: HUD & RESULT SCREEN
    # ===========================================
    def scoreline():
        return 'P1  {} - {}  P2'.format(round_wins['P1'], round_wins['P2'])

    def draw_hud():
        hud.clear()
        bar_pen.clear()
        for pl in players:
            geo = PANEL[pl.slot]
            if USE_HEART_ICONS:
                for i, icon in enumerate(heart_icons[pl.slot]):
                    icon.shape(HEART_FULL if i < pl.hp else HEART_EMPTY)
                    icon.showturtle()
                score_x = geo['x'] + geo['dir'] * (MAX_HP * HEART_STEP + 4)
            else:
                hud.color(pl.color_main)
                hud.goto(geo['x'], HEART_Y - 6)
                hud.write('<3 ' * max(0, pl.hp), align=geo['align'],
                          font=(FONT, 13, 'bold'))
                score_x = geo['x'] + geo['dir'] * (MAX_HP * 26)

            hud.color(pl.color_main)
            hud.goto(score_x, HEART_Y - 7)
            hud.write('{} {} [{}] {}'.format(pl.slot, pl.char_name, pl.skill_tag, pl.score),
                      align=geo['align'], font=(FONT, 14, 'bold'))

            draw_skill_bar(bar_pen, geo['bar_x'], BAR_Y, BAR_W, BAR_H,
                           pl.skill / SKILL_MAX, pl.color_main)

            tags = powers_hud_tags(pl)          # One label per running power
            if pl.stun > 0:
                tags.append('STUN')
            if tags:
                hud.color(TEXT_TAG)
                hud.goto(geo['bar_x'] + (BAR_W + 8 if geo['dir'] > 0 else -8), BAR_Y)
                hud.write(' '.join(tags), align='left' if geo['dir'] > 0 else 'right',
                          font=(FONT, 10, 'bold'))

        hud.color(HIGHLIGHT)                    # Round tally, e.g.  1 - 0
        hud.goto(0, 249)
        hud.write(scoreline(), align='center', font=(FONT, 16, 'bold'))
        hud.color(TEXT_DIM)
        hud.goto(0, 228)
        hud.write('FIRST TO {}  -  BEST OF {}'.format(TARGET_SCORE, ROUNDS_TO_WIN * 2 - 1),
                  align='center', font=(FONT, 10, 'bold'))
        hud.color(TEXT_FAINT)
        hud.goto(0, -272)
        hud.write(HINT, align='center', font=(FONT, 10, 'normal'))

    def show_result(winner):
        game_active['value'] = False
        if winner != 'draw':                    # Credit the round BEFORE drawing
            round_wins[winner.slot] += 1
        match_over['value'] = max(round_wins.values()) >= ROUNDS_TO_WIN
        for pl in players:
            pl.hide()
        for f in fruits:
            f.hideturtle()
        obstacle_pen.clear()
        hud.clear()                             # Or the HUD stays under the result text
        bar_pen.clear()
        for pool in heart_icons.values():
            for icon in pool:
                icon.hideturtle()

        result_pen.clear()
        result_pen.color(TEXT_BRIGHT)
        result_pen.goto(0, 95)
        result_pen.write('MATCH WINNER' if match_over['value'] else 'ROUND OVER',
                         align='center', font=(FONT, 26, 'bold'))
        if winner == 'draw':
            result_pen.goto(0, 50)
            result_pen.write('DRAW!', align='center', font=(FONT, 22, 'bold'))
        else:
            result_pen.color(winner.color_main)
            result_pen.goto(0, 50)
            label = 'TAKES THE MATCH!' if match_over['value'] else 'WINS THE ROUND!'
            result_pen.write('{} {}'.format(winner.name, label), align='center',
                             font=(FONT, 20, 'bold'))

        result_pen.color(HIGHLIGHT)              # The 1 - 0 the user asked for
        result_pen.goto(0, -5)
        result_pen.write(scoreline(), align='center', font=(FONT, 30, 'bold'))

        result_pen.color(TEXT_BRIGHT)
        result_pen.goto(0, -55)
        result_pen.write('P1  score {}  hp {}     |     P2  score {}  hp {}'.format(
            p1.score, max(0, p1.hp), p2.score, max(0, p2.hp)),
            align='center', font=(FONT, 13, 'normal'))
        result_pen.color(TEXT_DIM)
        result_pen.goto(0, -100)
        hint = ('Press R for a NEW MATCH     |     M for Menu' if match_over['value']
                else 'Press R for the next round     |     M for Menu')
        result_pen.write(hint, align='center', font=(FONT, 12, 'normal'))
        sfx.play('win')
        wn.update()

    # ===========================================
    # SECTION 5: MAIN GAME LOOP
    # ===========================================
    sfx.play('start')

    def game_loop():
        if STATE['epoch'] != epoch or not game_active['value']:
            return                              # A newer scene took over, or match ended

        moved = {}
        for pl in players:                      # 1. advance
            pl.tick_timers()
            moved[pl.slot] = step(pl)
        for pl in players:                      # 2. pickups and own body
            resolve_fruit(pl)
            if moved[pl.slot]:                  # A self hit needs a move to happen
                resolve_self_collision(pl)

        resolve_head_clash()                    # 3. combat
        resolve_bite(p1, p2)
        resolve_bite(p2, p1)

        for pl in players:                      # 4. draw
            pl.render()
        draw_hud()

        winner = check_win()                    # 5. win check
        if winner is not None:
            for pl in players:
                pl.direction = 'stop'
            show_result(winner)
            return

        wn.update()
        wn.ontimer(game_loop, FRAME_MS)

    game_loop()
