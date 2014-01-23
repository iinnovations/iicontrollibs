#!/usr/bin/python
# Colin Reese
# 12/18/2012
#
# periodicreadio.py

# This script runs the input reading scripts 
# specified interval, sends to log, channels and plot dbs 

import os
import pilib
import readio
from time import sleep

onewiredir = "/var/1wire/"
outputdir = "/var/www/data/"
controldatabase='/var/www/data/controldata.db'
logdatabase='/var/www/data/logdata.db'

readtime=10  	# default, seconds

# Read from systemstatus to make sure we should be running
inputsreadenabled=pilib.sqlitedatumquery(controldatabase,'select inputsreadenabled from systemstatus')
while inputsreadenabled:   
    #print("runtime")
    #print("reading input")
    # Read again, once inside each loop so we terminate if the 
    # variable name is changed

    inputsreadenabled=pilib.sqlitedatumquery(controldatabase,'select inputsreadenabled from systemstatus')
    
    # Set last run time
    pilib.sqlitequery(controldatabase, 'update systemstatus set lastinputspoll=\'' + pilib.gettimestring() + '\'')
    pilib.sqlitequery(controldatabase, 'update systemstatus set inputsreadstatus=\'1\'')

    # Read and record everything as specified in controldatabase 

    reply=readio.readio(controldatabase)

    result = pilib.readonedbrow(controldatabase,'systemstatus',0)
    systemsdict = result[0]
    #print("here is the systems dict")
    #print(systemsdict)
    readtime = systemsdict['inputsreadfreq'] 

    plotpoints=20
    logpoints=20

    ################################################### 
    # Update controlvalues in channels

    channels=pilib.readalldbrows(controldatabase,'channels')
    for channel in channels:
        
        # Get controlinput for each channel
        channelname = channel['name']
        controlinput = channel['controlinput']
        
        # Get the input for the name from inputs info
        # Then get the value and readtime from the input if it
        # can be found

        if controlinput: 
            controlvalue = pilib.sqlitedatumquery(controldatabase,'select value from inputsdata where id=' + "'" + controlinput +"'" )
            controltime = pilib.sqlitedatumquery(controldatabase,'select polltime from inputsdata where id=' + "'" + controlinput +"'" )

            # Only update channel value if value was found
 
            if controlvalue:
                pilib.sqlitequery(controldatabase, 'update channels set controlvalue=' + str(controlvalue) + ' where controlinput = ' + "'" + controlinput + "'") 
                #print(controltime)
                #print(controlinput)
                pilib.sqlitequery(controldatabase, 'update channels set controlvaluetime=\'' + controltime + '\' where controlinput = ' + "'" + controlinput + "'") 
        
        else:   # input is empty 
            pilib.sqlitequery(controldatabase,"update channels set statusmessage = \'No controlinput found '") 

            # disable channel
            #pilib.sqlitequery(controldatabase,"update channels set enabled=0 where controlinput = \'" + controlinput + "'") 

        # print(controlinput)
        # print(controltime)
        # print(controlvalue)

    ############################
    # Log value into tabled log

    # Get data for all sensors online
    
    inputsdata = pilib.readalldbrows(controldatabase,'inputsdata')
    for inputrow in inputsdata: 
        
        # Create table if it doesn't exist

        logtablename = 'input' + inputrow['id'] + 'log'
        query = 'create table if not exists ' + logtablename +  '( inputid text, value real, time text)'

        pilib.sqlitequery(logdatabase,query)

        # Enter row
        pilib.sqliteinsertsingle(logdatabase,logtablename,[inputrow['id'],inputrow['value'],inputrow['polltime']])

        # Size log based on specified size
  
        pilib.sizesqlitetable(logdatabase,logtablename,logpoints)

    #########################
    # log metadata
    pilib.getandsetmetadata(logdatabase)
    #print("sleeping")
    sleep(readtime)

pilib.sqlitequery(controldatabase, 'update systemstatus set inputsreadstatus=\'0\'')


    
