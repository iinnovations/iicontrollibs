#!/usr/bin/python

def readinputs(database):
    
    onewiredir='/var/1wire/'

    import readspi
    spidata=readspi.readspi()
    readspi.recordspidata(database,spidata)

    import readowfs
    owfsdata=readowfs.readowfs(onewiredir)
    readowfs.recordowfsdata(database,owfsdata)
  
    return("outputs read")

if __name__=="__main__":
    database='/var/www/data/controldata.db'
    readinputs(database)

