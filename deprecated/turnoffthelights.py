#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2014, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

import os
import sys
import math
import pilib
import controllib 
import spilights
import RPi.GPIO as GPIO
from time import sleep
 
T=True
F=False
GPIO.setmode(GPIO.BCM)

outputs=[18,23,24,25]
for output in outputs:
    GPIO.setup(int(output), GPIO.OUT)    
    GPIO.output(int(output), F)

spilights.setspilightsoff()
