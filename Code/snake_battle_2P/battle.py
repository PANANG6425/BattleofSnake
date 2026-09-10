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
                    SKILL_MAX, SKILL_GAIN_2P, MAX_HP, TARGET_SCORE, ROUNDS_TO_WIN, MAX_ROUNDS,
                    SCORE_TRANSFER, SELF_HIT_DAMAGE, STUN_FRAMES,
                    SELF_HIT_GRACE_EXTRA, INVULN_FRAMES, HIT_RADIUS, OBSTACLE_COUNT,
                    OBSTACLE_SIZE, OBSTACLE_SPOTS, FRUIT_COUNT_2P, FRUIT_MIN_GAP,
                    FRAME_MS, BG_COLOR, WALL_COLOR, OBSTACLE_FILL, OBSTACLE_EDGE,
                    TEXT_BRIGHT, TEXT_TAG, TEXT_DIM, TEXT_FAINT, HIGHLIGHT)
from engine import (wn, go_to_scene, load_shape, new_pen, STATE,
                    draw_skill_bar, fill_box, write_at, shape_turtle,
                    ImageButton, click_router)
from audio import sfx
from entity import (Snake, make_fruit, reroll_fruit, powers_flag, powers_effect,
                    powers_hud_tags)

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
BODY_CLEAR = 24                                 # Keep fruit off either snake's body

HEART_Y = 250
HEART_STEP = 22
BAR_W, BAR_H = 132, 12
BAR_Y = 224
ICON_GAP = 22                                   # Power icon, just outside the skill bar
ICON_SIZE = 0.9
TAG_LIFT = 20                                   # STUN / power tag floats this far above
                                                # the head - on the snake, where you are
                                                # actually looking, not up in the HUD
PANEL = {
    'P1': {'x': -356, 'dir': 1, 'align': 'left',  'bar_x': -358},
    'P2': {'x': 356,  'dir': -1, 'align': 'right', 'bar_x': 358 - BAR_W},
}
SPAWN = {'P1': ((-250, -35), 'right'), 'P2': ((250, -35), 'left')}
HINT = 'P1: WASD Q=Power  |  P2: Arrows O=Power  |  X = Sound  M = Menu'


def game_2p_scene(epoch, p1_char, p1_power, p2_char, p2_power, wins=None, history=None):
    """One round of a match.

    `wins` carries the round tally between rounds ({'P1': n, 'P2': n}) and `history`
    the per-round score ledger, so the final MATCH RESULT can add up a whole match
    even though each round starts the snakes back at 0.
    """
    # Local import: screens.py imports this module back, inside its own function.
    from screens import menu_scene, draw_result, scoreline

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
            # Heads are not enough: a fruit on a BODY segment costs the eater a heart
            # through resolve_self_collision. solo.py has always checked this.
            if any((px - x) ** 2 + (py - y) ** 2 < BODY_CLEAR ** 2
                   for pl in players for px, py in pl.segments()):
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
    rounds = list(history) if history else []   # One {'P1', 'P2', 'win'} per round played
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

    # The power each player CHOSE, pinned beside their bar. It never changes during a
    # round, so it is a plain shape turtle: no per-frame drawing, and it tells you what
    # your Q / O key will fire without reading any text.
    power_icons = []
    for pl in players:
        geo = PANEL[pl.slot]
        icon_x = geo['bar_x'] + (BAR_W + ICON_GAP if geo['dir'] > 0 else -ICON_GAP)
        power_icons.append(
            shape_turtle(pl.power['icon'], icon_x, BAR_Y + BAR_H / 2, size=ICON_SIZE))

    # ===========================================
    # SECTION 4: INPUT HANDLING
    # ===========================================
    def to_menu():
        go_to_scene(menu_scene)

    def do_restart():
        if game_active['value']:                # R only works on the result screen
            return
        # Carry the tally and the ledger into the next round, unless the match is
        # already decided - then R starts a fresh match at 0 - 0.
        done = match_over['value']
        go_to_scene(game_2p_scene, p1_char, p1_power, p2_char, p2_power,
                    None if done else round_wins, None if done else rounds)

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

    def punish(loser, hp=1):
        """One knockdown: HP only. Nothing here ever touches the score.

        Score moves in exactly ONE place in the whole game - a head-to-head clash,
        below. Everything else (a bite, your own body, and so the wall and boxes too)
        costs hearts alone, so a player can never be scored down for a collision they
        were not the aggressor in.

        Returns False when the hit was absorbed (immunity frames or SHIELD), which is
        also what stops a blocked clash from moving any score.
        """
        if loser.invuln > 0:
            return False
        if powers_flag(loser, 'invincible'):    # SHIELD
            return False
        loser.hp -= hp
        loser.invuln = INVULN_FRAMES
        loser.stun = STUN_FRAMES
        sfx.play('hit')
        return True

    def resolve_head_clash():
        """Head to head: the LOWER score WINS the clash and is PAID for it.

        The only score transfer in the game. The snake that is ahead loses a heart and
        hands over SCORE_TRANSFER of its score; the snake behind loses nothing and
        gains that score. Being in front is therefore dangerous, which is the point -
        it pushes the leader away from head-on fights and towards baiting instead.

        Called once per frame, not once per player, or the clash resolves twice.
        A level score costs both of them a heart, with no transfer either way.
        """
        if p1.hp <= 0 or p2.hp <= 0:
            return
        if p1.head.distance(p2.head) >= HIT_RADIUS:
            return
        # ONE clash per encounter. Without this the transfer flips who is ahead, so the
        # next frame - heads still touching, loser stunned in place - punished the snake
        # that had just WON the clash. Immunity frames on either side mean "still
        # recovering", and a clash needs two snakes that are both fit to fight.
        if p1.invuln > 0 or p2.invuln > 0:
            return
        if p1.score == p2.score:
            punish(p1)
            punish(p2)
            return
        loser, winner = (p1, p2) if p1.score > p2.score else (p2, p1)
        if punish(loser):                       # Ahead on score = you lose the clash
            share = int(loser.score * SCORE_TRANSFER)
            loser.score -= share
            winner.score += share
            # The loser is now stunned exactly where the heads met, so the winner's head
            # is touching its neck. Without this the very next resolve_bite() charged
            # the winner a heart for the clash it had just won - the opposite of the
            # rule that the lower score pays nothing.
            winner.bite_grace = STUN_FRAMES

    def resolve_bite(biter, victim):
        """Biting ANY part of the other snake costs the BITER a heart - and only that.

        Tail and body are treated the same on purpose. The old rule rewarded biting
        the tail, which fought against the point of the game: you want the enemy to
        take a bite out of you. No score changes hands here, whoever is ahead, so a
        bite is a pure HP punishment.
        """
        if biter.hp <= 0 or victim.hp <= 0:
            return
        if biter.bite_grace > 0:                # Just won a head clash - see there
            return
        for pos in victim.segments():
            if biter.head.distance(pos) < HIT_RADIUS:
                punish(biter)
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
                    punish(snake, SELF_HIT_DAMAGE)   # HP only, a fumble costs no score
                return

    def resolve_fruit(snake):
        for f in fruits:
            if snake.head.distance(f) < FRUIT_REACH:
                gain = int(FRUIT_SCORE * powers_effect(snake, 'score_mult', 1.0))
                snake.gain_fruit(gain, GROW_PER_FRUIT, SKILL_GAIN_2P)
                f.goto(random_free_spot(skip=f))
                reroll_fruit(f)                 # New spot, new fruit - looks only
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
    # SECTION 5B: HUD & END OF ROUND
    # ===========================================
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
                write_at(hud, geo['x'], HEART_Y - 6, '<3 ' * max(0, pl.hp), 13,
                         pl.color_main, geo['align'])
                score_x = geo['x'] + geo['dir'] * (MAX_HP * 26)

            write_at(hud, score_x, HEART_Y - 7, '{} {} [{}] {}'.format(
                pl.slot, pl.char_name, pl.skill_tag, pl.score), 14,
                pl.color_main, geo['align'])

            draw_skill_bar(bar_pen, geo['bar_x'], BAR_Y, BAR_W, BAR_H,
                           pl.skill / SKILL_MAX, pl.color_main)

            # STUN and the active-power tag ride ABOVE THE SNAKE, not next to the bar.
            # Beside the bar they read as part of the skill meter, which is what made
            # STUN confusing; over the head they are unmistakably about the snake.
            tags = powers_hud_tags(pl)          # One label per running power
            if pl.stun > 0:
                tags.append('STUN')
            if tags:
                # Keep the label inside the arena: centred text runs off the side walls,
                # and near the ceiling it climbs into the skill-bar row, so flip it under
                # the head up there instead.
                tx = min(max(pl.head.xcor(), ARENA_L + 40), ARENA_R - 40)
                ty = pl.head.ycor()
                ty += TAG_LIFT if ty < ARENA_T - 40 else -TAG_LIFT - 8
                write_at(hud, tx, ty, ' '.join(tags), 10, TEXT_TAG)

        write_at(hud, 0, 249, scoreline(round_wins), 16, HIGHLIGHT)       # Round tally,  1 - 0
        write_at(hud, 0, 228, 'FIRST TO {}  -  BEST OF {}'.format(
            TARGET_SCORE, ROUNDS_TO_WIN * 2 - 1), 10, TEXT_DIM)
        write_at(hud, 0, -272, HINT, 10, TEXT_FAINT)

    def clear_field():
        """Take the arena off screen so a result can be drawn over it."""
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
        for icon in power_icons:                # Or they float over the result text
            icon.hideturtle()

    def show_result(winner):
        """End of a round: bank the round, then hand off to the result screen.

        The ledger records the HP each player FINISHED the round with, because the
        match summary weights score by survival (screens.py explains the maths).
        A knocked-out player banks hp 0, so that round scores them nothing.
        """
        game_active['value'] = False
        rounds.append({'P1': p1.score, 'P2': p2.score,
                       'hpP1': max(0, p1.hp), 'hpP2': max(0, p2.hp),
                       'win': '-' if winner == 'draw' else winner.slot})
        if winner != 'draw':                    # Credit the round BEFORE drawing
            round_wins[winner.slot] += 1
        # Rounds also run out: without the MAX_ROUNDS half, a match where every round
        # is a draw would never reach ROUNDS_TO_WIN and never end.
        match_over['value'] = (max(round_wins.values()) >= ROUNDS_TO_WIN
                               or len(rounds) >= MAX_ROUNDS)
        clear_field()
        result_pen.clear()
        draw_result(result_pen, p1, p2, round_wins, rounds,
                    match_over['value'], winner)

        # R and M still work; these are the same two actions as buttons, because a
        # result screen is the one place a player is not already holding the keys.
        again = ImageButton('btn_playgame', -90, -232, 150, 86,
                            label='NEXT' if not match_over['value'] else 'AGAIN',
                            color=HIGHLIGHT)
        back = ImageButton('btn_menu', 90, -232, 110, 63, label='MENU', color=TEXT_DIM)
        wn.onscreenclick(click_router((again, do_restart), (back, to_menu)))

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
