import curses
import threading
import subprocess

# Constants
buildOutputSizeY = 3
windowMargin = 3 # Number of lines between the two windows

gameWindowSize = (15, 15)
enemyHordeSize = (10, 3)
def enemyHordeRange(dimension): return (0, gameWindowSize[dimension] - 1 - enemyHordeSize[dimension] - 1)

# Globals
buildOutput = [] # List of each line from build output

# Game Types
class Enemy:
    def __init__(self, positionX, positionY):
        self.initialPosition = [positionX, positionY]
        self.animation = ['I', 'Y']
        self.animationIndex = 0
        self.isAlive = True

# Utilities
def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))

# We read the build output in a separate thread to avoid blocking on readline
def readBuildOutput():
    buildProcess = subprocess.Popen('python -u fakeCompiler.py', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    while True:
        buildLine = buildProcess.stdout.readline()
        if buildLine:
            buildOutput.append(buildLine.decode('utf-8').strip())
        # Break if build is finished
        if buildProcess.poll() is not None:
            break

def main(fullscreen):
    fullscreen.clear()
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
        gameWindow = curses.newwin(gameWindowSize[1], gameWindowSize[0] + 1, buildOutputSizeY + windowMargin, 0)
        return (buildWindow, gameWindow)

    (buildWindow, gameWindow) = setupWindows()

    buildThread = threading.Thread(target=readBuildOutput)
    buildThread.start()

    # Game variables
    characterPositionX = 0
    enemyHorde = []
    enemyHordePosition = [0, 0]
    enemyHordeDirection = 1
    for enemyX in range(enemyHordeSize[0]):
        for enemyY in range(enemyHordeSize[1]):
            newEnemy = Enemy(enemyX, enemyY)
            enemyHorde.append(newEnemy)

    # Main loop
    while buildThread.is_alive():
        # Update game state
        inputKey = fullscreen.getch()
        if inputKey == curses.KEY_RESIZE:
            (buildWindow, gameWindow) = setupWindows(resize=True)
        elif inputKey == ord('a'):
            characterPositionX -= 1
        elif inputKey == ord('d'):
            characterPositionX += 1
        elif inputKey == ord(' '):
            pass # TODO: fire

        characterPositionX = clamp(characterPositionX, 0, gameWindowSize[0] - 1)
        enemyHorde = [enemy for enemy in enemyHorde if enemy.isAlive]

        #enemyHorde
        #for enemy in enemyHorde:


        # Render
        gameWindow.clear()
        for enemy in enemyHorde:
            gameWindow.addch(enemy.initialPosition[1] + enemyHordePosition[1], enemy.initialPosition[0] + enemyHordePosition[0], 'Y')
        gameWindow.addch(gameWindowSize[1] - 1, characterPositionX, 'S')
        gameWindow.refresh()

        # Print last 3 lines of build output
        buildWindow.clear()
        for outputLineIndex in range(3):
            buildOutputLineIndex = len(buildOutput) - buildOutputSizeY - outputLineIndex
            if buildOutputLineIndex >= 0:
                buildWindow.addstr(outputLineIndex, 0, buildOutput[buildOutputLineIndex])
        buildWindow.refresh()

    curses.endwin()

    # Output full build
    for line in buildOutput:
        print(line)

    print('\n\nYou might have won!')

if __name__ == '__main__':
    curses.wrapper(main)