#!/usr/bin/python

def readinputs(database):
    
    # TODO: We are going to have selective enable/disable
    # of interfaces in here from the system control
    # control database.

    import readspi
    spidata=readspi.readspi()
    readspi.recordspidata(database,spidata)

    import owfslib
    owfslib.updateowfstable(database,'owfs')
    owfslib.updateowfsdata(database,'inputsdata')
  
    return("outputs read")

if __name__=="__main__":
    database='/var/www/data/controldata.db'
    readinputs(database)

