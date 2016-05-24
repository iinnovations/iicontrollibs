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


from iiutilities import utility
from iiutilities import dblib
from iiutilities import datalib
from cupid import pilib
from cupid import updateio
from time import sleep

readtime = 10  # default, seconds

"""
Read from systemstatus to make sure we should be running
"""

def runperiodicio():

    updateioenabled = dblib.getsinglevalue(pilib.dirs.dbs.system, 'systemstatus', 'updateioenabled')

    while updateioenabled:

        utility.log(pilib.dirs.logs.io, 'Running periodicupdateio', 3, pilib.loglevels.io)
        utility.log(pilib.dirs.logs.system, 'Running periodicupdateio', 3, pilib.loglevels.system)

        # Set last run time
        dblib.setsinglevalue(pilib.dirs.dbs.system, 'systemstatus', 'lastinputpoll', datalib.gettimestring())
        dblib.setsinglevalue(pilib.dirs.dbs.system, 'systemstatus', 'updateiostatus', '1')

        # Read and record everything as specified in dirs.dbs.control
        # Update database of inputs with read data

        # DEBUG
        runupdate = True
        if runupdate:
            reply = updateio.updateiodata(pilib.dirs.dbs.control)
        else:
            utility.log(pilib.dirs.logs.io, 'DEBUG: Update IO disabled', 1, pilib.loglevels.io)
            utility.log(pilib.dirs.log.system, 'DEBUG: Update IO disabled', 1, pilib.loglevels.system)


        result = dblib.readonedbrow(pilib.dirs.dbs.system, 'systemstatus', 0)
        systemsdict = result[0]
        #print("here is the systems dict")
        #print(systemsdict)
        readtime = systemsdict['updateiofreq']

        # defaults
        plotpoints = 20
        logpoints = 1000

        ###################################################
        # Update controlvalues in channels

        channels = dblib.readalldbrows(pilib.dirs.dbs.control, 'channels')
        for channel in channels:

            # Get controlinput for each channel
            channelname = channel['name']
            controlinput = channel['controlinput']
            # Get the input for the name from inputs info
            # Then get the value and readtime from the input if it
            # can be found

            if controlinput and controlinput not in ['none', 'None']:

                controlvalue = dblib.getsinglevalue(pilib.dirs.dbs.control, 'inputs', 'value', "name='" + controlinput + "'")
                controltime = dblib.getsinglevalue(pilib.dirs.dbs.control, 'inputs', 'polltime',
                                                   "name='" + controlinput + "'")

                # Only update channel value if value was found

                if controlvalue is not None:
                    # print('control value for channel ' + channelname + ' = ' + str(controlvalue))
                    dblib.setsinglevalue(pilib.dirs.dbs.control, 'channels', 'controlvalue', str(controlvalue), "controlinput='" + controlinput + "'")
                    # pilib.sqlitequery(pilib.dirs.dbs.control, 'update channels set controlvalue=' + str(
                    #     controlvalue) + ' where controlinput = ' + "'" + controlinput + "'")
                    dblib.setsinglevalue(pilib.dirs.dbs.control, 'channels', 'controlvaluetime', str(controltime), "controlinput='" + controlinput + "'")
                    # pilib.sqlitequery(pilib.dirs.dbs.control,
                    #                   'update channels set controlvaluetime=\'' + controltime + '\' where controlinput = ' + "'" + controlinput + "'")

            else:  # input is empty
                dblib.setsinglevalue(pilib.dirs.dbs.control, 'channels', 'statusmessage', 'No controlinput found', "name='" + channelname + "'")

                # disable channel
                #pilib.sqlitequery(dirs.dbs.control,"update channels set enabled=0 where controlinput = \'" + controlinput + "'")


        ####################################################
        # Log value into tabled log

        # Get data for all sensors online

        inputsdata = dblib.readalldbrows(pilib.dirs.dbs.control, 'inputs')
        for inputrow in inputsdata:
            logtablename = 'input_' + inputrow['id'] + '_log'

            if datalib.isvalidtimestring(inputrow['polltime']):
                # Create table if it doesn't exist


                query = 'create table if not exists \'' + logtablename + '\' ( value real, time text primary key)'
                dblib.sqlitequery(pilib.dirs.dbs.log, query)

                # Enter row
                dblib.sqliteinsertsingle(pilib.dirs.dbs.log, logtablename,
                                         valuelist=[inputrow['value'], inputrow['polltime']],
                                         valuenames=['value', 'time'])

                # Clean log
                dblib.cleanlog(pilib.dirs.dbs.log, logtablename)

                # Size log based on specified size

                dblib.sizesqlitetable(pilib.dirs.dbs.log, logtablename, logpoints)


        ####################################################
        # log metadata
        dblib.getandsetmetadata(pilib.dirs.dbs.log)

        utility.log(pilib.dirs.logs.io, 'Sleeping for ' + str(readtime), 1, pilib.loglevels.io)
        sleep(readtime)

        # Read from systemstatus to make sure we should be running
        updateioenabled = dblib.getsinglevalue(pilib.dirs.dbs.system, 'systemstatus', 'updateioenabled')

    dblib.setsinglevalue(pilib.dirs.dbs.system, 'systemstatus', 'updateiostatus', '0')

if __name__ == "__main__":
    runperiodicio()

