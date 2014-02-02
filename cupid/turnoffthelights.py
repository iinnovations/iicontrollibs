#!/usr/bin/env python

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
