#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2014, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

# This script runs the input reading scripts 
# specified interval, sends to log, channels and plot dbs

# TODO: Update to include better logging

import pilib
import updateio
from time import sleep

readtime = 10  # default, seconds

# Read from systemstatus to make sure we should be running
updateioenabled = pilib.getsinglevalue(pilib.controldatabase, 'systemstatus', 'updateioenabled')

while updateioenabled:

    pilib.writedatedlogmsg(pilib.iolog, 'Running periodicupdateio', 3, pilib.iologlevel)
    pilib.writedatedlogmsg(pilib.systemstatuslog, 'Running periodicupdateio', 3, pilib.systemstatusloglevel)

    # Set last run time
    pilib.setsinglevalue(pilib.controldatabase, 'systemstatus', 'lastinputpoll', pilib.gettimestring())
    pilib.setsinglevalue(pilib.controldatabase, 'systemstatus', 'updateiostatus', '1')

    # Read and record everything as specified in controldatabase
    # Update database of inputs with read data

    # DEBUG
    runupdate = True
    if runupdate:
        reply = updateio.updateiodata(pilib.controldatabase)
    else:
        pilib.writedatedlogmsg(pilib.iolog,'DEBUG: Update IO disabled', 1, pilib.iologlevel)
        pilib.writedatedlogmsg(pilib.systemstatuslog,'DEBUG: Update IO disabled', 1, pilib.systemstatusloglevel)


    result = pilib.readonedbrow(pilib.controldatabase, 'systemstatus', 0)
    systemsdict = result[0]
    #print("here is the systems dict")
    #print(systemsdict)
    readtime = systemsdict['updateiofreq']

    # defaults
    plotpoints = 20
    logpoints = 1000

    ################################################### 
    # Update controlvalues in channels

    channels = pilib.readalldbrows(pilib.controldatabase, 'channels')
    for channel in channels:

        # Get controlinput for each channel
        channelname = channel['name']
        controlinput = channel['controlinput']
        # Get the input for the name from inputs info
        # Then get the value and readtime from the input if it
        # can be found

        if controlinput:

            controlvalue = pilib.getsinglevalue(pilib.controldatabase, 'inputs', 'value', "name='" + controlinput + "'")
            controltime = pilib.getsinglevalue(pilib.controldatabase, 'inputs', 'polltime',
                                               "name='" + controlinput + "'")

            # Only update channel value if value was found

            if controlvalue is not None:
                # print('control value for channel ' + channelname + ' = ' + str(controlvalue))
                pilib.setsinglevalue(pilib.controldatabase, 'channels', 'controlvalue', str(controlvalue), "controlinput='" + controlinput + "'")
                # pilib.sqlitequery(pilib.controldatabase, 'update channels set controlvalue=' + str(
                #     controlvalue) + ' where controlinput = ' + "'" + controlinput + "'")
                pilib.setsinglevalue(pilib.controldatabase, 'channels', 'controlvaluetime', str(controltime), "controlinput='" + controlinput + "'")
                # pilib.sqlitequery(pilib.controldatabase,
                #                   'update channels set controlvaluetime=\'' + controltime + '\' where controlinput = ' + "'" + controlinput + "'")

        else:  # input is empty
            pilib.setsinglevalue(pilib.controldatabase, 'channels', 'statusmessage', 'No controlinput found', "name='" + channelname + "'" )

            # disable channel
            #pilib.sqlitequery(controldatabase,"update channels set enabled=0 where controlinput = \'" + controlinput + "'") 


    ####################################################
    # Log value into tabled log

    # Get data for all sensors online

    inputsdata = pilib.readalldbrows(pilib.controldatabase, 'inputs')
    for inputrow in inputsdata:
        logtablename = 'input_' + inputrow['id'] + '_log'

        if pilib.isvalidtimestring(inputrow['polltime']):
            # Create table if it doesn't exist


            query = 'create table if not exists \'' + logtablename + '\' ( value real, time text primary key)'
            pilib.sqlitequery(pilib.logdatabase, query)

            # Enter row
            pilib.sqliteinsertsingle(pilib.logdatabase, logtablename,
                                     valuelist=[inputrow['value'], inputrow['polltime']],
                                     valuenames=['value', 'time'])

            # Clean log
            pilib.cleanlog(pilib.logdatabase, logtablename)

            # Size log based on specified size

            pilib.sizesqlitetable(pilib.logdatabase, logtablename, logpoints)


    ####################################################
    # log metadata
    pilib.getandsetmetadata(pilib.logdatabase)

    pilib.writedatedlogmsg(pilib.iolog,'Sleeping for ' + str(readtime), 1, pilib.iologlevel)
    sleep(readtime)

    # Read from systemstatus to make sure we should be running
    updateioenabled = pilib.getsinglevalue(pilib.controldatabase, 'systemstatus', 'updateioenabled')

pilib.setsinglevalue(pilib.controldatabase, 'systemstatus', 'updateiostatus', '0')

