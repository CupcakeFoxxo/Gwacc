import time
import random

compilerPhrases = [
    'i did 1 (one) compilies owo',
    'Unbuilding build failures...',
    'Installing 99 TB of GCC configuration files: 99.999%',
    'Processing 4D hyper-sparse matrices through convolutional neural networks',
    'Just compiler things™',
    'Very important stuff happening right now',
    'I\'m almost done i promise',
    'Removing bugs with off and raid (other brands are available)',
    'Almost finished downloading the build instructions for installing the dependencies needed for building.',
    'Time traveling to install Node 2040 Professional Edition',
]

if __name__ == '__main__':
    for index in range(50):
        print(compilerPhrases[random.randrange(len(compilerPhrases))])
        time.sleep(1)