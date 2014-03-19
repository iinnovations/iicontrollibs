#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2014, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"


# This script handles spi read functions 
# We use SPIdev0, because this is what is physically
# connected on the cupid control

import os
import time
import pilib

querylist = [];

########################################
# Read Thermocouple temperature. Clearly 
# we need to have a selector for what to 
# read/write on our SPI interface

def readspitc():
    valuedict = {}
    valuedict['SPITC1'] = getspitctemp().rstrip()
    return valuedict


def getspitctemp():
    import subprocess

    tctemp = subprocess.check_output(['python3', '/usr/lib/iicontrollibs/cupid/max31855-1.0/getmaxtemp.py'])
    return tctemp


def recordspidata(database, valuedict):
    # This is incomplete and hardcoded partially
    querylist = []
    for key, value in valuedict.iteritems():
        querylist.append(pilib.makesqliteinsert('inputsdata',
                                                valuelist=[key, 'SPI1', 'TC', '1', value, 'F', pilib.gettimestring(), 1,
                                                           key]))
        querylist.append(pilib.makesqliteinsert('ioinfo', valuelist=[key, key]))
    pilib.sqlitemultquery(database, querylist)


if __name__ == "__main__":
    from pilib import controldatabase
    valuedict = readspitc()
    recordspidata(controldatabase, valuedict)
    print(valuedict)
