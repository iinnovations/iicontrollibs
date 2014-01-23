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

    currenttable=pilib.readalldbrows(database,tablename)

    querylist=[]
    ow.init('localhost:4304')
    for sensor in ow.Sensor('/').sensorList():
        querylist.append(pilib.makesqliteinsert(database,tablename,[sensor.address,sensor.family,sensor.id,sensor.type,sensor.crc8]))
    pilib.sqlitemultquery(database,querylist)

def updateowfsdatatable(database,tablename):

    querylist=[]
    querylist.append('delete from ' + tablename + ' where interface = "i2c1wire"')

    ow.init('localhost:4304')
    for sensor in ow.Sensor('/').sensorList():
        if sensor.type=='DS18B20':
            id='i2c1wire' + '_' + sensor.address
            querylist.append(pilib.makesqliteinsert(database,tablename,[id,'i2c1wire',sensor.type,sensor.address,sensor.temperature,'C',pilib.gettimestring(),1,'']))

    # print(querylist)
    pilib.sqlitemultquery(database,querylist)

if __name__ == "__main__":
    controldatabase='/var/www/data/controldata.db'
    updateowfstable(controldatabase,'owfs')
    updateowfsdatatable(controldatabase,'inputsdata')
