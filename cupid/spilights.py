#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2016, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

import os
import sys
import inspect

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)

from utilities import dblib


def setrawspilights(enabledlists, CS=1, **kwargs):

    from pilib import syslog, sysloglevel
    from utilities.utility import log
    if 'method' in kwargs:
        method = kwargs['method']
    else:
        method = 'spidev'

    # Notes:
    # Low is on. Cathodes are open drain.
    # This unforunately means we need to initialize
    # to off on start-up. not a huge deal

    spiassignments = []
    for enabledlist in enabledlists:
        bytesum = 0
        for index, bit in enumerate(enabledlist):
            bytesum += bit * (2 ** index)

        spiassign = 255 - bytesum
        spiassignments.append(spiassign)

    resp = []
    if method == 'spidev':
        try:
            import spidev
        except ImportError:
            log(syslog, 'You have not installed the spidev python package. Exiting.', 0, sysloglevel)
            exit
        else:
            spi = spidev.SpiDev()
        try:
            spi.open(0, CS)  # Port 0, CS1
            spi.max_speed_hz = 50000
        except:
            log(syslog, 'Error raised on spi open. exiting.', 0, sysloglevel)
            exit
        else:

            # Transfer bytes
            # print('spi assignments')
            # print(spiassignments)
            resp = spi.xfer2(spiassignments)
            # resp = spi.xfer2(spiassignments)

    elif method == 'pigpio':
        import pigpio
        import array
        if 'piobject' in kwargs:
            pi = kwargs['piobject']
        else:
            pi = pigpio.pi()

        handle = pi.spi_open(0, 50000, 0)

        resp = pi.spi_write(handle, array.array(spiassignments).tostring())
        print(resp)

    if method == 'pigpio' and 'piobject' not in kwargs:
        pi.stop()

    return resp


def setspilights(lightsettingsarray, CS=1):

    # Color LED assignments (to SPI):
    # list 1:
    # 1 : RGB 2 Green 
    # 2 : RGB 1 Blue 
    # 3 : RGB 1 Red 
    # 4 : RGB 1 Green 
    # 5 : Yellow single color 
    # 6 : Blue single color 
    # 7 : Green single color 
    # 8 : Red single color 

    # list 2:

    # 1 : RGB 4 Blue 
    # 2 : RGB 4 Red 
    # 3 : RGB 4 Green 
    # 4 : RGB 3 Blue 
    # 5 : RGB 3 Red 
    # 6 : RGB 3 Green 
    # 7 : RGB 2 Blue 
    # 8 : RGB 2 Red 

    # Light settings array argument input
    # RGB1, RGB2, RGB3, RGB4, singlered, singlegreen, singleblue, singleyellow
    RGB1 = lightsettingsarray[0]
    RGB2 = lightsettingsarray[1]
    RGB3 = lightsettingsarray[2]
    RGB4 = lightsettingsarray[3]
    singlered = lightsettingsarray[4]
    singlegreen = lightsettingsarray[5]
    singleblue = lightsettingsarray[6]
    singleyellow = lightsettingsarray[7]

    enabledlist1 = [RGB2[1], RGB1[2], RGB1[0], RGB1[1], singleyellow, singleblue, singlegreen, singlered]
    enabledlist2 = [RGB4[2], RGB4[0], RGB4[1], RGB3[2], RGB3[0], RGB3[1], RGB2[2], RGB2[0]]
    # print('enabled lists')
    # print(enabledlist1)
    # print(enabledlist2)
    setrawspilights([enabledlist1, enabledlist2], CS)


def setspilightsoff(CS=1):
    setrawspilights([[0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0]], CS)


def twitterspilights(delay):
    import time

    settingsarray = []
    settingsarray.append([[1, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], 0, 0, 0, 0])
    settingsarray.append([[0, 1, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], 0, 0, 0, 0])
    settingsarray.append([[0, 0, 1], [0, 0, 0], [0, 0, 0], [0, 0, 0], 0, 0, 0, 0])
    settingsarray.append([[0, 0, 0], [1, 0, 0], [0, 0, 0], [0, 0, 0], 0, 0, 0, 0])
    settingsarray.append([[0, 0, 0], [0, 1, 0], [0, 0, 0], [0, 0, 0], 0, 0, 0, 0])
    settingsarray.append([[0, 0, 0], [0, 0, 1], [0, 0, 0], [0, 0, 0], 0, 0, 0, 0])
    settingsarray.append([[0, 0, 0], [0, 0, 0], [1, 0, 0], [0, 0, 0], 0, 0, 0, 0])
    settingsarray.append([[0, 0, 0], [0, 0, 0], [0, 1, 0], [0, 0, 0], 0, 0, 0, 0])
    settingsarray.append([[0, 0, 0], [0, 0, 0], [0, 0, 1], [0, 0, 0], 0, 0, 0, 0])
    settingsarray.append([[0, 0, 0], [0, 0, 0], [0, 0, 0], [1, 0, 0], 0, 0, 0, 0])
    settingsarray.append([[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 1, 0], 0, 0, 0, 0])
    settingsarray.append([[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 1], 0, 0, 0, 0])
    settingsarray.append([[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], 1, 0, 0, 0])
    settingsarray.append([[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], 0, 1, 0, 0])
    settingsarray.append([[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], 0, 0, 1, 0])
    settingsarray.append([[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], 0, 0, 0, 1])
    run = True
    index = 0
    while run == True:
        setspilights(settingsarray[index])
        # print('sending')
        # print(settingsarray[index])
        time.sleep(delay)
        index += 1
        if index >= len(settingsarray):
            index = 0


def updatelightsfromdb(database, table, CS):
    import pilib

    # get settings from database
    query = 'select status from \'' + table + '\' where interface=\'SPI' + str(CS) + '\''
    query2 = 'select name from \'' + table + '\' where interface=\'SPI' + str(CS) + '\''

    statuses = dblib.sqlitequery(database, query)
    names = dblib.sqlitequery(database, query2)
    # print(statuses)
    # print(names)
    d = {}
    for status, name in zip(statuses, names):
        d[name[0]] = status[0]

    # print(d)
    try:
        setarray = [[d['SPI_RGB1_R'], d['SPI_RGB1_G'], d['SPI_RGB1_B']],
                    [d['SPI_RGB2_R'], d['SPI_RGB2_G'], d['SPI_RGB2_B']],
                    [d['SPI_RGB3_R'], d['SPI_RGB3_G'], d['SPI_RGB3_B']],
                    [d['SPI_RGB4_R'], d['SPI_RGB4_G'], d['SPI_RGB4_B']],
                    d['SPI_SC_R'], d['SPI_SC_G'], d['SPI_SC_B'],
                    d['SPI_SC_Y']]
    except KeyError:
        print('key error on indicator keys')
    else:
        setspilights(setarray, CS)


def getCuPIDlightsentries(table, CS, previndicators=None):
    querylist=[]

    if not previndicators:
        from pilib import controldatabase
        from utilities.dblib import readalldbrows
        previndicators = readalldbrows(controldatabase, 'indicators')

    previndicatornames = []
    previndicatorvalues = []
    d={}
    for previndicator in previndicators:
        previndicatornames.append(previndicator['name'])
        previndicatorvalues.append(previndicator['status'])
        d[previndicator['name']]=previndicator['status']

    interface = 'SPI' + str(CS)
    names = ['SPI_RGB1_R','SPI_RGB1_G', 'SPI_RGB1_B','SPI_RGB2_R', 'SPI_RGB2_G', 'SPI_RGB2_B',
                'SPI_RGB3_R', 'SPI_RGB3_G', 'SPI_RGB3_B',
                'SPI_RGB4_R', 'SPI_RGB4_G', 'SPI_RGB4_B',
                'SPI_SC_R', 'SPI_SC_G', 'SPI_SC_B', 'SPI_SC_Y']
    details = ['red', 'green', 'blue', 'red', 'green', 'blue', 'red',
               'green', 'blue', 'red', 'green', 'blue', 'red', 'green', 'blue', 'yellow']
    setlist = []
    valuelist = []
    for name, detail in zip(names, details):
        if name in previndicatornames:
            value = previndicators[previndicatornames.index(name)]['status']
        else:
            value = 0
        valuelist.append(value)
        querylist.append("insert or replace into " + table + " values ('" + name + "','" + interface + "', 'CuPIDlights', " + str(value) + ",'" + detail + "')")

    setlist = [[valuelist[0], valuelist[1], valuelist[2]],
               [valuelist[3], valuelist[4], valuelist[5]],
               [valuelist[6], valuelist[7], valuelist[8]],
               [valuelist[7], valuelist[8], valuelist[9]],
               valuelist[10], valuelist[11], valuelist[12], valuelist[13]]

    return querylist, setlist

if __name__ == '__main__':
    from pilib import controldatabase
    # updatelightsfromdb(controldatabase, 'indicators',1)
    #twitterspilights(1)
    setspilightsoff()
