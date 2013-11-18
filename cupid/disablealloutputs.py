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

database = '/var/www/data/controldata.db'
logdatabase = '/var/www/data/logdata.db'

# Kill everything

outputs = pilib.readalldbrows(database,'outputs')

for output in outputs:
    GPIO.setup(int(output['GPIO']), GPIO.OUT)    
    GPIO.output(int(output['GPIO']), F)    

print('all outputs disabled')
