#!/usr/bin/python
# Colin Reese
# 12/18/2012
#
# This script handles owfs read functions and converts read
# temperatures into a simple html file

import os
import time
import pilib

def readowfs(onewiredir):

    querylist=[];
    querylist.append('delete from sensordata')

    onlineROMlist=[]
    ROMfiles=[]
    for filename in os.listdir(onewiredir):
        try:
            filename.index('28.')
        except ValueError:
            pass
            #print("not found")
        else:
            addressfile=open(onewiredir + filename + '/address')	
            ROMaddy=addressfile.readline().strip()
            onlineROMlist.append(ROMaddy)
            ROMfiles.append(filename)

    if onlineROMlist:
        #print("ROMs online:\n")
        #print(onlineROMlist)
        os.system('echo ' +  onlineROMlist[0] + '> /home/pi/ROMs')
        # default to fahrenheit

        tempscale="F"

        # Read info from ROM files

        ROMsandtemps=[]
        i=0
        #print("ROMfiles")
        #print( ROMfiles)
        #print("onlineROMlist")
        #print(onlineROMlist)
        for filename in ROMfiles:
            tempfile=open(onewiredir + filename + "/temperature")
            #print(tempfile)
            ROMsandtemps.append([onlineROMlist[i],tempfile.readline().strip()])
            i +=1

        #print("ROM tuples\n")
        #print(ROMsandtemps)

def recordowfsdata(controldatabase,ROMsandvalues=None):

    # Write to database
    # At the moment all are enabled by default.
    # Eventually we'll read this before we delete all entries
    if ROMsandvalues: 
        for tuple in ROMsandvalues:

            ROM=tuple[0]
            temp=tuple[1]
            queryresult=pilib.sqlitequery(controldatabase,'select name from inputsinfo where inputID = ' + "'" + ROM + "'") 
            if not queryresult:
                name=''
            else:
                name = queryresult[0][0]
            valuelist = ['OWROM' + tuple[0],tuple[1],'F',pilib.gettimestring(),1,name]
            query = pilib.makesqliteinsert(controldatabase,'inputsdata',valuelist)
            # print(query) 
            querylist.append(query)
    else:
        return("no ROMs passed")

if __name__ == "__main__":
    onewiredir='/var/1wire'
    controldatabase='/var/www/data/controldata.db'
    ROMsandvalues=readowfs(onewiredir)
    writeresponse=recordowfsdata(controldatabase,ROMsandvalues)

    print(ROMsandvalues)
    print(writeresponse)
   
