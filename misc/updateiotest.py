#!/usr/bin/env python
import datalib

__author__ = "Colin Reese"
__copyright__ = "Copyright 2014, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"


# do this stuff to access the pilib for sqlite
import os, sys, inspect

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)


from datetime import datetime
import time
from cupid.updateio import updateiodata
import cupid.pilib as pilib

import pigpio
pi = pigpio.pi()

theabsolutestarttime = datetime.utcnow()
cycle = 0
while True:
    print(' ***** Cycle ' + str(cycle) + ' *****')
    cycle += 1
    starttime = datetime.utcnow()
    print(datalib.gettimestring() + ' : Running updateio')
    updateiodata(pilib.controldatabase, piobject=pi)
    print('elapsed time: ' + str((datetime.utcnow()-starttime).total_seconds()))
    print('total elapsed time: ' + str((datetime.utcnow()-theabsolutestarttime).total_seconds()))
    time.sleep(0.1)