"""
snake_2p.py - 2 player battle mode (P1: WASD | P2: Arrow keys). Each player's
skill button only works if it matches what they picked on Character Select.
"""

import turtle
import random
from scene_manager import wn, go_to_scene, load_shape, STATE
from characters import by_key
import powers
from audio import sfx
from game_config import (ARENA_2P, SPEED_2P, SEG_SPACING, START_LENGTH, GROW_PER_FRUIT,
                         MAX_HP, TARGET_SCORE, FRUIT_SCORE, SCORE_PENALTY,
                         SKILL_MAX, SKILL_GAIN_2P, STUN_FRAMES, SELF_HIT_GRACE_EXTRA,
                         INVULN_FRAMES, HIT_RADIUS, OBSTACLE_COUNT, OBSTACLE_SIZE,
                         OBSTACLE_SPOTS, FRUIT_COUNT_2P, FRUIT_MIN_GAP, FRAME_MS, FONT)

def game_2p_scene(epoch, p1_char, p1_skill, p2_char, p2_skill):
    from menu import menu_scene                 # local import avoids a circular import at load time

    wn.title('Snake Battle - Local Multiplayer (P1: WASD | P2: Arrow Keys)')
    wn.bgcolor('black')

    ARENA_L, ARENA_R, ARENA_B, ARENA_T = ARENA_2P
    BASE_SPEED = SPEED_2P
    SKILL_GAIN = SKILL_GAIN_2P

    # --- Arena border ---
    border = turtle.Turtle()
    border.color('gray')
    border.pensize(6)
    border.penup()
    border.goto(-380, 210)
    border.pendown()
    for _ in range(2):
        border.forward(760)
        border.right(90)
        border.forward(490)
        border.right(90)
    border.hideturtle()

    # --- Obstacles ---
    obstacle_pen = turtle.Turtle()
    obstacle_pen.hideturtle()
    obstacle_pen.penup()
    obstacle_pen.color('#5a5a6e', '#2b2b3a')
    obstacle_pen.pensize(3)
    obstacles = []

    def draw_obstacle_box(cx, cy, size):
        half = size / 2
        obstacle_pen.penup()
        obstacle_pen.goto(cx - half, cy + half)
        obstacle_pen.setheading(0)
        obstacle_pen.pendown()
        obstacle_pen.begin_fill()
        for _ in range(4):
            obstacle_pen.forward(size)
            obstacle_pen.right(90)
        obstacle_pen.end_fill()
        obstacle_pen.penup()
        obstacles.append((cx - half, cy - half, cx + half, cy + half))

    def build_obstacles():
        obstacle_pen.clear()
        obstacles.clear()
        spots = OBSTACLE_SPOTS
        for cx, cy in spots[:OBSTACLE_COUNT]:
            draw_obstacle_box(cx, cy, OBSTACLE_SIZE)

    def inside_obstacle(x, y, pad=0):
        for left, bottom, right, top in obstacles:
            if left - pad <= x <= right + pad and bottom - pad <= y <= top + pad:
                return True
        return False

    build_obstacles()

    # --- Snake entity (shared by both players) ---
    class Snake:
        def __init__(self, slot, char_key, start_pos, start_dir, skill_type):
            # slot is the seat ('P1' / 'P2') and drives the HUD side. char_key is the
            # chosen character, and doubles as the sprite filename prefix. They are
            # separate now that either seat can pick any character.
            char = by_key(char_key)
            self.slot = slot
            self.name = slot
            self.char_name = char['name']
            self.key = char['key']
            key = self.key
            self.color_main = char['main']
            self.color_dim = char['dim']
            self.start_pos = start_pos
            self.start_dir = start_dir
            self.power = powers.by_key(skill_type)   # Chosen at Character Select
            self.skill_type = self.power['key']
            self.skill_tag = self.power['tag']

            self.head_sprites = {d: load_shape('{}_head_{}'.format(key, d))
                                 for d in ('up', 'down', 'left', 'right')}
            self.ghost_sprites = {d: load_shape('{}_head_{}_ghost'.format(key, d))
                                  for d in ('up', 'down', 'left', 'right')}
            self.body_sprite = load_shape('{}_body'.format(key))

            # Head and body are decided SEPARATELY. turtle cannot tint an image shape,
            # so a .gif carries its own colour and characters.py cannot recolour it.
            # Splitting the two lets you drop in .gif heads and still have the body take
            # its colour from characters.py: just do not ship a <key>_body.gif.
            self.use_head_sprites = all(self.head_sprites.values())
            self.use_body_sprite = self.body_sprite is not None

            self.head = turtle.Turtle()
            self.head.penup()
            if self.use_head_sprites:
                self.head.shape(self.head_sprites[start_dir])
            else:
                self.head.shape('square')
                self.head.color(self.color_main)
                self.head.shapesize(0.8, 0.8)

            # The stamper's shape is set per stamp group in render(), because the body
            # and the head can now be different kinds (image vs coloured square).
            self.stamper = turtle.Turtle()
            self.stamper.penup()
            self.stamper.hideturtle()

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
            self.hp = MAX_HP
            self.score = 0
            self.skill = 0
            self.speed = BASE_SPEED
            self.stun = 0
            self.invuln = 0
            self.self_hit_grace = 0             # Frames left where a self hit cannot retrigger
            powers.init(self)                   # {power key -> frames left}; no per-power attrs
            self.stamper.clearstamps()

        def segments(self):
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

        def turn(self, new_dir, opposite):
            if self.direction != opposite:
                self.direction = new_dir
                self.facing = new_dir

        def use_power(self):
            # One key per player fires whichever power they picked, so the registry
            # can grow past two without running out of keys to bind.
            if powers.activate(self):
                sfx.play('power')

        def tick_timers(self):
            if self.stun > 0: self.stun -= 1
            if self.invuln > 0: self.invuln -= 1
            if self.self_hit_grace > 0: self.self_hit_grace -= 1
            powers.tick(self)
            self.speed = BASE_SPEED * powers.effect(self, 'speed_mult', 1.0)

        def move(self):
            if self.stun > 0 or self.direction == 'stop':
                return
            x, y = self.head.xcor(), self.head.ycor()
            if self.direction == 'up': y += self.speed
            elif self.direction == 'down': y -= self.speed
            elif self.direction == 'left': x -= self.speed
            elif self.direction == 'right': x += self.speed

            bumped = False
            if x > ARENA_R or x < ARENA_L or y > ARENA_T or y < ARENA_B:
                bumped = True                   # The outer wall always stops you
            elif inside_obstacle(x, y, pad=6) and not powers.flag(self, 'noclip'):
                bumped = True                   # PHASE slips through the boxes

            if bumped:
                self.stun = STUN_FRAMES
                self.direction = 'stop'
                sfx.play('bump')
                return

            self.head.goto(x, y)
            self.path.append((round(x), round(y)))
            keep = int((self.length + 2) * SEG_SPACING / BASE_SPEED) + 8
            if len(self.path) > keep:
                del self.path[:-keep]

        def render(self):
            self.stamper.clearstamps()
            cloaked = powers.flag(self, 'cloak')
            blinking = self.invuln > 0 and (self.invuln // 4) % 2 == 0

            # 1. BODY, stamped first. The head goes on top of it, and turtle canvas
            #    items keep creation order, so the head has to be stamped last.
            if not cloaked:                     # CLOAK hides the body entirely
                if self.use_body_sprite:
                    self.stamper.shape(self.body_sprite)
                else:
                    self.stamper.shape('square')
                    self.stamper.color(self.color_main)   # <- body colour, from characters.py
                    self.stamper.shapesize(0.65, 0.65)
                for pos in self.segments():
                    self.stamper.goto(pos)
                    self.stamper.stamp()

            # 2. HEAD
            if self.use_head_sprites:
                self.head.hideturtle()          # The sprite head is stamped, not shown
                if not blinking:                # Blink = skip a frame after taking a hit
                    use_ghost = cloaked and all(self.ghost_sprites.values())
                    table = self.ghost_sprites if use_ghost else self.head_sprites
                    self.stamper.shape(table[self.facing])
                    self.stamper.goto(self.head.pos())
                    self.stamper.stamp()
            else:
                self.head.showturtle()
                self.head.shape('square')
                self.head.shapesize(0.8, 0.8)
                if cloaked:
                    self.head.color(self.color_dim)
                elif blinking:
                    self.head.color('white')
                else:
                    self.head.color(self.color_main)

    p1 = Snake('P1', p1_char, (-250, -35), 'right', p1_skill)
    p2 = Snake('P2', p2_char, (250, -35), 'left', p2_skill)
    players = [p1, p2]

    # --- Fruits ---
    def random_free_spot(skip=None):
        for _ in range(200):
            x = random.randint(ARENA_L + 30, ARENA_R - 30)
            y = random.randint(ARENA_B + 30, ARENA_T - 30)
            if inside_obstacle(x, y, pad=20):
                continue
            if any(pl.head.distance(x, y) < 60 for pl in players):
                continue
            # Keep fruits apart, otherwise two can land on the same spot and one
            # touch scores both of them at once.
            if any(f is not skip and f.distance(x, y) < FRUIT_MIN_GAP for f in fruits):
                continue
            return x, y
        return 0, 0

    fruit_sprite = load_shape('fruit')
    fruits = []
    for _ in range(FRUIT_COUNT_2P):
        f = turtle.Turtle()
        f.penup()
        if fruit_sprite:
            f.shape(fruit_sprite)
        else:
            f.shape('circle')
            f.color('red')
            f.shapesize(0.7, 0.7)
        f.goto(random_free_spot())
        fruits.append(f)

    # --- Input handling ---
    def p1_up(): p1.turn('up', 'down')
    def p1_down(): p1.turn('down', 'up')
    def p1_left(): p1.turn('left', 'right')
    def p1_right(): p1.turn('right', 'left')
    def p2_up(): p2.turn('up', 'down')
    def p2_down(): p2.turn('down', 'up')
    def p2_left(): p2.turn('left', 'right')
    def p2_right(): p2.turn('right', 'left')

    def to_menu():
        go_to_scene(menu_scene)

    wn.listen()
    wn.onkeypress(p1_up, 'w')
    wn.onkeypress(p1_down, 's')
    wn.onkeypress(p1_left, 'a')
    wn.onkeypress(p1_right, 'd')
    wn.onkeypress(p2_up, 'Up')
    wn.onkeypress(p2_down, 'Down')
    wn.onkeypress(p2_left, 'Left')
    wn.onkeypress(p2_right, 'Right')
    # One power key per player, whatever power they picked. E and P stay bound as
    # aliases so the old muscle memory still works.
    wn.onkeypress(p1.use_power, 'q')
    wn.onkeypress(p1.use_power, 'e')
    wn.onkeypress(p2.use_power, 'o')
    wn.onkeypress(p2.use_power, 'p')
    wn.onkeypress(sfx.toggle, 'x')
    wn.onkeypress(to_menu, 'm')

    # --- Combat & scoring ---
    def apply_damage(victim):
        if victim.invuln > 0:
            return False
        if powers.flag(victim, 'invincible'):   # SHIELD
            return False
        victim.hp -= 1
        victim.score = int(victim.score * SCORE_PENALTY)
        victim.invuln = INVULN_FRAMES
        victim.stun = STUN_FRAMES
        sfx.play('hit')
        return True

    def resolve_attacks(attacker, defender):
        if attacker.hp <= 0 or defender.hp <= 0:
            return
        head = attacker.head
        if head.distance(defender.head) < HIT_RADIUS:
            apply_damage(defender)
            return
        segs = defender.segments()
        if not segs:
            return
        if head.distance(segs[-1]) < HIT_RADIUS:
            apply_damage(defender)
            return
        for pos in segs[:-1]:
            if head.distance(pos) < HIT_RADIUS:
                apply_damage(attacker)
                return

    def resolve_self_collision(snake):
        """Running into your own body costs a short stun, never HP.

        This used to DEADLOCK the snake permanently. It set direction='stop', and move()
        returns early while stunned, so the head never left its own body - which meant
        this check fired again on the very next frame, resetting the stun to 30 forever.
        The snake froze and no key press could recover it, because turn() was overwritten
        by direction='stop' again a frame later.

        Two changes break the loop: a grace window so one self hit cannot retrigger, and
        keeping the current direction so the snake coasts out of its own coil once the
        stun ends, with no key press needed.
        """
        if snake.self_hit_grace > 0:            # Still recovering from the last self hit
            return
        if powers.flag(snake, 'noclip'):        # PHASE slips through your own tail
            return
        segs = snake.segments()
        for pos in segs[2:]:                    # Skip the 2 segments right behind the head
            if snake.head.distance(pos) < HIT_RADIUS - 2:
                snake.stun = STUN_FRAMES
                snake.self_hit_grace = STUN_FRAMES + SELF_HIT_GRACE_EXTRA
                return

    def resolve_fruit(snake):
        for f in fruits:
            if snake.head.distance(f) < 18:
                snake.score += int(FRUIT_SCORE * powers.effect(snake, 'score_mult', 1.0))
                snake.length += GROW_PER_FRUIT
                snake.skill = min(SKILL_MAX, snake.skill + SKILL_GAIN)
                f.goto(random_free_spot(skip=f))
                sfx.play('eat')
                return                          # One fruit per frame, per player

    # --- HUD ---
    hud = turtle.Turtle()
    hud.hideturtle()
    hud.penup()
    hud.color('white')
    bar_pen = turtle.Turtle()
    bar_pen.hideturtle()
    bar_pen.penup()

    HEART_FULL = load_shape('heart_full')
    HEART_EMPTY = load_shape('heart_empty')
    USE_HEART_ICONS = HEART_FULL is not None and HEART_EMPTY is not None

    HEART_Y = 250
    HEART_STEP = 22
    BAR_W, BAR_H = 132, 12
    PANEL = {
        'P1': {'heart_x': -356, 'dir': 1, 'text_x': -356, 'align': 'left', 'bar_x': -358},
        'P2': {'heart_x': 356, 'dir': -1, 'text_x': 356, 'align': 'right', 'bar_x': 358 - BAR_W},
    }

    heart_icons = {}
    if USE_HEART_ICONS:
        for pl in players:
            pool = []
            geo = PANEL[pl.slot]
            for i in range(MAX_HP):
                icon = turtle.Turtle()
                icon.penup()
                icon.shape(HEART_FULL)
                icon.goto(geo['heart_x'] + geo['dir'] * i * HEART_STEP, HEART_Y)
                pool.append(icon)
            heart_icons[pl.slot] = pool

    def draw_skill_bar(left, bottom, ratio, color):
        bar_pen.penup()
        bar_pen.goto(left, bottom)
        bar_pen.setheading(0)
        bar_pen.pensize(2)
        bar_pen.color('#5a5a6b')
        bar_pen.pendown()
        for _ in range(2):
            bar_pen.forward(BAR_W)
            bar_pen.left(90)
            bar_pen.forward(BAR_H)
            bar_pen.left(90)
        bar_pen.penup()
        fill_w = (BAR_W - 4) * ratio
        if fill_w >= 1:
            bar_pen.goto(left + 2, bottom + 2)
            bar_pen.color(color)
            bar_pen.pendown()
            bar_pen.begin_fill()
            for _ in range(2):
                bar_pen.forward(fill_w)
                bar_pen.left(90)
                bar_pen.forward(BAR_H - 4)
                bar_pen.left(90)
            bar_pen.end_fill()
            bar_pen.penup()

    def draw_hud():
        hud.clear()
        bar_pen.clear()
        for pl in players:
            geo = PANEL[pl.slot]
            if USE_HEART_ICONS:
                for i, icon in enumerate(heart_icons[pl.slot]):
                    icon.shape(HEART_FULL if i < pl.hp else HEART_EMPTY)
                    icon.showturtle()
                score_x = geo['text_x'] + geo['dir'] * (MAX_HP * HEART_STEP + 4)
            else:
                hud.color(pl.color_main)
                hud.goto(geo['text_x'], HEART_Y - 6)
                hud.write('<3 ' * max(0, pl.hp), align=geo['align'], font=('Courier', 13, 'bold'))
                score_x = geo['text_x'] + geo['dir'] * (MAX_HP * 26)

            hud.color(pl.color_main)
            hud.goto(score_x, HEART_Y - 7)
            hud.write('{} {} [{}] {}'.format(pl.slot, pl.char_name, pl.skill_tag, pl.score),
                       align=geo['align'], font=('Courier', 14, 'bold'))

            ratio = max(0.0, min(1.0, pl.skill / SKILL_MAX))
            draw_skill_bar(geo['bar_x'], 224, ratio, pl.color_main)

            tags = []
            tags = powers.hud_tags(pl)      # One label per running power
            if pl.stun > 0: tags.append('STUN')
            if tags:
                hud.color('#dddddd')
                hud.goto(geo['bar_x'] + (BAR_W + 8 if geo['dir'] > 0 else -8), 224)
                hud.write(' '.join(tags), align='left' if geo['dir'] > 0 else 'right',
                           font=('Courier', 10, 'bold'))

        hud.color('gray')
        hud.goto(0, 243)
        hud.write('FIRST TO {}'.format(TARGET_SCORE), align='center', font=('Courier', 12, 'bold'))
        hud.color('#4a4a4a')
        hud.goto(0, -272)
        hud.write('P1: WASD Q=Power  |  P2: Arrows O=Power  |  X = Sound  M = Menu',
                   align='center', font=('Courier', 10, 'normal'))

    # --- Win condition & result screen ---
    result_pen = turtle.Turtle()
    result_pen.hideturtle()
    result_pen.penup()
    game_active = {'value': True}

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

    def show_result(winner):
        game_active['value'] = False
        for pl in players:
            pl.head.hideturtle()
            pl.stamper.clearstamps()
        for f in fruits:
            f.hideturtle()
        obstacle_pen.clear()
        hud.clear()                             # Was missing: the HUD text stayed under the result
        bar_pen.clear()                         # Was missing: the skill bars stayed on screen
        for pool in heart_icons.values():       # Was missing: the hearts stayed on screen
            for icon in pool:
                icon.hideturtle()

        result_pen.clear()
        result_pen.color('white')
        result_pen.goto(0, 60)
        result_pen.write('RESULT', align='center', font=('Courier', 26, 'bold'))

        if winner == 'draw':
            result_pen.goto(0, 15)
            result_pen.write('DRAW!', align='center', font=('Courier', 22, 'bold'))
        else:
            result_pen.color(winner.color_main)
            result_pen.goto(0, 15)
            result_pen.write('{} WINS!'.format(winner.name), align='center', font=('Courier', 22, 'bold'))

        result_pen.color('white')
        result_pen.goto(0, -30)
        result_pen.write('P1  score {}  hp {}     |     P2  score {}  hp {}'.format(
            p1.score, max(0, p1.hp), p2.score, max(0, p2.hp)),
            align='center', font=('Courier', 13, 'normal'))
        sfx.play('win')
        result_pen.goto(0, -80)
        result_pen.color('gray')
        result_pen.write('Press R to play again     |     M for Menu', align='center', font=('Courier', 12, 'normal'))
        wn.update()

    def do_restart():
        if game_active['value']:
            return
        go_to_scene(game_2p_scene, p1_char, p1_skill, p2_char, p2_skill)

    wn.onkeypress(do_restart, 'r')

    def game_loop():
        if STATE['epoch'] != epoch or not game_active['value']:
            return

        for pl in players:
            pl.tick_timers()
            pl.move()
        for pl in players:
            resolve_fruit(pl)
            resolve_self_collision(pl)

        resolve_attacks(p1, p2)
        resolve_attacks(p2, p1)

        for pl in players:
            pl.render()
        draw_hud()

        winner = check_win()
        if winner is not None:
            for pl in players:
                pl.direction = 'stop'
            show_result(winner)
            return

        wn.update()
        wn.ontimer(game_loop, FRAME_MS)

    game_loop()