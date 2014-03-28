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


def updateowfstable(database, tablename):
    import ow
    import pilib
    querylist = []
    ow.init('localhost:4304')
    sensorlist = ow.Sensor('/').sensorList()
    for sensor in sensorlist:
        print(sensor.id)
        querylist.append(
            pilib.makesqliteinsert(tablename, [sensor.address, sensor.family, sensor.id, sensor.type, sensor.crc8]))
    pilib.sqlitemultquery(database, querylist)
    ow.finish()


def updateowfsentries(database, tablename):
    import ow
    import pilib
    querylist = []
    querylist.append('delete from ' + tablename + ' where interface = "i2c1wire"')

    ow.init('localhost:4304')

    # We're going to set a name because calling things by their ids is getting
    # a bit ridiculous, but we can't have empty name fields if we rely on them
    # being there. They need to be unique, so we'll name them by type and increment them

    sensorlist = ow.Sensor('/').sensorList()
    for sensor in sensorlist:
        print(sensor.id)
        run = False
        if sensor.type == 'DS18B20' and run:
            sensorid = 'i2c1wire' + '_' + sensor.address

            # Get name if one exists
            name = pilib.sqlitedatumquery(database, 'select name from ioinfo where id=\'' + sensorid + '\'')

            # If doesn't exist, check to see if proposed name exists. If it doesn't, add it.
            # If it does, keep trying.

            if name == '':
                for index in range(100):
                    # check to see if name exists
                    name = sensor.type + '-' + str(int(index + 1))
                    print(propname)
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
            querylist.append(pilib.makesqliteinsert(tablename, [sensorid, 'i2c1wire', sensor.type, sensor.address, name, float(sensor.temperature), 'C', pilib.gettimestring(), '']))
    #print(querylist)
    pilib.sqlitemultquery(database, querylist)
    ow.finish()


if __name__ == "__main__":
    from pilib import controldatabase
    updateowfstable(controldatabase, 'owfs')
    updateowfsentries(controldatabase, 'inputs')
