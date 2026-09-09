"""
snake_2p.py - 2 player battle mode (P1: WASD | P2: Arrow keys). Each player's
skill button only works if it matches what they picked on Character Select.
"""

import turtle
import random
from scene_manager import wn, go_to_scene, load_shape, STATE

def game_2p_scene(epoch, p1_skill, p2_skill):
    from menu import menu_scene                 # local import avoids a circular import at load time

    wn.title('Snake Battle - Local Multiplayer (P1: WASD | P2: Arrow Keys)')
    wn.bgcolor('black')

    ARENA_L, ARENA_R = -375, 375
    ARENA_B, ARENA_T = -275, 205
    BASE_SPEED = 3
    BOOST_SPEED = 6
    SEG_SPACING = 15
    START_LENGTH = 4
    GROW_PER_FRUIT = 1

    MAX_HP = 3
    TARGET_SCORE = 500
    FRUIT_SCORE = 100
    SCORE_PENALTY = 0.5

    SKILL_MAX = 100
    SKILL_GAIN = 25
    SKILL_COST = 50
    SKILL_FRAMES = 180

    STUN_FRAMES = 30
    INVULN_FRAMES = 60
    HIT_RADIUS = 12
    OBSTACLE_COUNT = 6
    OBSTACLE_SIZE = 60

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
        spots = [(-200, 65), (0, 65), (200, 65), (-200, -135), (0, -135), (200, -135)]
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
        def __init__(self, name, key, color, dim_color, start_pos, start_dir, skill_type):
            self.name = name
            self.key = key
            self.color_main = color
            self.color_dim = dim_color
            self.start_pos = start_pos
            self.start_dir = start_dir
            self.skill_type = skill_type                     # 'SPEED' or 'STEALTH' - chosen at Character Select
            self.skill_tag = 'SPD' if skill_type == 'SPEED' else 'STL'

            self.head_sprites = {d: load_shape('{}_head_{}'.format(key, d))
                                 for d in ('up', 'down', 'left', 'right')}
            self.ghost_sprites = {d: load_shape('{}_head_{}_ghost'.format(key, d))
                                  for d in ('up', 'down', 'left', 'right')}
            self.body_sprite = load_shape('{}_body'.format(key))
            self.use_sprites = all(self.head_sprites.values()) and self.body_sprite is not None

            self.head = turtle.Turtle()
            self.head.penup()
            if self.use_sprites:
                self.head.shape(self.head_sprites[start_dir])
            else:
                self.head.shape('square')
                self.head.color(color)
                self.head.shapesize(0.8, 0.8)

            self.stamper = turtle.Turtle()
            self.stamper.penup()
            if self.use_sprites:
                self.stamper.shape(self.body_sprite)
            else:
                self.stamper.shape('square')
                self.stamper.color(color)
                self.stamper.shapesize(0.65, 0.65)
            self.stamper.hideturtle()

            self.reset()

        def reset(self):
            self.head.goto(*self.start_pos)
            if not self.use_sprites:
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
            self.boost_timer = 0
            self.invis_timer = 0
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

        def use_speed_boost(self):                  # Only works if SPEED was chosen at Character Select
            if self.skill_type != 'SPEED':
                return
            if self.skill >= SKILL_COST and self.boost_timer == 0:
                self.skill -= SKILL_COST
                self.boost_timer = SKILL_FRAMES

        def use_invisibility(self):                 # Only works if STEALTH was chosen at Character Select
            if self.skill_type != 'STEALTH':
                return
            if self.skill >= SKILL_COST and self.invis_timer == 0:
                self.skill -= SKILL_COST
                self.invis_timer = SKILL_FRAMES

        def tick_timers(self):
            if self.stun > 0: self.stun -= 1
            if self.invuln > 0: self.invuln -= 1
            if self.boost_timer > 0: self.boost_timer -= 1
            if self.invis_timer > 0: self.invis_timer -= 1
            self.speed = BOOST_SPEED if self.boost_timer > 0 else BASE_SPEED

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
                bumped = True
            elif inside_obstacle(x, y, pad=6):
                bumped = True

            if bumped:
                self.stun = STUN_FRAMES
                self.direction = 'stop'
                return

            self.head.goto(x, y)
            self.path.append((round(x), round(y)))
            keep = int((self.length + 2) * SEG_SPACING / BASE_SPEED) + 8
            if len(self.path) > keep:
                del self.path[:-keep]

        def render(self):
            self.stamper.clearstamps()
            cloaked = self.invis_timer > 0
            blinking = self.invuln > 0 and (self.invuln // 4) % 2 == 0

            if self.use_sprites:
                self.head.hideturtle()
                if not cloaked:
                    self.stamper.shape(self.body_sprite)
                    for pos in self.segments():
                        self.stamper.goto(pos)
                        self.stamper.stamp()
                if not blinking:
                    table = self.ghost_sprites if cloaked else self.head_sprites
                    self.stamper.shape(table.get(self.facing) or self.head_sprites[self.facing])
                    self.stamper.goto(self.head.pos())
                    self.stamper.stamp()
                return

            if cloaked:
                self.head.color(self.color_dim)
            elif blinking:
                self.head.color('white')
            else:
                self.head.color(self.color_main)

            if not cloaked:
                self.stamper.color(self.color_main)
                for pos in self.segments():
                    self.stamper.goto(pos)
                    self.stamper.stamp()

    p1 = Snake('P1', 'p1', '#22e0e0', '#0d3a3a', (-250, -35), 'right', p1_skill)
    p2 = Snake('P2', 'p2', '#ffa22a', '#3a260d', (250, -35), 'left', p2_skill)
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
            if any(f is not skip and f.distance(x, y) < 40 for f in fruits):
                continue
            return x, y
        return 0, 0

    fruit_sprite = load_shape('fruit')
    fruits = []
    for _ in range(2):
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
    wn.onkeypress(p1.use_speed_boost, 'q')
    wn.onkeypress(p1.use_invisibility, 'e')
    wn.onkeypress(p2.use_speed_boost, 'o')
    wn.onkeypress(p2.use_invisibility, 'p')
    wn.onkeypress(to_menu, 'm')

    # --- Combat & scoring ---
    def apply_damage(victim):
        if victim.invuln > 0:
            return False
        victim.hp -= 1
        victim.score = int(victim.score * SCORE_PENALTY)
        victim.invuln = INVULN_FRAMES
        victim.stun = STUN_FRAMES
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
        segs = snake.segments()
        for pos in segs[2:]:
            if snake.head.distance(pos) < HIT_RADIUS - 2:
                snake.stun = STUN_FRAMES
                snake.direction = 'stop'
                return

    def resolve_fruit(snake):
        for f in fruits:
            if snake.head.distance(f) < 18:
                snake.score += FRUIT_SCORE
                snake.length += GROW_PER_FRUIT
                snake.skill = min(SKILL_MAX, snake.skill + SKILL_GAIN)
                f.goto(random_free_spot(skip=f))
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
        'p1': {'heart_x': -356, 'dir': 1, 'text_x': -356, 'align': 'left', 'bar_x': -358},
        'p2': {'heart_x': 356, 'dir': -1, 'text_x': 356, 'align': 'right', 'bar_x': 358 - BAR_W},
    }

    heart_icons = {}
    if USE_HEART_ICONS:
        for pl in players:
            pool = []
            geo = PANEL[pl.key]
            for i in range(MAX_HP):
                icon = turtle.Turtle()
                icon.penup()
                icon.shape(HEART_FULL)
                icon.goto(geo['heart_x'] + geo['dir'] * i * HEART_STEP, HEART_Y)
                pool.append(icon)
            heart_icons[pl.key] = pool

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
            geo = PANEL[pl.key]
            if USE_HEART_ICONS:
                for i, icon in enumerate(heart_icons[pl.key]):
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
            hud.write('{} [{}]  {}'.format(pl.name, pl.skill_tag, pl.score),
                       align=geo['align'], font=('Courier', 14, 'bold'))

            ratio = max(0.0, min(1.0, pl.skill / SKILL_MAX))
            draw_skill_bar(geo['bar_x'], 224, ratio, pl.color_main)

            tags = []
            if pl.boost_timer > 0: tags.append('BOOST')
            if pl.invis_timer > 0: tags.append('CLOAK')
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
        hud.write('P1: WASD  Q=Boost E=Cloak     |     P2: Arrows  O=Boost P=Cloak     |     M = Menu',
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
        result_pen.goto(0, -80)
        result_pen.color('gray')
        result_pen.write('Press R to play again     |     M for Menu', align='center', font=('Courier', 12, 'normal'))
        wn.update()

    def do_restart():
        if game_active['value']:
            return
        go_to_scene(game_2p_scene, p1_skill, p2_skill)

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
        wn.ontimer(game_loop, 16)

    game_loop()