#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2014, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"


def setrawspilights(enabledlists, CS=1):
    try:
        import spidev
    except ImportError:
        raise ImportError('You have not installed the spidev python package. Exiting.')
        exit

    spi = spidev.SpiDev()
    try:
        spi.open(0, CS)  # Port 0, CS1
    except:
        print('error raised. exiting.')
        exit
    else:

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

        # Transfer bytes 
        resp = spi.xfer2(spiassignments)
        return resp


def setspilights(lightsettingsarray, CS=1):
    # Color LED assignments:
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
    setrawspilights([enabledlist1, enabledlist2],CS)


def setspilightsoff(CS=1):
    setrawspilights([[0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0]],CS)


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
        setspilights(settingsarray[index],CS)
        print('sending')
        print(settingsarray[index])
        time.sleep(delay)
        index += 1
        if index >= len(settingsarray):
            index = 0


def updatelightsfromdb(database, table, CS):
    import pilib

    # get settings from database
    query = 'select status from \'' + table + '\' where type=\'SPI' + str(CS) + '\''
    query2 = 'select name from \'' + table + '\' where type=\'SPI' + str(CS) + '\''

    statuses = pilib.sqlitequery(database, query)
    names = pilib.sqlitequery(database, query2)
    d = {}
    for status, name in zip(statuses, names):
        d[name[0]] = status[0]
    setarray = [[d['SPI' + str(CS) + '_RGB1_R'], d['SPI' + str(CS) + '_RGB1_G'], d['SPI' + str(CS) + '_RGB1_B']],
                [d['SPI' + str(CS) + '_RGB2_R'], d['SPI' + str(CS) + '_RGB2_G'], d['SPI' + str(CS) + '_RGB2_B']],
                [d['SPI' + str(CS) + '_RGB3_R'], d['SPI' + str(CS) + '_RGB3_G'], d['SPI' + str(CS) + '_RGB3_B']],
                [d['SPI' + str(CS) + '_RGB4_R'], d['SPI' + str(CS) + '_RGB4_G'], d['SPI' + str(CS) + '_RGB4_B']],
                d['SPI' + str(CS) + '_SC_R'], d['SPI' + str(CS) + '_SC_G'], d['SPI' + str(CS) + '_SC_B'],
                d['SPI' + str(CS) + '_SC_Y']]
    setspilights(setarray, CS)

def getCuPIDlightsentries(table, CS, previndicators=None):
    querylist=[]

    if not previndicators:
        from pilib import readalldbrows, controldatabase
        previndicators = readalldbrows(controldatabase, 'indicators')

    previndicatorsnames = []
    for previndicator in previndicators:
        previndicatorsnames.append(previndicator['name'])

    interface = 'SPI' + str(CS)
    names = ['SPI' + str(CS) + '_RGB1_R',
             'SPI' + str(CS) + '_RGB1_G',
             'SPI' + str(CS) + '_RGB1_B',
             'SPI' + str(CS) + '_RGB2_R',
             'SPI' + str(CS) + '_RGB2_G',
             'SPI' + str(CS) + '_RGB2_B',
             'SPI' + str(CS) + '_RGB3_R',
             'SPI' + str(CS) + '_RGB3_G',
             'SPI' + str(CS) + '_RGB3_B',
             'SPI' + str(CS) + '_RGB4_R',
             'SPI' + str(CS) + '_RGB4_G',
             'SPI' + str(CS) + '_RGB4_B',
             'SPI' + str(CS) + '_SC_R',
             'SPI' + str(CS) + '_SC_G',
             'SPI' + str(CS) + '_SC_B',
             'SPI' + str(CS) + '_SC_Y']
    details = ['red', 'green', 'blue', 'red', 'green', 'blue', 'red',
               'green', 'blue', 'red', 'green', 'blue', 'red', 'green', 'blue', 'yellow']
    setlist = []
    valuelist = []
    for name, detail in zip(names, details):
        if name in previndicatorsnames:
            value = previndicators[previndicatorsnames.index(name)]['status']
        else:
            value = 0
        valuelist.append(value)
        querylist.append("insert into " + table + " values ('" + name + "','" + interface + "', 'CuPIDlights', " + str(value) + ",'" + detail + "')")

    setlist = [[valuelist[0], valuelist[1], valuelist[2]],
               [valuelist[3], valuelist[4], valuelist[5]],
               [valuelist[6], valuelist[7], valuelist[8]],
               [valuelist[7], valuelist[8], valuelist[9]],
               valuelist[10], valuelist[11], valuelist[12], valuelist[13]]

    return querylist, setlist

if __name__ == '__main__':
    from pilib import controldatabase
    updatelightsfromdb(controldatabase,'indicators',1)
    #twitterspilights(1)
    #setspilightsoff()
