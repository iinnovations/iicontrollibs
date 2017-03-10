#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2016, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

import os
import sys
import inspect

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)


def test_counter(gpio=22):
    from time import sleep
    from cupid import pilib
    import pigpio
    pi = pigpio.pi()
    my_gpio_output = pilib.pigpiod_gpio_output(**{'pi':pi, 'gpio':22})
    my_gpio_output.set_value(0)
    on_period = 50
    off_period = 50 # ms
    counter = 0
    try:
        while True:
            counter += 1
            print('on \t\t' + str(counter))
            my_gpio_output.set_value(1)
            sleep(float(on_period) / 1000)
            print('off')
            my_gpio_output.set_value(0)
            sleep(float(off_period) / 1000)

    except KeyboardInterrupt:
        print('Exiting on keyboard interrupt ...')
        pi.stop()

if __name__ == "__main__":
    test_counter()
