#!/usr/bin/python
# Colin Reese
# 12/18/2012
#
# This script handles owfs read functions and converts read
# temperatures into a simple html file

# Used files:
#   sensordata.html : file to write data to in html format
#   sensor files : located in /var/1wire/10.ROM , where ROM is
#       the device hardware address

#import re
import os
import time
#import csv
import pilib

filedir = ""
onewiredir = "/var/1wire/"
outputdir = "/var/www/data/"
database = '/var/www/data/controldata.db'
querylist=[];
querylist.append('delete from sensordata')

##########################################
# Do our 1wire stuff

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


    # Write to database
    # At the moment all are enabled by default.
    # Eventually we'll read this before we delete all entries

    for tuple in ROMsandtemps:

        ROM=tuple[0]
        temp=tuple[1]
        queryresult=pilib.sqlitequery(database,'select name from sensorinfo where sensorID = ' + "'" + ROM + "'") 
        if not queryresult:
            name=''
        else:
            name = queryresult[0][0]
        valuelist = [tuple[0],tuple[1],'F',pilib.gettimestring(),1,name]
        query = pilib.makesqliteinsert(database,'sensordata',valuelist)
        # print(query) 
        querylist.append(query)

    # execute combined query

    #print(querylist)

########################################
# Do thermocouple stuff

import subprocess
tctemp=subprocess.check_output(['python3','/usr/lib/modwsgi/max31855-1.0/getmaxtemp.py'])
print('temperature is ')
print(tctemp)
print(tctemp)
querylist.append(pilib.makesqliteinsert(database,'sensordata',['TC1','SPITC','TC',tctemp,'F',pilib.gettimestring(),1,'']))

if querylist:
    print(querylist)
    pilib.sqlitemultquery(database,querylist)
    print('doing querylist')
