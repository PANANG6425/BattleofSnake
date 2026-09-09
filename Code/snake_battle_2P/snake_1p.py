"""
snake_1p.py - single player classic snake + one chosen power (SPEED or
STEALTH), picked on the Character Select screen.
"""

import turtle
import random
from scene_manager import wn, go_to_scene, load_shape, STATE

def game_1p_scene(epoch, skill):
    from menu import menu_scene                 # local import avoids a circular import at load time

    wn.title('Snake - 1 Player ({})'.format(skill))
    wn.bgcolor('black')

    ARENA_L, ARENA_R = -380, 380
    ARENA_B, ARENA_T = -280, 260
    BASE_SPEED = 4
    BOOST_SPEED = 8
    SEG_SPACING = 15
    START_LENGTH = 4
    SKILL_MAX = 100
    SKILL_GAIN = 20
    SKILL_COST = 50
    SKILL_FRAMES = 180
    FRUIT_SCORE = 100

    border = turtle.Turtle()
    border.color('gray')
    border.pensize(6)
    border.penup()
    border.goto(ARENA_L - 5, ARENA_T + 5)
    border.pendown()
    for _ in range(2):
        border.forward(ARENA_R - ARENA_L + 10)
        border.right(90)
        border.forward(ARENA_T - ARENA_B + 10)
        border.right(90)
    border.hideturtle()

    head_sprites = {d: load_shape('p1_head_{}'.format(d)) for d in ('up', 'down', 'left', 'right')}
    ghost_sprites = {d: load_shape('p1_head_{}_ghost'.format(d)) for d in ('up', 'down', 'left', 'right')}
    body_sprite = load_shape('p1_body')
    use_sprites = all(head_sprites.values()) and body_sprite is not None

    head = turtle.Turtle()
    head.penup()
    if use_sprites:
        head.shape(head_sprites['right'])
    else:
        head.shape('square')
        head.color('#22e0e0')
        head.shapesize(0.8, 0.8)
    head.goto(0, 0)

    stamper = turtle.Turtle()
    stamper.penup()
    stamper.hideturtle()
    if use_sprites:
        stamper.shape(body_sprite)
    else:
        stamper.shape('square')
        stamper.color('#22e0e0')
        stamper.shapesize(0.65, 0.65)

    fruit_sprite = load_shape('fruit')
    fruit = turtle.Turtle()
    fruit.penup()
    if fruit_sprite:
        fruit.shape(fruit_sprite)
    else:
        fruit.shape('circle')
        fruit.color('red')
        fruit.shapesize(0.7, 0.7)

    state = {
        'direction': 'stop', 'facing': 'right', 'length': START_LENGTH,
        'path': [(0, 0)], 'score': 0, 'skill': 0, 'speed': BASE_SPEED,
        'boost_timer': 0, 'invis_timer': 0, 'active': True,
    }

    def random_free_spot():
        for _ in range(200):
            x = random.randint(ARENA_L + 30, ARENA_R - 30)
            y = random.randint(ARENA_B + 30, ARENA_T - 30)
            if head.distance(x, y) > 60:
                return x, y
        return 0, 0

    fruit.goto(random_free_spot())

    def turn(new_dir, opposite):
        if state['direction'] != opposite:
            state['direction'] = new_dir
            state['facing'] = new_dir

    def go_up(): turn('up', 'down')
    def go_down(): turn('down', 'up')
    def go_left(): turn('left', 'right')
    def go_right(): turn('right', 'left')

    def use_skill():
        if state['skill'] < SKILL_COST:
            return
        if skill == 'SPEED' and state['boost_timer'] == 0:
            state['skill'] -= SKILL_COST
            state['boost_timer'] = SKILL_FRAMES
        elif skill == 'STEALTH' and state['invis_timer'] == 0:
            state['skill'] -= SKILL_COST
            state['invis_timer'] = SKILL_FRAMES

    result_pen = turtle.Turtle()
    result_pen.hideturtle()
    result_pen.penup()

    def retry():
        if state['active']:
            return
        go_to_scene(game_1p_scene, skill)

    def to_menu():
        go_to_scene(menu_scene)

    wn.listen()
    wn.onkeypress(go_up, 'Up')
    wn.onkeypress(go_down, 'Down')
    wn.onkeypress(go_left, 'Left')
    wn.onkeypress(go_right, 'Right')
    wn.onkeypress(use_skill, 'space')
    wn.onkeypress(retry, 'r')
    wn.onkeypress(to_menu, 'm')

    hud = turtle.Turtle()
    hud.hideturtle()
    hud.penup()
    hud.color('white')
    bar_pen = turtle.Turtle()
    bar_pen.hideturtle()
    bar_pen.penup()

    def segments():
        points = []
        target = SEG_SPACING
        travelled = 0.0
        path = state['path']
        prev = path[-1]
        for i in range(len(path) - 2, -1, -1):
            cur = path[i]
            travelled += abs(cur[0] - prev[0]) + abs(cur[1] - prev[1])
            prev = cur
            while travelled >= target and len(points) < state['length']:
                points.append(cur)
                target += SEG_SPACING
            if len(points) >= state['length']:
                break
        return points

    def draw_skill_bar():
        bar_pen.clear()
        left, bottom, w, h = -70, 226, 140, 12
        bar_pen.goto(left, bottom)
        bar_pen.setheading(0)
        bar_pen.pensize(2)
        bar_pen.color('#5a5a6b')
        bar_pen.pendown()
        for _ in range(2):
            bar_pen.forward(w)
            bar_pen.left(90)
            bar_pen.forward(h)
            bar_pen.left(90)
        bar_pen.penup()
        ratio = max(0.0, min(1.0, state['skill'] / SKILL_MAX))
        fill_w = (w - 4) * ratio
        if fill_w >= 1:
            bar_pen.goto(left + 2, bottom + 2)
            bar_pen.color('#22e0e0')
            bar_pen.pendown()
            bar_pen.begin_fill()
            for _ in range(2):
                bar_pen.forward(fill_w)
                bar_pen.left(90)
                bar_pen.forward(h - 4)
                bar_pen.left(90)
            bar_pen.end_fill()
            bar_pen.penup()

    def draw_hud():
        hud.clear()
        hud.color('white')
        hud.goto(-380, 268)
        hud.write('SCORE: {}'.format(state['score']), font=('Courier', 14, 'bold'))
        draw_skill_bar()
        tag = 'BOOST!' if state['boost_timer'] > 0 else ('CLOAK!' if state['invis_timer'] > 0 else '')
        hud.color('gold')
        hud.goto(0, 268)
        hud.write(tag, align='center', font=('Courier', 12, 'bold'))
        hud.color('#8a93a3')
        hud.goto(380, 268)
        hud.write('[{}]'.format(skill), align='right', font=('Courier', 12, 'bold'))
        hud.color('#4a4a4a')
        hud.goto(0, -272)
        hud.write('Arrows = Move   SPACE = {}   R = Retry   M = Menu'.format(skill),
                   align='center', font=('Courier', 10, 'normal'))

    def render():
        stamper.clearstamps()
        cloaked = state['invis_timer'] > 0
        if use_sprites:
            head.hideturtle()
            table = ghost_sprites if cloaked else head_sprites
            if not cloaked:
                stamper.shape(body_sprite)
                for pos in segments():
                    stamper.goto(pos)
                    stamper.stamp()
            stamper.shape(table.get(state['facing']) or head_sprites[state['facing']])
            stamper.goto(head.pos())
            stamper.stamp()
        else:
            head.color('#0d3a3a' if cloaked else '#22e0e0')
            if not cloaked:
                stamper.color('#22e0e0')
                for pos in segments():
                    stamper.goto(pos)
                    stamper.stamp()

    def game_over():
        state['active'] = False
        result_pen.clear()
        result_pen.color('white')
        result_pen.goto(0, 30)
        result_pen.write('GAME OVER', align='center', font=('Courier', 26, 'bold'))
        result_pen.goto(0, -10)
        result_pen.write('Score: {}'.format(state['score']), align='center', font=('Courier', 18, 'bold'))
        result_pen.color('gray')
        result_pen.goto(0, -50)
        result_pen.write('R = Retry     M = Menu', align='center', font=('Courier', 12, 'normal'))
        wn.update()

    def loop():
        if STATE['epoch'] != epoch or not state['active']:
            return

        if state['boost_timer'] > 0:
            state['boost_timer'] -= 1
        if state['invis_timer'] > 0:
            state['invis_timer'] -= 1
        state['speed'] = BOOST_SPEED if state['boost_timer'] > 0 else BASE_SPEED

        if state['direction'] != 'stop':
            x, y = head.xcor(), head.ycor()
            if state['direction'] == 'up': y += state['speed']
            elif state['direction'] == 'down': y -= state['speed']
            elif state['direction'] == 'left': x -= state['speed']
            elif state['direction'] == 'right': x += state['speed']

            if x > ARENA_R or x < ARENA_L or y > ARENA_T or y < ARENA_B:
                game_over()
                return

            head.goto(x, y)
            state['path'].append((round(x), round(y)))
            keep = int((state['length'] + 2) * SEG_SPACING / BASE_SPEED) + 8
            if len(state['path']) > keep:
                del state['path'][:-keep]

            if state['invis_timer'] == 0:            # STEALTH lets you phase through your own tail
                for pos in segments()[2:]:
                    if head.distance(pos) < 10:
                        game_over()
                        return

            if head.distance(fruit) < 18:
                state['score'] += FRUIT_SCORE
                state['length'] += 1
                state['skill'] = min(SKILL_MAX, state['skill'] + SKILL_GAIN)
                fruit.goto(random_free_spot())

        render()
        draw_hud()
        wn.update()
        wn.ontimer(loop, 16)

    loop()