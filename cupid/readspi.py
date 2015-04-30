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


def getMAX31855tctemp(CS=0,device=0):
    try:
        import Adafruit_GPIO.SPI as SPI
        import Adafruit_MAX31855.MAX31855 as MAX31855
    except:
        print('Libraries are not installed!')
        return

    SPI_PORT   = CS
    SPI_DEVICE = device
    sensor = MAX31855.MAX31855(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))
    temp = sensor.readTempC()
    return temp


def readspi(CS=0,device=0,**kwargs):

    # import spidev
    import pigpio
    import time
    # spi = spidev.SpiDev() # create spi object
    # spi.open(CS, device) # open spi port 0, device (CS) 1
    from array import array
    import struct

    if 'piobject' in kwargs:
        pi = kwargs['piobject']
    else:
        pi = pigpio.pi()

    if 'numbytes' in kwargs:
        numbytes = kwargs['numbytes']
    else:
        numbytes=1
    if 'speed' in kwargs:
        speed = kwargs['speed']
    else:
        speed=50000

    handle = pi.spi_open(0, 50000, 0)

    resp = pi.spi_read(handle, numbytes)

    responselist = []
    for item in enumerate(resp[1]):
        responselist.append(int(item[1]))

    pi.spi_close(handle)
    if 'piobject' not in kwargs:
        pi.stop()
    return responselist


def convertbytelisttotemp(bytelist):
    from math import pow
    returndict = {}
    numbytes = 4
    sumresponse = 0
    for index, item in enumerate(bytelist):
        # print(int(item))
        # print(int(item) << (8*(numbytes-index-1)))
        sumresponse += int(item) << (8*(numbytes-index-1))
    # print(sumresponse)
    # print('sign: ' + str(sumresponse >> 31))
    sign = sumresponse >> 31
    # print(bin(sumresponse))
    temp = (sumresponse >> 18) & 16383

    # print('temp: ' + bin(temp))
    tctemp = float(temp) / 4
    if sign:
        tctemp -= 16384

    returndict['tctemp'] = tctemp

    # bits 5 through 17 are the internal temps
    sign = sumresponse & (1 << 15)
    temp = (sumresponse >> 4) & 4095
    internaltemp = float(temp) / 16
    if sign:
        internaltemp -= 4096

    returndict['internaltemp'] = internaltemp

    # Process single bits
    returndict['fault'] = bool(sumresponse & (1 << 16))
    returndict['opencircuit'] = bool(sumresponse & (1 << 0))
    returndict['groundshort'] = bool(sumresponse & (1 << 1))
    returndict['vccshort'] = bool(sumresponse & (1 << 2))

    return returndict


def getpigpioMAX31855temp(CS=0,device=0,**kwargs):

    dataresult = readspi(0, 0, numbytes=4)
    # print(dataresult)
    resultdict = convertbytelisttotemp(dataresult)

    return resultdict

if __name__ == "__main__":
    from pilib import controldatabase
    valuedict = getpigpioMAX31855temp()
    # recordspidata(controldatabase, valuedict)
    print(valuedict)
