#!/usr/bin/env python

__author__ = 'Colin Reese'
__copyright__ = 'Copyright 2014, Interface Innovations'
__credits__ = ['Colin Reese']
__license__ = 'Apache 2.0'
__version__ = '1.0'
__maintainer__ = 'Colin Reese'
__email__ = 'support@interfaceinnovations.org'
__status__ = 'Development'

# This script handles owfs read functions

import os, inspect, sys

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)


# Using fuse / owfs
def owfsbuslist(owdir):
    from os import walk

    # Should get this from somewhere for recognized types
    families = ['28']

    d = []
    for (dirpath, dirnames, filenames) in walk(owdir):
        d.extend(dirnames)
        break

    devicedirs = []
    devices = []
    for item in d:
        if item.split('.')[0] in families:
            devices.append(item)
            devicedirs.append(owdir + '/' + item)
    # print(devices)
    return devices


def owfsgetbusdevices(owdir):
    from os import walk

    buslist = owfsbuslist(owdir)

    initprops = ['id', 'address', 'crc8', 'alias', 'family', 'type']

    devices = []
    for devicedir in buslist:
        propdict = {}
        devicepath = owdir + '/' + devicedir
        propdict['devicedir'] = devicepath
        for (dirpath, dirnames, filenames) in walk(devicepath):
            propsavailable = filenames
            break
        for propavailable in propsavailable:
            if propavailable in initprops:
                propvalue = open(devicepath + '/' + propavailable).read().strip()
                propdict[propavailable] = propvalue
        devices.append(owfsDevice(propdict))
    return devices


class owfsDevice():
    def __init__(self, propdict):
        for key, value in propdict.items():
            setattr(self, key, value)

    def readprop(self, propname, garbage=None):
        # need some error-checking here
        proppath = self.devicedir + '/' + propname
        propvalue = open(proppath).read().strip()
        setattr(self, propname, propvalue)
        return propvalue

    def readprops(self, proplist, garbage=None):
        propvalues = []
        for propname in proplist:
            propvalue = self.readprop(self, propname)
            propvalues.append(propvalue)
        return propvalues


###############################################
# Using ownet

def owbuslist(host='localhost'):
    from resource.pyownet.protocol import OwnetProxy

    owProxy = OwnetProxy(host)
    buslist = []
    if host == 'localhost':
        dirs = owProxy.dir()
        for dir in dirs:
            buslist.append(str(dir))
    return owProxy, buslist


class owDevice():
    def __init__(self, propdict):
        for key, value in propdict.items():
            setattr(self, key, value)

    def readprop(self, propname, myProxy=None):
        from resource.pyownet.protocol import OwnetProxy

        prop = self.devicedir + propname
        if myProxy:
            propvalue = myProxy.read(prop).strip()
            setattr(self, propname, propvalue)
        else:
            propvalue = OwnetProxy(self.host).read(prop).strip()
            setattr(self, propname, propvalue)
        return propvalue

    def readprops(self, proplist, myProxy=None):
        from resource.pyownet.protocol import OwnetProxy

        if myProxy:
            pass
        else:
            myProxy = OwnetProxy(self.host)
        propvalues = []
        for propname in proplist:
            prop = self.devicedir + propname
            propvalue = myProxy.read(prop).strip()
            setattr(self, propname, propvalue)
            propvalues.append(propvalues)
        return propvalues


def getowbusdevices(host='localhost'):
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
            if propname in initprops:
                propdict[propname] = myProxy.read(prop).strip()
            else:
                pass
                # Could put in default values here, but cleaner if not

        deviceobjects.append(owDevice(propdict))

    return myProxy, deviceobjects


def updateowfstable(database, tablename, busdevices, execute=True):
    from pilib import makesqliteinsert, sqlitemultquery

    querylist = []
    for device in busdevices:
        # print(device.id)
        # print([device.address, device.family, device.id, device.type, device.crc8])
        querylist.append(
            makesqliteinsert(tablename, [device.address, device.family, device.id, device.type, device.crc8]))
    # print(querylist)
    if execute:
        sqlitemultquery(database, querylist)
    return querylist


def updateowfsdevices(busdevices, myProxy=None):
    import pilib

    querylist = []

    # We're going to set a name because calling things by their ids is getting
    # a bit ridiculous, but we can't have empty name fields if we rely on them
    # being there. They need to be unique, so we'll name them by type and increment them

    for index, device in enumerate(busdevices):
        # print(device.id)
        # We only
        if device.type == 'DS18B20':
            device.sensorid = '1wire' + '_' + device.address

            # Get name if one exists
            name = pilib.sqlitedatumquery(pilib.controldatabase, 'select name from ioinfo where id=\'' + device.sensorid + '\'')

            # If doesn't exist, check to see if proposed name exists. If it doesn't, add it.
            # If it does, keep trying.

            if name == '':
                for rangeindex in range(100):
                    # check to see if name exists
                    name = device.type + '-' + str(int(index + 1))
                    # print(name)
                    foundid = pilib.sqlitedatumquery(pilib.controldatabase, 'select id from ioinfo where name=\'' + name + '\'')
                    # print('foundid' + foundid)
                    if foundid:
                        pass
                    else:
                        pilib.sqlitequery(pilib.controldatabase, pilib.makesqliteinsert('ioinfo', valuelist=[device.sensorid, name],
                                                                           valuenames=['id', 'name']))

                        break
            device.name = name

            # Is it time to read temperature?
            # At the moment, we assume yes.
            device.readprop('temperature', myProxy)
            device.value = device.temperature

        # We update the device and send them back for other purposes.
        busdevices[index] = device

    return busdevices


def updateowfsinputentries(database, tablename, devices, execute=True):
    from pilib import readalldbrows, controldatabase, sqlitemultquery
    querylist = []
    querylist.append("delete from '" + tablename + "' where interface='1wire'")

    # get defaults
    defaults = readalldbrows(controldatabase, 'defaults')[0]

    # get current entries
    previnputs = readalldbrows(controldatabase, 'inputs')

    # Make list of IDs for easy indexing
    previnputids = []
    for input in previnputs:
        previnputids.append(input['id'])

    for device in devices:
        if device.sensorid in previnputids:
            device.pollfreq = previnputs[previnputids.index['device.sensorid']]['pollfreq']
            device.ontime = previnputs[previnputids.index['device.sensorid']]['ontime']
            device.offtime = previnputs[previnputids.index['device.sensorid']]['offtime']
        else:
            device.pollfreq = defaults['pollfreq']
            device.ontime = ''
            device.offtime = ''

            querylist.append('insert into inputs values (\'' + device.sensorid + '\',\'' + '1Wire' + '\',\'' +
                        str(device.type) + '\',\'' + str(device.id) + '\',\'' + str(device.name) + '\',\'' + str(device.value) + "','','" +
                        str(device.polltime) + '\',' + str(device.pollfreq) + "," + device.ontime + "," + device.offtime + ")")

    print(querylist)
    if execute:
        sqlitemultquery(controldatabase,querylist)

    return querylist

# Currently we are using straight fuse/owfs directory listing, rather than the pyownet functions (also
# available above)

def runowfsupdate(debug=False, execute=True):
    import time

    queries = []
    from pilib import onewiredir, controldatabase, sqlitemultquery

    if debug:
        print('getting buses')
        starttime = time.time()
    busdevices = owfsgetbusdevices(onewiredir)
    if debug:
        print('done getting devices, took ' + str(time.time() - starttime))
        print('updating device data')
        starttime = time.time()
    updateddevices = updateowfsdevices(busdevices)
    if debug:
        print('done reading devices, took ' + str(time.time() - starttime))
        print('your devices: ')
        for device in busdevices:
            print(device.id)
        print('updating entries in owfstable')
        starttime = time.time()
    owfstableentries = updateowfstable(controldatabase, 'owfs', updateddevices, execute=execute)
    if debug:
        print('done updating owfstable, took ' + str(time.time() - starttime))

    owfsinputentries = updateowfsinputentries(controldatabase, 'inputs', updateddevices, execute=execute)
    queries.extend(owfstableentries)
    queries.extend(owfsinputentries)
    if execute:
        sqlitemultquery(controldatabase, queries)
    return busdevices, queries


if __name__ == '__main__':
    runowfsupdate()