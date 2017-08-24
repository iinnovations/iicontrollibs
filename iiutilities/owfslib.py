#!/usr/bin/env python

__author__ = 'Colin Reese'
__copyright__ = 'Copyright 2016, Interface Innovations'
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
    families = ['28', '3B']

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


def owfsgetbusdevices(owdir, debug=False):
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
        if debug:
            print(propsavailable)
        for propavailable in propsavailable:
            if propavailable in initprops:
                propvalue = open(devicepath + '/' + propavailable).read().strip()
                propdict[propavailable] = propvalue
            propdict['sensorid'] = '1wire' + '_' + propdict['address']
        devices.append(owfsDevice(propdict))
    return devices


class owfsDevice():
    def __init__(self, propdict):
        for key, value in propdict.items():
            setattr(self, key, value)

    def readprop(self, propname, garbage=None):
        try:
            proppath = self.devicedir + '/' + propname
            propvalue = open(proppath).read().strip()
        except:
            if hasattr(self, 'logpath'):
                from iiutilities.utility import log
                log(self.logpath, 'Error reading property ' + propname + ' for device ' + self.address)

            propvalue = -1

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
    from iiutilities.dblib import sqlitemultquery
    from iiutilities.dblib import makesqliteinsert

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


def updateowfsdevices(busdevices, myProxy=None, debug=False):
    from cupid import pilib
    from iiutilities import dblib
    from iiutilities import datalib
    from iiutilities import utility

    # get defaults
    defaults = dblib.readalldbrows(pilib.dirs.dbs.control, 'defaults')
    default_dict={}
    for default_item in defaults:
        default_dict[default_item['valuename']] = default_item['value']

    # get current entries
    previnputs = dblib.readalldbrows(pilib.dirs.dbs.control, 'inputs')

    # Make list of IDs for easy indexing
    previnputids = []
    for input in previnputs:
        previnputids.append(input['id'])

    # Iterate over devices. Determine if values exist for polltime, frequency.
    # If so, update the device. If not, use defaults.
    # Then determine whether we should update value or not (Read temperature)

    for index, device in enumerate(busdevices):
        if device.sensorid in previnputids:
            try:
                newpollfreq = float(previnputs[previnputids.index(device.sensorid)]['pollfreq'])
            except ValueError:
                device.pollfreq = float(default_dict['inputpollfreq'])
            else:
                if newpollfreq >= 0:
                    device.pollfreq = float(previnputs[previnputids.index(device.sensorid)]['pollfreq'])
                else:
                    device.pollfreq = float(default_dict['inputpollfreq'])

            device.ontime = previnputs[previnputids.index(device.sensorid)]['ontime']
            device.offtime = previnputs[previnputids.index(device.sensorid)]['offtime']
            device.polltime = previnputs[previnputids.index(device.sensorid)]['polltime']
            device.value = previnputs[previnputids.index(device.sensorid)]['value']
            device.log_options = previnputs[previnputids.index(device.sensorid)]['log_options']
        else:
            device.pollfreq = float(default_dict['inputpollfreq'])
            device.ontime = ''
            device.offtime = ''
            device.polltime = ''
            device.value = ''

        """
        We're going to set a name because calling things by their ids is getting
        a bit ridiculous, but we can't have empty name fields if we rely on them
        being there. They need to be unique, so we'll name them by type and increment them

        Not really sure why this is conditional?
        """

        if device.type in ['DS18B20', 'DS1825']:

            # Get name if one exists
            name = dblib.sqlitedatumquery(pilib.dirs.dbs.control, 'select name from ioinfo where id=\'' + device.sensorid + '\'')

            # If doesn't exist, check to see if proposed name exists. If it doesn't, add it.
            # If it does, keep trying.

            if name == '':
                for rangeindex in range(100):
                    # check to see if name exists
                    name = device.type + '-' + str(int(index + 1))
                    # print(name)
                    foundid = dblib.sqlitedatumquery(pilib.dirs.dbs.control, 'select id from ioinfo where name=\'' + name + '\'')
                    # print('foundid' + foundid)
                    if foundid:
                        pass
                    else:
                        dblib.sqlitequery(pilib.dirs.dbs.control, dblib.makesqliteinsert('ioinfo', valuelist=[device.sensorid, name],
                                                                                        valuenames=['id', 'name']))
                        break
            device.name = name

            device.time_since_last = datalib.timestringtoseconds(datalib.gettimestring()) - datalib.timestringtoseconds(device.polltime, defaulttozero=True)

            # Is it time to read temperature?
            if device.time_since_last > device.pollfreq:
                utility.log(pilib.dirs.logs.io, 'reading temperature [' + device.name + '][' + device.id + ']' , 9, pilib.loglevels.io)
                device.readprop('temperature', myProxy)
                device.polltime = datalib.gettimestring()
                device.value = device.temperature
            else:
                utility.log(pilib.dirs.logs.io, 'not time to poll', 9, pilib.loglevels.io, )
                # print('not time to poll')

            device.unit = 'F'

        # We update the device and send them back for other purposes.
        busdevices[index] = device

    return busdevices


def updateowfsinputentries(database, tablename, devices, execute=True):
    from cupid.pilib import dirs, cupidDatabase
    from iiutilities.dblib import sqlitemultquery, make_insert_from_dict
    querylist = []
    querylist.append("delete from '" + tablename + "' where interface='1wire'")

    for device in devices:
        insert_dict = {'id':device.sensorid, 'interface':'1wire', 'type':str(device.type), 'address':str(device.id), 
                  'name':str(device.name), 'value':str(device.value), 'unit':str(device.unit), 
                  'polltime':str(device.polltime), 'pollfreq':str(device.pollfreq), 'ontime':device.ontime, 'offtime':device.offtime}
        querylist.append(make_insert_from_dict('inputs', insert_dict))
        # querylist.append("insert into inputs values ('" + device.sensorid +"','" + '1wire' + "','" +
        #                 str(device.type) + "','" + str(device.id) + "','" + str(device.name) + "','" + str(device.value) + "','" + str(device.unit)+ "','" +
        #                 str(device.polltime) + "'," + str(device.pollfreq) + ",'" + device.ontime + "','" + device.offtime + "')")

    # print(querylist)
    if execute:
        control_db = cupidDatabase(dirs.dbs.control)
        control_db.queries(querylist)

    return querylist

# Currently we are using straight fuse/owfs directory listing, rather than the pyownet functions (also
# available above)


def runowfsupdate(execute=True, **kwargs):
    import time
    from iiutilities import utility

    settings = {
        'logpath':None,
        'owfsdir':'/var/1wire',
        'loglevel':1
    }
    settings.update(kwargs)

    queries = []
    if settings['logpath']:
        utility.log(settings['logpath'], 'getting buses', 9, settings['loglevel'])

    starttime = time.time()
    busdevices = owfsgetbusdevices(settings['owfsdir'])

    utility.log(settings['logpath'], 'done getting devices, took ' + str(time.time() - starttime), 9, settings['loglevel'])
    utility.log(settings['logpath'], 'updating device data', 9, settings['loglevel'])

    starttime = time.time()
    updateddevices = updateowfsdevices(busdevices)

    utility.log(settings['logpath'], 'done reading devices, took ' + str(time.time() - starttime), 9, settings['loglevel'])
    utility.log(settings['logpath'], 'your devices: ', 9, settings['loglevel'])

    for device in busdevices:
        utility.log(settings['logpath'], device.id)

    utility.log(settings['logpath'], 'updating entries in owfstable', 9, settings['loglevel'])
    starttime = time.time()

    owfstableentries = updateowfstable(settings['logpath'], 'owfs', updateddevices, execute=execute)

    utility.log(settings['logpath'], 'done updating owfstable, took ' + str(time.time() - starttime), 9, settings['loglevel'])

    owfsinputentries = updateowfsinputentries(settings['logpath'], 'inputs', updateddevices, execute=execute)

    queries.extend(owfstableentries)
    queries.extend(owfsinputentries)

    return busdevices, queries


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'debug':
        runowfsupdate(debug=True)
    else:
        runowfsupdate()