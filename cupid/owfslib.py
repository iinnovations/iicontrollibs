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

import pilib
import ow


def updateowfstable(database, tablename):
    # don't need this. sqliteinsert makes an insert or update query.
    #currenttable=pilib.readalldbrows(database,tablename)

    querylist = []
    ow.init('localhost:4304')
    for sensor in ow.Sensor('/').sensorList():
        querylist.append(
            pilib.makesqliteinsert(tablename, [sensor.address, sensor.family, sensor.id, sensor.type, sensor.crc8]))
    pilib.sqlitemultquery(database, querylist)


def updateowfsdatatable(database, tablename):
    querylist = []
    namequerylist = []
    querylist.append('delete from ' + tablename + ' where interface = "i2c1wire"')

    ow.init('localhost:4304')

    # We're going to set a name because calling things by their ids is getting
    # a bit ridiculous, but we can't have empty name fields if we rely on them
    # being there. They need to be unique, so we'll name them by type and increment them

    for sensor in ow.Sensor('/').sensorList():
        if sensor.type == 'DS18B20':
            sensorid = 'i2c1wire' + '_' + sensor.address

            querylist.append(pilib.makesqliteinsert(tablename, [sensorid, 'i2c1wire', sensor.type, sensor.address,
                                                                float(sensor.temperature), 'C', pilib.gettimestring(),
                                                                1, '']))

            # Get name if one exists
            name = pilib.sqlitedatumquery(database, 'select name from ioinfo where id=\"' + sensorid + '\"')

            # If doesn't exist, check to see if proposed name exists. If it doesn't, add it.
            # If it does, keep trying.

            if name == '':
                for index in range(100):
                    # check to see if name exists
                    propname = sensor.type + '-' + str(int(index + 1))
                    foundid = pilib.sqlitedatumquery(database, 'select id from ioinfo where name=\"' + propname + '\"')
                    if foundid:
                        pass
                    else:
                        pilib.sqlitequery(database, pilib.makesqliteinsert('ioinfo', valuelist=[id, propname],
                                                                           valuenames=['id', 'name']))
                        break

    #print(querylist)
    pilib.sqlitemultquery(database, querylist)


if __name__ == "__main__":
    updateowfstable(pilib.controldatabase, 'owfs')
    updateowfsdatatable(pilib.controldatabase, 'inputsdata')
