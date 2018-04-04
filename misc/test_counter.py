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


class io_wrapper(object):

    """
    This is going to be a general class of IO handler that has a identifying values to match against (to know when we
    need to destroy and recreate it), and can handle functions in the background, such as pigpiod callbacks. This way
    we can do more than atomic read/write operations. For GPIO, we can even set callbacks for value changes.
    """
    def __init__(self, **kwargs):
        # self.required_properties = ['type','options', 'pi']
        self.required_properties = ['pi']

        if not all(property in kwargs for property in self.required_properties):
            print('You did not provide all required parameters: ' + str(self.required_properties))
        self.settings = {}
        self.settings.update(kwargs)
        for key,value in self.settings.items():
            setattr(self, key, value)


class pigpiod_gpio_counter(io_wrapper):

    def __init__(self, **kwargs):
        import copy
        # inherit parent properties
        super(pigpiod_gpio_counter, self).__init__(**kwargs)

        import pigpio
        self.settings = {'edge':'falling', 'pullupdown':None, 'debounce_ms':20, 'event_min_ms':20,
                         'watchdog_ms':1000, 'rate_period_ms':2000, 'debug':False, 'reset_ticks':30000, 'init_counts':0}
        self.settings.update(kwargs)
        for key,value in self.settings.items():
            setattr(self, key, value)

        self.pi.set_mode(self.gpio, pigpio.INPUT)
        if self.pullupdown in ['up', 'pullup']:
            self.pi.set_pull_up_down(self.gpio, pigpio.PUD_UP)

        self._cb = self.pi.callback(self.gpio, pigpio.FALLING_EDGE, self._cbf)
        self.pi.set_watchdog(self.gpio, self.watchdog_ms)

        self.busy = False
        self.ticks = copy.copy(self.settings['init_counts'])
        self.last_event_count = 0

        self.last_counts = copy.copy(self.settings['init_counts'])
        if self.settings['init_counts']:
            from datetime import datetime
            self.last_counts_time = datetime.now()
        else:
            self.last_counts_time = None
        self.rate = 0

    def _cbf(self, gpio, level, tick):
        if not self.busy:
            self.busy = True
            self.process_callback(gpio, level, tick)

    def process_callback(self, gpio, level, tick):
        # a tick event happened
        import time

        if level == 0:  # Falling edge
            time.sleep(0.001 * self.debounce_ms)
            value = self.pi.read(self.gpio)
            if value == 0:
                # print('event length satisfied')

                if tick - self.last_event_count > self.debounce_ms * 1000:
                    self.ticks += 1
                    self.last_event_count = tick
                else:
                    if self.debug:
                        print('debounce')
            else:
                # print('event not long enough ( we waited to see ).')
                pass

        elif level == 2:  # Watchdog timeout. We will calculate
            pass

        self.busy = False

    def get_value(self):
        from datetime import datetime
        now = datetime.now()
        if self.last_counts_time:
            seconds_delta = now - self.last_counts_time
            seconds_passed = seconds_delta.seconds + float(seconds_delta.microseconds) / 1000000
            self.rate = float(self.ticks - self.last_counts) / seconds_passed
            if self.debug:
                print('COUNTING RATE')
                print(self.last_counts, self.ticks)

        self.last_counts = self.ticks
        self.last_counts_time = now

        if self.ticks > self.reset_ticks:
            if self.debug:
                print('RESETTING (count is ' + str(self.ticks) + ')')
                print('reset_ticks : ' + str(self.reset_ticks))
            self.last_counts -= self.reset_ticks
            self.ticks -= self.reset_ticks
        # self.event_tick = 0  # reset event
        return self.ticks

    def get_rate(self):

        return self.rate


class pigpiod_gpio_output(io_wrapper):
    def __init__(self, **kwargs):
        # inherit parent properties
        super(pigpiod_gpio_output, self).__init__(**kwargs)

        import pigpio
        self.settings = {}
        self.settings.update(kwargs)

        for key, value in self.settings.items():
            setattr(self, key, value)

        self.pi.set_mode(self.gpio, pigpio.OUTPUT)

    def get_value(self):
        self.pi.read(self.gpio)

    def set_value(self, value):
        self.pi.write(self.gpio, value)


def test_counter(gpio_address=22, run_sim=False, **kwargs):
    from time import sleep
    import pigpio
    pi = pigpio.pi()

    options = {'init_counts':0, 'read_period_s':5, 'debug':True, 'run_counter':True}
    options.update(kwargs)

    read_counter = 0

    if run_sim:
        my_gpio_output = pigpiod_gpio_output(**{'pi':pi, 'gpio':gpio_address})
        my_gpio_output.set_value(0)
        on_period = 50
        off_period = 50 # ms
        toggle_counter = 0

    if options['run_counter']:
        my_counter = pigpiod_gpio_counter(**{'gpio': gpio_address, 'pi': pi, 'type': 'counter', 'reset_ticks': 20000,
                                         'init_counts': int(options['init_counts'])})
    from datetime import datetime
    import time
    now = datetime.now()

    counter_read_time = now
    start_time=now

    try:
        while True:
            if run_sim:
                # print('on \t\t' + str(counter))
                my_gpio_output.set_value(1)
                sleep(float(on_period) / 1000)
                # print('off')
                my_gpio_output.set_value(0)
                sleep(float(off_period) / 1000)
                toggle_counter += 1

            if options['run_counter']:
                now = datetime.now()
                if (now - counter_read_time).total_seconds() > options['read_period_s'] or read_counter == 0:
                    read_counter += 1

                    print(time.strftime('%Y-%m-%d %H:%M:%S') + ' : (' + str((now-start_time).total_seconds()) + 's, ' + str(read_counter) + ' reads)')
                    print('\t Counter value : ' + str(my_counter.get_value()))
                    print(time.strftime('\t Rate value : ' + str(my_counter.get_rate())))

                    counter_read_time = now


    except KeyboardInterrupt:
        print('Exiting on keyboard interrupt ...')
        pi.stop()

if __name__ == "__main__":
    # test_counter(gpio_address=27, run_sim=True)
    # test_counter(gpio_address=22, run_sim=False)
    test_counter(gpio_address=27, run_sim=True, run_counter=False)
