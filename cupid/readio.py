#!/usr/bin/python

def readio(database):
    
    # TODO: We are going to have selective enable/disable
    # of interfaces in here from the system control
    # control database.

    #import readspi
    #spidata=readspi.readspi()
    #readspi.recordspidata(database,spidata)

    import owfslib
    owfslib.updateowfstable(database,'owfs')
    owfslib.updateowfsdatatable(database,'inputsdata')
  
    return("outputs read")

def updateiodata(database):
    from pilib import readalldbrows, sqlitedatumquery, sqlitequery
    inputsdata = readalldbrows(database,'inputsdata')
    querylist=[]
    for input in inputsdata:
        id=input['id']
        #print('id - ' + id)
        name=sqlitedatumquery(database,'select name from ioinfo where id=\'' + id + '\'')
        #print('name - ' + name)
        sqlitequery(database, 'update inputsdata set name=\'' + name + '\' where id = \'' + id + '\'')

if __name__=="__main__":
    import pilib
    database=pilib.controldatabase
    readio(database)

