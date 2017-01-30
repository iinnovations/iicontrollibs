#!/usr/bin/env python

# read_counter.py
# 2016-01-20
# Public Domain

import time
import pigpio  # http://abyz.co.uk/rpi/pigpio/python.html


class reader:
    """
   A class to read speedometer pulses and calculate the RPM.
   """

    def __init__(self, pi, gpio, pulses_per_rev=1.0, weighting=0.0, min_RPM=5.0):
        """
      Instantiate with the Pi and gpio of the RPM signal
      to monitor.

      Optionally the number of pulses for a complete revolution
      may be specified.  It defaults to 1.

      Optionally a weighting may be specified.  This is a number
      between 0 and 1 and indicates how much the old reading
      affects the new reading.  It defaults to 0 which means
      the old reading has no effect.  This may be used to
      smooth the data.

      Optionally the minimum RPM may be specified.  This is a
      number between 1 and 1000.  It defaults to 5.  An RPM
      less than the minimum RPM returns 0.0.
      """
        self.pi = pi
        self.gpio = gpio
        self.pulses_per_rev = pulses_per_rev

        if min_RPM > 1000.0:
            min_RPM = 1000.0
        elif min_RPM < 1.0:
            min_RPM = 1.0

        self.min_RPM = min_RPM

        self._watchdog = 100  # Milliseconds.

        if weighting < 0.0:
            weighting = 0.0
        elif weighting > 0.99:
            weighting = 0.99

        self._new = 1.0 - weighting  # Weighting for new reading.
        self._old = weighting  # Weighting for old reading.
        self.event_start = 0
        self.last_event_count = 0
        self.ticks = 0
        self._high_tick = None
        self._period = None
        self.busy = False
        self.event_threshold = 50000 # event must last 50ms
        self.debounce = 50000 # event cannot duplicate within this period

        pi.set_mode(gpio, pigpio.INPUT)
        pi.set_pull_up_down(gpio, pigpio.PUD_UP)

        self._cb = pi.callback(gpio, pigpio.FALLING_EDGE, self._cbf)
        pi.set_watchdog(gpio, self._watchdog)

    def _cbf(self, gpio, level, tick):

        if not self.busy: # better t set another function to catch this before here.
            self.busy = True
            # a tick event happened
            if level == 0:  # Falling edge
                time.sleep(0.000001 * self.debounce)
                value = self.pi.read(self.gpio)
                if value == 0:
                    print('event length satisfied')

                    if tick - self.last_event_count > self.debounce:
                        print('** COUNT IT\n')
                        self.ticks += 1
                        self.last_event_count = tick
                    else:
                        print('debounce')
                else:
                    # print('event not long enough ( we waited to see ).')
                    pass

            elif level == 2:  # Watchdog timeout.

                self.event_tick = 0 # reset event

                if self._period is not None:
                    if self._period < 2000000000:
                        self._period += (self._watchdog * 1000)

            self.busy = False

    def get_value(self):
        return self.ticks

    def RPM(self):
        """
      Returns the RPM.
      """
        RPM = 0.0
        if self._period is not None:
            RPM = 60000000.0 / (self._period * self.pulses_per_rev)
            if RPM < self.min_RPM:
                RPM = 0.0

        return RPM

    def cancel(self):
        """
      Cancels the reader and releases resources.
      """
        self.pi.set_watchdog(self.gpio, 0)  # cancel watchdog
        self._cb.cancel()


if __name__ == "__main__":

    import time
    import pigpio
    import read_counter

    RPM_GPIO = 22
    RUN_TIME = 300
    SAMPLE_TIME = 0.5

    pi = pigpio.pi()

    io_objects = []

    io_objects.append(read_counter.reader(pi, RPM_GPIO))

    start = time.time()

    # for practice, find object with the correct GPIO
    for object in io_objects:
        if object.gpio == RPM_GPIO:
            the_object = object
            break

    try:
        while (time.time() - start) < RUN_TIME:

            time.sleep(SAMPLE_TIME)

            print(the_object.get_value())

            # RPM = p.RPM()
    except KeyboardInterrupt:
        print('BUT YOU INTERRUPTED ME')

        # print("RPM={}".format(int(RPM + 0.5)))
        # print('TICKS: \t' + str(p.ticks))
    the_object.cancel()

    pi.stop()
