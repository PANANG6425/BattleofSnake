"""
rules.py - combat, pickups and win conditions. No drawing happens here.

Attack rules (identical for both players, evaluated in both directions each frame):
    head -> enemy head  : enemy loses 1 HP, enemy score -50%
    head -> enemy tail  : enemy loses 1 HP, enemy score -50%
    head -> enemy body  : the ATTACKER loses 1 HP, attacker score -50%
"""

from config import (HIT_RADIUS, SELF_HIT_RADIUS, SELF_SKIP_SEGMENTS, # Collision tuning
                    STUN_FRAMES, INVULN_FRAMES, SELF_HIT_COOLDOWN,   # Timers
                    SCORE_PENALTY, FRUIT_SCORE, SKILL_GAIN,          # Scoring
                    GROW_PER_FRUIT, TARGET_SCORE)
import effects                                  # Particle bursts
import fruit                                    # The fruit list and respawn helpers
from sounds import sfx                          # Sound effects


def apply_damage(victim):                       # Deal 1 HP and halve the score, once per immunity window
    if victim.invuln > 0:                       # Still immune from the last hit
        return False                            # No damage dealt
    victim.hp -= 1                              # Remove one heart
    victim.score = int(victim.score * SCORE_PENALTY) # Apply the score penalty
    victim.invuln = INVULN_FRAMES               # Start the immunity window
    victim.stun = STUN_FRAMES                   # Brief freeze as knockback feedback
    sfx.play('hit')                             # Sound feedback
    effects.burst_hit(victim.head.xcor(), victim.head.ycor()) # Visual feedback
    return True                                 # Damage dealt


def resolve_attacks(attacker, defender):        # One attacker / defender ordering, called both ways
    if attacker.hp <= 0 or defender.hp <= 0:    # Match already decided
        return
    head = attacker.head                        # Shorthand

    if head.distance(defender.head) < HIT_RADIUS:  # RULE: head hits enemy head
        apply_damage(defender)                  # Defender is punished
        return                                  # One hit per ordering per frame

    segs = defender.segments()                  # Cached defender segments (tail last)
    if not segs:                                # Body not formed yet
        return

    if head.distance(segs[-1]) < HIT_RADIUS:    # RULE: head hits enemy tail
        apply_damage(defender)                  # Defender is punished
        return

    for pos in segs[:-1]:                       # RULE: head hits enemy body -> attacker is punished
        if head.distance(pos) < HIT_RADIUS:     # Crashed into the midsection
            apply_damage(attacker)              # Attacker is punished instead
            return


def resolve_self_collision(snake):              # Biting yourself stuns you - it never kills
    if snake.self_hit_cd > 0:                   # Cooldown still running
        return                                  # Cannot be stunned by itself again yet
    segs = snake.segments()                      # Cached segments
    for pos in segs[SELF_SKIP_SEGMENTS:]:       # Skip the segments right behind the head
        if snake.head.distance(pos) < SELF_HIT_RADIUS: # Head overlaps an older part of the body
            # IMPORTANT: `direction` is deliberately NOT cleared here.
            # Clearing it left the head parked inside its own body, and every attempt to
            # move re-triggered this check - the "eat your own tail and the player is
            # dead forever" bug. Keeping the direction plus SELF_HIT_COOLDOWN (longer
            # than STUN_FRAMES) guarantees the snake drives out of its own body.
            snake.stun = STUN_FRAMES            # Brief freeze
            snake.self_hit_cd = SELF_HIT_COOLDOWN # Cannot re-trigger until it has moved clear
            sfx.play('bump')                    # Sound feedback
            effects.burst_bump(snake.head.xcor(), snake.head.ycor()) # Visual feedback
            return                              # One self-hit per frame


def resolve_fruit(snake, players):              # Fruit pickup for one snake
    for f in fruit.fruits:                      # Check every fruit on the field
        if snake.head.distance(f) < 18:         # Close enough to eat
            snake.score += FRUIT_SCORE          # Add score
            snake.length += GROW_PER_FRUIT      # Grow the body
            snake.gain_skill(SKILL_GAIN)        # Charge the skill bar
            sfx.play('eat')                     # Sound feedback
            effects.burst_eat(f.xcor(), f.ycor()) # Visual feedback at the fruit
            fruit.respawn(f, players)           # Move the fruit somewhere else


def check_win(p1, p2):                          # Return the winning Snake, 'draw', or None
    if p1.hp <= 0 and p2.hp <= 0:               # Both out of hearts on the same frame
        return 'draw'
    if p1.hp <= 0:                              # P1 is out
        return p2
    if p2.hp <= 0:                              # P2 is out
        return p1
    if p1.score >= TARGET_SCORE and p2.score >= TARGET_SCORE: # Both crossed the target together
        if p1.score == p2.score:                # Exactly equal
            return 'draw'
        return p1 if p1.score > p2.score else p2 # Higher score wins
    if p1.score >= TARGET_SCORE:                # P1 reached the target
        return p1
    if p2.score >= TARGET_SCORE:                # P2 reached the target
        return p2
    return None                                 # Match continues
