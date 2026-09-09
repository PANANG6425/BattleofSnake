"""
main.py - entry point. Wires the modules together, owns the game loop and the flow
between "playing" and "result screen".

Run this file:  python main.py

Import order matters: config has no dependencies, screen creates the one turtle Screen,
and everything else builds on those two. Nothing lower in the chain imports main.
"""

from config import FRAME_MS, FONT, PLAYER_SETUP # Loop timing, font, player definitions
from screen import wn, new_pen                  # The window and the pen helper
import arena                                    # Walls and obstacle boxes
import effects                                  # Particle bursts
import fruit                                    # Fruit pickups
import hud                                      # Stats panel and stun bars
import rules                                    # Combat, pickups and win conditions
from snake import Snake                         # The player entity
from sounds import sfx                          # Sound effects

# ===========================================
# WORLD SETUP
# ===========================================
arena.draw_border()                             # Draw the outer walls once
arena.build_obstacles()                          # Draw the obstacle boxes

players = [Snake(*setup) for setup in PLAYER_SETUP] # Build one Snake per entry in the config
p1, p2 = players                                # Convenient names for the two players

fruit.spawn_fruits(players)                     # Create the fruit pickups
hud.build(players)                              # Create the heart icon pools

game_active = True                              # True while a match is running

# ===========================================
# INPUT
# ===========================================
def bind_keys():                                # Bind every key once at startup
    wn.listen()                                 # Give the window keyboard focus
    for key, direction in (('w', 'up'), ('s', 'down'), ('a', 'left'), ('d', 'right')):
        wn.onkeypress(lambda d=direction: p1.turn(d), key)          # Player 1 steering
    for key, direction in (('Up', 'up'), ('Down', 'down'), ('Left', 'left'), ('Right', 'right')):
        wn.onkeypress(lambda d=direction: p2.turn(d), key)          # Player 2 steering
    wn.onkeypress(p1.use_speed_boost, 'q')      # Player 1 skill 1
    wn.onkeypress(p1.use_invisibility, 'e')     # Player 1 skill 2
    wn.onkeypress(p2.use_speed_boost, 'o')      # Player 2 skill 1
    wn.onkeypress(p2.use_invisibility, 'p')     # Player 2 skill 2
    wn.onkeypress(sfx.toggle, 'm')              # Mute / unmute
    wn.onkeypress(restart, 'r')                 # Restart from the result screen

# ===========================================
# RESULT SCREEN
# ===========================================
_result = new_pen()                             # Pen used only for the result screen

def show_result(winner):                        # End the match and show the result
    global game_active                          # Modify the loop flag
    game_active = False                         # Stop scheduling frames

    for pl in players:                          # Clear the arena so the text reads cleanly
        pl.hide()                               # Hide head and body
    fruit.hide_all()                            # Hide the fruits
    effects.clear()                             # Drop every particle
    hud.clear_overlay()                          # Remove the stun bars
    arena.clear_obstacles()                     # Erase the obstacle boxes

    _result.clear()                             # Wipe any previous result text
    _result.color('white')                      # Heading color
    _result.goto(0, 60)                         # Heading position
    _result.write('RESULT', align='center', font=(FONT, 26, 'bold'))

    if winner == 'draw':                        # Nobody won outright
        _result.goto(0, 15)                     # Outcome position
        _result.write('DRAW!', align='center', font=(FONT, 22, 'bold'))
    else:                                       # One player won
        _result.color(winner.color_main)        # Winner's color
        _result.goto(0, 15)                     # Outcome position
        _result.write('{} WINS!'.format(winner.name), align='center', font=(FONT, 22, 'bold'))
        sfx.play('win')                         # Victory sound

    _result.color('white')                      # Detail line color
    _result.goto(0, -30)                        # Detail line position
    _result.write('P1  score {}  hp {}     |     P2  score {}  hp {}'.format(
        p1.score, max(0, p1.hp), p2.score, max(0, p2.hp)),
        align='center', font=(FONT, 13, 'normal'))
    _result.color('gray')                       # Hint color
    _result.goto(0, -80)                        # Hint position
    _result.write('Press R to play again', align='center', font=(FONT, 12, 'normal'))
    wn.update()                                 # Force an immediate redraw


def restart():                                  # Start a fresh match from the result screen
    global game_active                          # Modify the loop flag
    if game_active:                             # Ignore R while a match is running
        return
    _result.clear()                             # Remove the result text
    arena.build_obstacles()                      # Redraw the obstacle boxes
    for pl in players:                          # Reset both players
        pl.reset()                              # Hearts, score, skill, length, position
    fruit.respawn_all(players)                  # Move and show every fruit
    effects.clear()                             # No leftover particles
    game_active = True                          # Re-enable the loop
    game_loop()                                 # Kick it off again

# ===========================================
# MAIN GAME LOOP
# ===========================================
def game_loop():                                # One frame, then reschedule itself
    global game_active                          # Read the loop flag
    if not game_active:                         # Match is over
        return

    for pl in players:                          # 1. advance state
        pl.tick_timers()                        # Count down stun / immunity / cooldowns / skills
        pl.move()                               # Step the head (blocked moves just do not commit)
        pl.refresh_segments()                   # Recompute body positions ONCE for this frame

    for pl in players:                          # 2. pickups and self collision
        rules.resolve_fruit(pl, players)        # Fruit -> score, growth, skill bar
        rules.resolve_self_collision(pl)        # Own body -> stun, never death

    rules.resolve_attacks(p1, p2)               # 3. combat, evaluated both ways
    rules.resolve_attacks(p2, p1)               # so the rules are symmetric

    for pl in players:                          # 4. draw the world
        pl.render()                             # Body first, head stamped on top
    effects.update_and_draw()                   # Particles above the snakes
    hud.draw_panel(players)                     # Stats panel
    hud.draw_stun_bars(players)                 # Stun bars last, so they float above everything

    winner = rules.check_win(p1, p2)            # 5. win check
    if winner is not None:                      # Someone won or it is a draw
        show_result(winner)                     # Show the result and stop the loop
        return

    wn.update()                                 # Push this frame to the screen
    wn.ontimer(game_loop, FRAME_MS)             # Schedule the next frame


if __name__ == '__main__':                      # Only run the game when executed directly
    bind_keys()                                 # Hook up the keyboard
    print(sfx.status(), '| backend:', sfx.backend) # One line so you can see if audio was found
    game_loop()                                 # First frame
    wn.mainloop()                               # Hand control to turtle's event loop
