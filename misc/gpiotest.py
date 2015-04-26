#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2014, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

import RPi.GPIO as GPIO
from datetime import datetime
import time


gpioaddresses = [18, 23, 24, 25, 4, 17, 21, 22]


def gettimestring(timeinseconds=None):
    import time
    if timeinseconds:
        try:
            timestring = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timeinseconds))
        except TypeError:
            timestring = ''
    else:
        timestring = time.strftime('%Y-%m-%d %H:%M:%S')
    return timestring


def doGpio(address,mode):
    # test redeclare
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(True)
    if mode == 'output':
        print(gettimestring() + ' : \tSetting up GPIO ' + str(address))
        GPIO.setup(address, GPIO.OUT)
        #print(gettimestring() + ' : \tSetting GPIO ' + str(address))
        #GPIO.output(address, False)
        #print(gettimestring() + ' : \tReading GPIO ' + str(address))
        #value = GPIO.input(address)
        #print(gettimestring() + ' : \tValue: ' + str(value))
    else:
        print(gettimestring() + ' : \tSetting GPIO ' + str(address))
        GPIO.setup(address, GPIO.IN)
        print(gettimestring() + ' : \tReading GPIO ' + str(address))
        value = GPIO.input(address)
        print(gettimestring() + ' : \tValue: ' + str(value))

# GPIO.setmode(GPIO.BCM)
# GPIO.setwarnings(False)

cycle = 0
while True:
    print(' ***** Cycle ' + str(cycle) + ' *****')
    cycle += 1
    starttime = datetime.utcnow()

    #if cycle/2:
    if True: 
        mode = 'output'
    else:
        mode = 'input'

    print(gettimestring() + ' : Beginning GPIO set/reads. Mode: ' + mode)
    for address in gpioaddresses:
        doGpio(address, mode)
    print('elapsed time: ' + str((datetime.utcnow()-starttime).total_seconds()))
    #time.sleep(0.1)
