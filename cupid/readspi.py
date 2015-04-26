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


def recordspidata(database, valuedict, execute=False):
    # This is incomplete and hardcoded partially
    querylist = []
    for key, value in valuedict.iteritems():
        querylist.append(pilib.makesqliteinsert('inputs',
                                                valuelist=[key, 'SPI1', 'TC', '1', 'SPITC1', value, 'F', pilib.gettimestring(), 1,
                                                           '','']))
        querylist.append(pilib.makesqliteinsert('ioinfo', valuelist=[key, key, '']))
    if execute:
        pilib.sqlitemultquery(database, querylist)

    return querylist


def getMAX31855tctemp(CS=1):
    try:
        import Adafruit_GPIO.SPI as SPI
        import Adafruit_MAX31855.MAX31855 as MAX31855
    except:
        print('Libraries are not installed!')

    SPI_PORT   = CS
    SPI_DEVICE = 0
    sensor = MAX31855.MAX31855(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))
    temp = sensor.readTempC()
    return temp

if __name__ == "__main__":
    from pilib import controldatabase
    valuedict = readspitc()
    recordspidata(controldatabase, valuedict)
    print(valuedict)
