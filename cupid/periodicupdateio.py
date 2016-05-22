#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2016, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

import os
import sys
import inspect

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)


from utilities import utility
from utilities import dblib
from utilities import datalib
from cupid import pilib
from cupid import updateio
from time import sleep

readtime = 10  # default, seconds

# Read from systemstatus to make sure we should be running
updateioenabled = dblib.getsinglevalue(pilib.controldatabase, 'systemstatus', 'updateioenabled')

while updateioenabled:

    utility.log(pilib.iolog, 'Running periodicupdateio', 3, pilib.iologlevel)
    utility.log(pilib.syslog, 'Running periodicupdateio', 3, pilib.sysloglevel)

    # Set last run time
    dblib.setsinglevalue(pilib.controldatabase, 'systemstatus', 'lastinputpoll', datalib.gettimestring())
    dblib.setsinglevalue(pilib.controldatabase, 'systemstatus', 'updateiostatus', '1')

    # Read and record everything as specified in controldatabase
    # Update database of inputs with read data

    # DEBUG
    runupdate = True
    if runupdate:
        reply = updateio.updateiodata(pilib.controldatabase)
    else:
        utility.log(pilib.iolog, 'DEBUG: Update IO disabled', 1, pilib.iologlevel)
        utility.log(pilib.syslog, 'DEBUG: Update IO disabled', 1, pilib.sysloglevel)


    result = dblib.readonedbrow(pilib.controldatabase, 'systemstatus', 0)
    systemsdict = result[0]
    #print("here is the systems dict")
    #print(systemsdict)
    readtime = systemsdict['updateiofreq']

    # defaults
    plotpoints = 20
    logpoints = 1000

    ################################################### 
    # Update controlvalues in channels

    channels = dblib.readalldbrows(pilib.controldatabase, 'channels')
    for channel in channels:

        # Get controlinput for each channel
        channelname = channel['name']
        controlinput = channel['controlinput']
        # Get the input for the name from inputs info
        # Then get the value and readtime from the input if it
        # can be found

        if controlinput and controlinput not in ['none', 'None']:

            controlvalue = dblib.getsinglevalue(pilib.controldatabase, 'inputs', 'value', "name='" + controlinput + "'")
            controltime = dblib.getsinglevalue(pilib.controldatabase, 'inputs', 'polltime',
                                               "name='" + controlinput + "'")

            # Only update channel value if value was found

            if controlvalue is not None:
                # print('control value for channel ' + channelname + ' = ' + str(controlvalue))
                dblib.setsinglevalue(pilib.controldatabase, 'channels', 'controlvalue', str(controlvalue), "controlinput='" + controlinput + "'")
                # pilib.sqlitequery(pilib.controldatabase, 'update channels set controlvalue=' + str(
                #     controlvalue) + ' where controlinput = ' + "'" + controlinput + "'")
                dblib.setsinglevalue(pilib.controldatabase, 'channels', 'controlvaluetime', str(controltime), "controlinput='" + controlinput + "'")
                # pilib.sqlitequery(pilib.controldatabase,
                #                   'update channels set controlvaluetime=\'' + controltime + '\' where controlinput = ' + "'" + controlinput + "'")

        else:  # input is empty
            dblib.setsinglevalue(pilib.controldatabase, 'channels', 'statusmessage', 'No controlinput found', "name='" + channelname + "'")

            # disable channel
            #pilib.sqlitequery(controldatabase,"update channels set enabled=0 where controlinput = \'" + controlinput + "'") 


    ####################################################
    # Log value into tabled log

    # Get data for all sensors online

    inputsdata = dblib.readalldbrows(pilib.controldatabase, 'inputs')
    for inputrow in inputsdata:
        logtablename = 'input_' + inputrow['id'] + '_log'

        if datalib.isvalidtimestring(inputrow['polltime']):
            # Create table if it doesn't exist


            query = 'create table if not exists \'' + logtablename + '\' ( value real, time text primary key)'
            dblib.sqlitequery(pilib.logdatabase, query)

            # Enter row
            dblib.sqliteinsertsingle(pilib.logdatabase, logtablename,
                                     valuelist=[inputrow['value'], inputrow['polltime']],
                                     valuenames=['value', 'time'])

            # Clean log
            dblib.cleanlog(pilib.logdatabase, logtablename)

            # Size log based on specified size

            dblib.sizesqlitetable(pilib.logdatabase, logtablename, logpoints)


    ####################################################
    # log metadata
    dblib.getandsetmetadata(pilib.logdatabase)

    utility.log(pilib.iolog, 'Sleeping for ' + str(readtime), 1, pilib.iologlevel)
    sleep(readtime)

    # Read from systemstatus to make sure we should be running
    updateioenabled = dblib.getsinglevalue(pilib.controldatabase, 'systemstatus', 'updateioenabled')

dblib.setsinglevalue(pilib.controldatabase, 'systemstatus', 'updateiostatus', '0')

