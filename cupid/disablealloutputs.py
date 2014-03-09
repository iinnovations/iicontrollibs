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
