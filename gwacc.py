import curses
import threading
import subprocess
import time
import enum

# Constants
buildOutputSizeY = 3
windowMargin = 3 # Number of lines between the two windows

gameWindowSize = (20, 10)
heroPositionY = gameWindowSize[1] - 1
enemyHordeSize = (10, 3)
def enemyHordeRange(dimension): return (0, (gameWindowSize[dimension] - 1) - (enemyHordeSize[dimension] - 1))
enemyHordeRangeX = enemyHordeRange(0)
enemyHordeRangeY = enemyHordeRange(1)
gameUpdateRate = 1. / 30 # 30 FPS
enemyAnimation = ('Y', 'T')

# Speeds are measured in the number of frames between position updates
enemyHordeSpeed = 10
bulletSpeed = 4
heroFireSpeed = 10

# Globals
buildOutput = [] # List of each line from build output

# Game Types
class Enemy:
    def __init__(self, positionX, positionY):
        self.position = self.initialPosition = [positionX, positionY]
        self.isAlive = True

    def setPositionFromHordePosition(self, hordePosition):
        self.position = [self.initialPosition[0] + hordePosition[0], self.initialPosition[1] + hordePosition[1]]

class Bullet:
    def __init__(self, positionX, positionY, lastUpdateFrame):
        self.position = [positionX, positionY]
        self.lastUpdateFrame = lastUpdateFrame
        self.isAlive = True

class GameOutcome(enum.Enum):
    playing = 0
    lost = 1
    won = 2

# Utilities
def samePosition(position0, position1):
    return position0[0] == position1[0] and position0[1] == position1[1]

def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))

# We read the build output in a separate thread to avoid blocking on readline
def readBuildOutput():
    buildProcess = subprocess.Popen(['python', '-u', 'fakeCompiler.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    while True:
        buildLine = buildProcess.stdout.readline()
        if buildLine:
            buildOutput.append(buildLine.decode('utf-8').strip())
        # Break if build is finished
        if buildProcess.poll() is not None:
            break

def main(fullscreen):
    fullscreen.nodelay(True) # Don't block when getting input
    curses.curs_set(0) # Hide cursor

    # Divide terminal into two windows
    buildWindow = None
    gameWindow = None
    def setupWindows(resize=False):
        (sizeY, sizeX) = fullscreen.getmaxyx()
        if resize:
            curses.resize_term(sizeY, sizeX)

        # TODO: make sure we have enough space and prompt to resize terminal if not
        buildWindow = curses.newwin(buildOutputSizeY, sizeX, 0, 0)
        gameWindow = curses.newwin(gameWindowSize[1] + 2, gameWindowSize[0] + 2, buildOutputSizeY + windowMargin, 0)
        return (buildWindow, gameWindow)

    (buildWindow, gameWindow) = setupWindows()

    buildThread = threading.Thread(target=readBuildOutput)
    buildThread.start()

    # Game variables
    lastGameUpdateTime = time.time()
    frameCounter = 0

    gameOutcome = GameOutcome.playing

    heroPositionX = 0
    heroBullets = []
    heroLastFireFrame = -heroFireSpeed

    enemyHorde = []
    enemyHordePosition = [0, 0]
    enemyHordeDirection = 1
    enemyHordeLastUpdateFrame = 0
    enemyAnimationIndex = 0

    explosions = []

    # Setup horde positions
    for enemyX in range(enemyHordeSize[0]):
        for enemyY in range(enemyHordeSize[1]):
            newEnemy = Enemy(enemyX, enemyY)
            enemyHorde.append(newEnemy)

    # Main loop
    while buildThread.is_alive():
        # Print last buildOutputSizeY lines of build output
        buildWindow.clear()
        for outputLineIndex in range(buildOutputSizeY):
            buildOutputLineIndex = len(buildOutput) - (buildOutputSizeY - outputLineIndex)
            if buildOutputLineIndex >= 0:
                buildWindow.addstr(outputLineIndex, 0, buildOutput[buildOutputLineIndex])
        buildWindow.refresh()

        currentTime = time.time()
        deltaTime = currentTime - lastGameUpdateTime
        if gameOutcome == GameOutcome.playing and deltaTime >= gameUpdateRate:
            lastGameUpdateTime = currentTime
            frameCounter += 1

            # Handle controls
            inputKey = fullscreen.getch()
            if inputKey == curses.KEY_RESIZE:
                (buildWindow, gameWindow) = setupWindows(resize=True)
            elif inputKey == ord('a'):
                heroPositionX -= 1
            elif inputKey == ord('d'):
                heroPositionX += 1
            elif inputKey == ord(' '):
                if frameCounter - heroLastFireFrame >= heroFireSpeed:
                    heroLastFireFrame = frameCounter
                    newBullet = Bullet(heroPositionX, gameWindowSize[1] - 2, frameCounter)
                    heroBullets.append(newBullet)
            elif inputKey == ord('i'):
                # Quit game
                gameOutcome = GameOutcome.lost
                break

            # Update and render game
            heroPositionX = clamp(heroPositionX, 0, gameWindowSize[0] - 1)
            for enemy in enemyHorde:
                enemy.setPositionFromHordePosition(enemyHordePosition)
                for bullet in heroBullets:
                    if samePosition(enemy.position, bullet.position):
                        enemy.isAlive = bullet.isAlive = False
                        explosions.append(enemy.position)
                if enemy.isAlive and enemy.position[1] >= heroPositionY:
                    gameOutcome = GameOutcome.lost

            # Move the horde
            if frameCounter - enemyHordeLastUpdateFrame >= enemyHordeSpeed:
                explosions = []
                enemyAnimationIndex += 1
                enemyHordeLastUpdateFrame = frameCounter
                enemyHordePosition[0] += enemyHordeDirection
                enemyHordeRangeX = enemyHordeRange(0)
                if enemyHordeDirection == 1 and enemyHordePosition[0] == enemyHordeRangeX[1]:
                    enemyHordeDirection = -1
                elif enemyHordeDirection == -1 and enemyHordePosition[0] == enemyHordeRangeX[0]:
                    enemyHordeDirection = 1
                    # Go down one row since we hit the left wall
                    enemyHordePosition[1] += 1

            # Move bullets
            for bullet in heroBullets:
                if frameCounter - bullet.lastUpdateFrame >= bulletSpeed:
                    bullet.lastUpdateFrame = frameCounter
                    bullet.position[1] -= 1
                    if bullet.position[1] < 0:
                        bullet.isAlive = False

            # Remove dead entities
            enemyHorde = [enemy for enemy in enemyHorde if enemy.isAlive]
            heroBullets = [bullet for bullet in heroBullets if bullet.isAlive]

            if not enemyHorde:
                gameOutcome = GameOutcome.won

            gameWindow.clear()
            gameWindow.border('|', '|', '-', '-', '+', '+', '+', '+')
            if gameOutcome == GameOutcome.playing:
                # Render based on game map coordinates with 0, 0 being top-left
                def render(character, position):
                    gameWindow.addch(position[1] + 1, position[0] + 1, character)
                for enemy in enemyHorde:
                    render(enemyAnimation[enemyAnimationIndex % len(enemyAnimation)], enemy.position)
                for bullet in heroBullets:
                    render('^', bullet.position)
                for explosion in explosions:
                    render('*', explosion)
                render('S', [heroPositionX, heroPositionY])
            else:
                gameWindow.addstr(1, 1, 'You {}!!!'.format('lost' if gameOutcome == GameOutcome.lost else 'won'))

            gameWindow.refresh()

    curses.endwin()

    # Output full build
    for line in buildOutput:
        print(line)

    if gameOutcome == GameOutcome.lost:
        print('\n\nYou lost :(')
    else:
        print('\n\nYou won!! :D')

if __name__ == '__main__':
    curses.wrapper(main)