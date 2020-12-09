import curses
import threading
import subprocess

gameWindowSizeX = 10
gameWindowSizeY = 10

buildOutputSizeY = 3

def main(fullscreen):
    fullscreen.clear()
    fullscreen.nodelay(True) # Don't block when getting input

    # Divide terminal into two windows
    buildWindow = None
    gameWindow = None
    def setupWindows(resize=False):
        (sizeY, sizeX) = fullscreen.getmaxyx()
        if resize:
            curses.resize_term(*fullscreen.getmaxyx())

        # TODO: make sure we have enough space and prompt to resize terminal if not
        buildWindow = curses.newwin(buildOutputSizeY, sizeX, 0, 0)
        gameWindow = curses.newwin(gameWindowSizeY, gameWindowSizeX, buildOutputSizeY, 0)
        return (buildWindow, gameWindow)

    (buildWindow, gameWindow) = setupWindows()

    # Setup build process
    buildProcess = subprocess.Popen('python fakeCompiler.py', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    buildOutput = []

    # Main loop
    while True:
        # Handle game update
        inputKey = fullscreen.getch()
        if inputKey == curses.KEY_RESIZE:
            setupWindows(resize=True)
        gameWindow.clear()
        gameWindow.addch('G')
        gameWindow.refresh()

        # Handle build output
        buildLine = buildProcess.stdout.readline()
        if buildLine:
            buildOutput.append(buildLine.decode('utf-8').strip())

        # Print last 3 lines of build output
        buildWindow.clear()
        for outputLineIndex in range(3):
            buildOutputLineIndex = len(buildOutput) - buildOutputSizeY - outputLineIndex
            if buildOutputLineIndex >= 0:
                buildWindow.addstr(outputLineIndex, 0, buildOutput[buildOutputLineIndex])
        buildWindow.refresh()

        # Break if build is finished
        if buildProcess.poll() is not None:
            break

    # Output full build
    for line in buildOutput:
        print(line)

    print('\n\nYou might have won!')

if __name__ == '__main__':
    curses.wrapper(main)