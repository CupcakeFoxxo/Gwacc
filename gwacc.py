import curses
import threading
import subprocess

gameWindowSizeX = 10
gameWindowSizeY = 10

buildOutputSizeY = 3

windowMargin = 3 # Number of lines between the two windows

buildOutput = [] # List of each line from build output

def readBuildOutput():
    # Setup build process
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
        gameWindow = curses.newwin(gameWindowSizeY, gameWindowSizeX, buildOutputSizeY + windowMargin, 0)
        return (buildWindow, gameWindow)

    (buildWindow, gameWindow) = setupWindows()

    buildThread = threading.Thread(target=readBuildOutput)
    buildThread.start()

    # Main loop
    while buildThread.is_alive():
        fullscreen.refresh()

        # Handle game update
        inputKey = fullscreen.getch()
        if inputKey == curses.KEY_RESIZE:
            (buildWindow, gameWindow) = setupWindows(resize=True)
        gameWindow.clear()
        gameWindow.addch('G')
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