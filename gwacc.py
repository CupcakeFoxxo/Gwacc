import curses
import threading
import subprocess

# Constants
gameWindowSize = (10, 10)
buildOutputSizeY = 3
windowMargin = 3 # Number of lines between the two windows

# Globals
buildOutput = [] # List of each line from build output

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
    characterPosition = [0, 0]

    # Main loop
    while buildThread.is_alive():
        fullscreen.refresh()

        # Handle game update
        inputKey = fullscreen.getch()
        if inputKey == curses.KEY_RESIZE:
            (buildWindow, gameWindow) = setupWindows(resize=True)
        elif inputKey == ord('a'):
            characterPosition[0] -= 1
        elif inputKey == ord('d'):
            characterPosition[0] += 1
        elif inputKey == ord('w'):
            characterPosition[1] -= 1
        elif inputKey == ord('s'):
            characterPosition[1] += 1

        def clamp(value, minimum, maximum):
            return max(minimum, min(maximum, value))

        for dimension in range(2):
            characterPosition[dimension] = clamp(characterPosition[dimension], 0, gameWindowSize[dimension] - 1)

        gameWindow.clear()
        gameWindow.addch(characterPosition[1], characterPosition[0], 'G')
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