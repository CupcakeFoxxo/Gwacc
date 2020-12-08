from curses import wrapper

def main(fullscreen):
    # Clear screen
    fullscreen.clear()

    # This raises ZeroDivisionError when i == 10.
    for i in range(0, 11):
        v = i-10
        if i != 10:
            fullscreen.addstr(i, 0, '10 divided by {} is {}'.format(v, 10/v))

    fullscreen.refresh()
    fullscreen.getkey()

if __name__ == '__main__':
    wrapper(main)