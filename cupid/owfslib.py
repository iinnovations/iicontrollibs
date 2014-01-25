#!/usr/bin/python
# Colin Reese
# 12/18/2012
#
# This script handles owfs read functions

import os
import time
import pilib
import ow

def updateowfstable(database,tablename):

    # don't need this. sqliteinsert makes an insert or update query.
    #currenttable=pilib.readalldbrows(database,tablename)

    querylist=[]
    ow.init('localhost:4304')
    for sensor in ow.Sensor('/').sensorList():
        querylist.append(pilib.makesqliteinsert(tablename,[sensor.address,sensor.family,sensor.id,sensor.type,sensor.crc8]))
    pilib.sqlitemultquery(database,querylist)

def updateowfsdatatable(database,tablename):

    querylist=[]
    namequerylist=[]
    querylist.append('delete from ' + tablename + ' where interface = "i2c1wire"')

    ow.init('localhost:4304')

    # We're going to set a name because calling things by their ids is getting
    # a bit ridiculous, but we can't have empty name fields if we rely on them
    # being there. They need to be unique, so we'll name them by type and increment them

    for sensor in ow.Sensor('/').sensorList():
        if sensor.type=='DS18B20':
            id='i2c1wire' + '_' + sensor.address

            querylist.append(pilib.makesqliteinsert(tablename,[id,'i2c1wire',sensor.type,sensor.address,float(sensor.temperature),'C',pilib.gettimestring(),1,'']))

            # Get name if one exists
            name = pilib.sqlitedatumquery(database, 'select name from ioinfo where id=\"' + id + '\"')

            # If doesn't exist, check to see if proposed name exists. If it doesn't, add it.
            # If it does, keep trying.

            if name == '':
                for index in range(100):
                    # check to see if name exists
                    propname= sensor.type + '-' + str(int(index+1))
                    foundid = pilib.sqlitedatumquery(database, 'select id from ioinfo where name=\"' + propname + '\"')
                    if foundid:
                        pass
                    else:
                        pilib.sqlitequery(database,pilib.makesqliteinsert('ioinfo',valuelist=[id,propname],valuenames=['id','name']))
                        break

    #print(querylist)
    pilib.sqlitemultquery(database,querylist)

if __name__ == "__main__":
    updateowfstable(pilib.controldatabase,'owfs')
    updateowfsdatatable(pilib.controldatabase,'inputsdata')
