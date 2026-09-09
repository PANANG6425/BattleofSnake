import turtle # Import the turtle graphics module for drawing and window handling

# ===========================================
# SECTION 1: SCREEN SETUP
# ===========================================
wn = turtle.Screen()                          # Create the main game window
wn.title('TRON Snake - Single Player Starter Kit') # Set title displayed on window title bar
wn.bgcolor('black')                           # Set background color of window to black
wn.setup(width=800, height=600)               # Set window dimensions (width = 800px, height = 600px)
wn.tracer(0)                                  # Turn off auto screen updates to enable smooth frame rendering

# Loop control flag (True: game is active, False: game is stopped)
game_active = True                            # Initialize state variable to track if game is running

# ===========================================
# SECTION 2: GAME ENTITIES
# ===========================================
# ARENA BOUNDARIES (4 Outer Walls)
border = turtle.Turtle()                      # Instantiate Turtle object for drawing arena boundaries
border.color('gray')                          # Set wall border color to gray
border.pensize(6)                             # Set line thickness of boundary walls to 6 pixels
border.penup()                                # Lift pen to move to starting corner without drawing
border.goto(-380, 280)                        # Position pen at top-left corner of the arena (x=-380, y=280)
border.pendown()                              # Lower pen to begin drawing outer walls
# Draw the 4 rectangular outer walls
for _ in range(2):                            # Loop twice to draw two pairs of equal sides
    border.forward(760)                       # Draw top/bottom horizontal wall (width = 760px)
    border.right(90)                          # Turn pen right 90 degrees
    border.forward(560)                       # Draw right/left vertical wall (height = 560px)
    border.right(90)                          # Turn pen right 90 degrees
border.hideturtle()                           # Hide wall-drawing cursor graphics for clean look

# PLAYER (TRON Light Cycle)
p1 = turtle.Turtle()                          # Instantiate Turtle object for player 1
p1.shape('square')                            # Set player shape to square
p1.color('cyan')                              # Set player color to cyan (classic TRON color)
p1.shapesize(0.8, 0.8)                        # Scale player size down to 16x16 pixels
p1.penup()                                    # Lift pen so player object moves cleanly without default line
p1.goto(0, 0)                                 # Start player at center of the grid (x=0, y=0)

# Configure the TRON light-trail effect
p1.pensize(10)                                # Set trail wall thickness to 10 pixels
p1.pendown()                                  # Lower pen so the snake leaves a trail line as it moves
tail_positions = []                           # List to store light-trail coordinates [(x, y), ...]

# ===========================================
# SECTION 3: PARAMETERS & PHYSICS
# ===========================================
p1.speed_val = 3                              # Movement speed of player in pixels per frame
p1.direction = 'stop'                         # Initial movement direction state

# ===========================================
# SECTION 4: INPUT HANDLING
# ===========================================
def go_up():                                  # Callback function to change direction upward
    if p1.direction != 'down':                # Prevent 180-degree self-collision reversal
        p1.direction = 'up'                   # Update direction to 'up'

def go_down():                                # Callback function to change direction downward
    if p1.direction != 'up':                  # Prevent 180-degree self-collision reversal
        p1.direction = 'down'                 # Update direction to 'down'

def go_left():                                # Callback function to change direction leftward
    if p1.direction != 'right':               # Prevent 180-degree self-collision reversal
        p1.direction = 'left'                 # Update direction to 'left'

def go_right():                               # Callback function to change direction rightward
    if p1.direction != 'left':                # Prevent 180-degree self-collision reversal
        p1.direction = 'right'                # Update direction to 'right'

wn.listen()                                   # Set screen focus to register user keyboard inputs
wn.onkeypress(go_up, 'Up')                    # Bind Up Arrow key press to execute go_up()
wn.onkeypress(go_down, 'Down')                # Bind Down Arrow key press to execute go_down()
wn.onkeypress(go_left, 'Left')                # Bind Left Arrow key press to execute go_left()
wn.onkeypress(go_right, 'Right')              # Bind Right Arrow key press to execute go_right()

# ===========================================
# SECTION 5: MAIN GAME LOOP
# ===========================================
def game_loop():                              # Primary function executing every game tick (~60 FPS)
    global game_active                        # Access global active flag to check game state
    if not game_active:                       # Stop executing loop iterations if game is over
        return

    # Continuous movement based on direction
    if p1.direction != 'stop':                # Execute movement logic only if player has started moving
        # Save current position tuple to trail list (FIXED: added inner parenthesis to form tuple)
        tail_positions.append((round(p1.xcor()), round(p1.ycor())))

        if p1.direction == 'up':              # If moving up
            p1.sety(p1.ycor() + p1.speed_val) # Increase Y coordinate by speed value
        elif p1.direction == 'down':          # If moving down
            p1.sety(p1.ycor() - p1.speed_val) # Decrease Y coordinate by speed value
        elif p1.direction == 'left':          # If moving left
            p1.setx(p1.xcor() - p1.speed_val) # Decrease X coordinate by speed value
        elif p1.direction == 'right':         # If moving right
            p1.setx(p1.xcor() + p1.speed_val) # Increase X coordinate by speed value

        # Boundary collision detection (Outer Walls)
        x, y = p1.xcor(), p1.ycor()           # Get current x and y positions of player head
        if x > 375 or x < -375 or y > 275 or y < -275: # Check if player hits boundary walls
            game_over()                       # Trigger game over sequence
            return                            # Exit game loop iteration immediately

        # Trail self-collision detection
        if len(tail_positions) > 15:          # Ignore recent 15 path points behind head to avoid self-collision
            for pos in tail_positions[:-15]:  # Iterate over stored historical trail points
                if p1.distance(pos) < 8:      # Check if player head is within 8 pixels of any old trail segment
                    game_over()               # Trigger game over sequence
                    return                    # Exit game loop iteration immediately

    wn.update()                               # Redraw all screen elements for current frame
    wn.ontimer(game_loop, 16)                 # Schedule next execution of game_loop after 16ms (~60 FPS)

def game_over():                              # Function executing terminal game behavior
    global game_active                        # Access global state variable to modify it
    p1.color('red')                           # Change player color to red indicating collision
    wn.update()                               # Force immediate screen update to show red player

    pen = turtle.Turtle()                     # Instantiate new Turtle object to render Game Over text
    pen.hideturtle()                          # Hide cursor graphics for clean text display
    pen.color('white')                        # Set color of Game Over text to white
    pen.penup()                               # Lift pen before moving position
    pen.goto(0, 0)                            # Center text pen at window origin (x=0, y=0)
    pen.write('GAME OVER!', align='center', font=('Courier', 30, 'bold')) # Draw Game Over banner text

    game_active = False                       # Set global active flag to False stopping main loop

# Game Execution Entry Point
game_loop()                                   # Kickoff initial frame execution of game loop
wn.mainloop()                                 # Start turtle event listener loop to keep window open