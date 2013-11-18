#!/usr/bin/env python

import os
import sys
import math
import pilib
import controllib 
import RPi.GPIO as GPIO
from time import sleep
 
T=True
F=False
GPIO.setmode(GPIO.BCM)

outputs=[18,23,24,25]
for output in outputs:
    GPIO.setup(int(output), GPIO.OUT)    

approve=raw_input("are you sure you want to turn on the outputs? This could have bad consequences (type yes to continue)")

while approve=='yes':
   for output in outputs:
       GPIO.output(int(output), T)
   sleep(10)


