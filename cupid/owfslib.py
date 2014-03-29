#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2014, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

# This script handles owfs read functions

import os, inspect, sys

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)


def owbuslist(host='localhost'):
    from resource.pyownet.protocol import OwnetProxy
    owProxy = OwnetProxy(host)
    buslist = []
    if host == 'localhost':
        dirs = owProxy.dir()
        for dir in dirs:
            buslist.append(str(dir))
    return owProxy, buslist


class owdevice():
    def __init__(self, propdict):
        for key, value in propdict.items():
            setattr(self, key, value)

    def readprop(self, propname):
        from resource.pyownet.protocol import OwnetProxy

        prop = self.devicedir + propname
        propvalue = OwnetProxy(self.host).read(prop).strip()
        setattr(self, propname, propvalue)
        return propvalue

    def readprops(self, proplist):
        from resource.pyownet.protocol import OwnetProxy
        myProxy = OwnetProxy(self.host)
        propvalues = []
        for propname in proplist:
            prop = self.devicedir + propname
            propvalue = myProxy.read(prop).strip()
            setattr(self, propname, propvalue)
            propvalues.append(propvalues)
        return propvalues


def getbusdevices(host='localhost'):
    from resource.pyownet.protocol import OwnetProxy

    # These are the properties we will always read on initialization
    # They should exist for every device type. We can add device-specific properties
    # to read below, based on type. We also want these to be properties that do not require
    # any internal conversion, i.e. static properties

    initprops = ['id', 'address', 'crc8', 'alias', 'family', 'type']

    myProxy, buslist = owbuslist(host)
    deviceobjects = []
    for device in buslist:
        propdict = {}
        propdict['devicedir'] = device
        propdict['host'] = host
        props = myProxy.dir(device)
        for prop in props:
            propname = prop.split('/')[2]
            # print(propname)
            if propname in initprops:
                # print(prop)
                propdict[propname] = myProxy.read(prop).strip()
            else:
                pass
                # Could put in default values here, but cleaner if not

        deviceobjects.append(owdevice(propdict))

    return deviceobjects


def updateowfstable(database, tablename, busdevices):
    from pilib import makesqliteinsert, sqlitemultquery

    querylist = []
    for device in busdevices:
        # print(device.id)
        querylist.append(
            makesqliteinsert(tablename, [device.address, device.family, device.id, device.type, device.crc8]))
    sqlitemultquery(database, querylist)


def updateowfsentries(database, tablename, busdevices):

    import pilib

    querylist = []
    querylist.append('delete from ' + tablename + ' where interface = \'i2c1wire\'')

    # We're going to set a name because calling things by their ids is getting
    # a bit ridiculous, but we can't have empty name fields if we rely on them
    # being there. They need to be unique, so we'll name them by type and increment them

    for device in busdevices:
        print(device.id)
        if device.type == 'DS18B20':
            sensorid = 'i2c1wire' + '_' + device.address

            # Get name if one exists
            name = pilib.sqlitedatumquery(database, 'select name from ioinfo where id=\'' + sensorid + '\'')

            # If doesn't exist, check to see if proposed name exists. If it doesn't, add it.
            # If it does, keep trying.

            if name == '':
                for index in range(100):
                    # check to see if name exists
                    name = device.type + '-' + str(int(index + 1))
                    print(name)
                    foundid = pilib.sqlitedatumquery(database, 'select id from ioinfo where name=\'' + name + '\'')
                    print('foundid' + foundid)
                    if foundid:
                        pass
                    else:
                        pilib.sqlitequery(database, pilib.makesqliteinsert('ioinfo', valuelist=[sensorid, name],
                                                                           valuenames=['id', 'name']))
                        break

            # Is it time to read temperature?
            # At the moment, we assume yes.
            device.readprop('temperature')
            print(device.temperature)
            querylist.append(pilib.makesqliteinsert(tablename, [sensorid, 'i2c1wire', device.type, device.address, name,
                                                                float(device.temperature), 'C', pilib.gettimestring(),
                                                                '']))
    print(querylist)
    pilib.sqlitemultquery(database, querylist)


if __name__ == "__main__":
    import time
    from pilib import controldatabase
    print('running')
    updateowfstable(controldatabase,'owfs')
    updateowfsentries(controldatabase,'inputs')
    print('done running')
    mydevices = getbusdevices()
    print('Found ' + str(len(mydevices)) + ' devices')
    for device in mydevices:
        print('id: ' + device.id)
        print(' getting temp ...')
        starttime = time.time()
        temp = device.readprop('temperature')
        print('temperature is ' + str(temp))
        print('elapsed time ' + str(time.time() - starttime))

