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


from time import sleep


# Run the script periodically based on systemstatus

# This script does the following:
# Processes channels data into output settings and channels data (action, etc)
# Log data

# What it does not do:
# Read inputs (done by updateio, through periodicreadio)
# Set physical outputs (this is done by updateio)


def runpicontrol(runonce=False):
    from utilities import dblib
    from utilities import utility
    from cupid import pilib
    from utilities import datalib
    from cupid import controllib

    systemstatus = dblib.readalldbrows(pilib.controldatabase, 'systemstatus')[0]

    while systemstatus['picontrolenabled']:

        utility.log(pilib.syslog, 'Running picontrol', 3, pilib.sysloglevel)
        utility.log(pilib.controllog, 'Running picontrol', 3, pilib.controlloglevel)

        # Set poll date. While intuitively we might want to set this
        # after the poll is complete, if we error below, we will know
        # from this stamp when it barfed. This is arguably more valuable
        # then 'last time we didn't barf'

        dblib.sqlitequery(pilib.controldatabase,
                          "update systemstatus set lastpicontrolpoll='" + datalib.gettimestring() + "'")

        channels = dblib.readalldbrows(pilib.controldatabase, 'channels')
        outputs = dblib.readalldbrows(pilib.controldatabase, 'outputs')
        controlalgorithms = dblib.readalldbrows(pilib.controldatabase, 'controlalgorithms')
        algorithmnames=[]
        for algorithm in controlalgorithms:
            algorithmnames.append(algorithm['name'])

        # Cycle through channels and set action based on setpoint
        # and algorithm if set to auto mode

        for channel in channels:
            statusmsg = ''
            querylist = []
            channelindex = str(int(channel['channelindex']))
            channelname = channel['name']
            logtablename = 'channel' + '_' + channel['name'] + '_log'
            time = datalib.gettimestring()
            disableoutputs = True

            # Make sure channel is enabled
            if channel['enabled']:
                # Create log if it doesn't exist
                query = 'create table if not exists \'' + logtablename + '\' (time text, controlinput text, controlvalue real, setpointvalue real, action real, algorithm text, enabled real, statusmsg text)'
                dblib.sqlitequery(pilib.logdatabase, query)

                statusmsg = ''
                if 'setpointvalue' in channel:
                    setpointvalue = float(channel['setpointvalue'])
                else:
                    statusmsg += 'No setpoint. '

                # Need to test for age of data. If stale or disconnected, invalidate
                if 'controlvalue' in channel:
                    try:
                        controlvalue = float(channel['controlvalue'])
                    except (ValueError, TypeError) as e:
                        statusmsg += 'Invalid control value. '
                        controllib.setcontrolvalue(pilib.controldatabase, channelname, 0)
                else:
                    statusmsg += 'No controlvalue. '

                # Test to see if key exists and is true
                if 'enabled' in channel:
                    if channel['enabled']:
                        pass
                    else:
                        statusmsg += 'Channel disabled. '
                else:
                    statusmsg += 'Error. Enabled key does not exist'

                mode = channel['mode']
                channelalgorithmname = channel['controlalgorithm']
                controlinput = channel['controlinput']
                logpoints = channel['logpoints']

                # Move forward if everything is defined for control
                if channel['enabled'] and 'controlvalue' in locals() and 'setpointvalue' in locals():

                    statusmsg += 'Channel Enabled. '

                    if mode == 'auto':
                        statusmsg += 'Mode:Auto. '
                        #print('running auto sequence')

                        # run algorithm on channel

                        response = controllib.runalgorithm(pilib.controldatabase, pilib.recipedatabase, channelname)
                        action = response[0]
                        message = response[1]

                        statusmsg += ' ' + response[1] + ' '
                        statusmsg += 'Action: ' + str(action) + '. '

                        # Set action in channel

                        controllib.setaction(pilib.controldatabase, channelname, action)

                    elif mode == 'manual':
                        #print('manual mode')
                        statusmsg += 'Mode:Manual. '
                        action = controllib.getaction(pilib.controldatabase, channelname)
                    else:
                        #print('error, mode= ' + mode)
                        statusmsg += 'Mode:Error. '

                    if systemstatus['enableoutputs']:
                        statusmsg += 'System outputs enabled. '
                        if channel['outputsenabled']:
                            statusmsg += 'Channel outputs enabled. '
                            disableoutputs = False

                            # find out whether action is positive or negative or
                            # not at all.

                            # and act. for now, this is binary, but in the future
                            # this will be a duty cycle daemon

                            outputsetnames = []
                            outputresetnames = []
                            if action > 0:
                                print("set positive output on")
                                outputsetnames.append(channel['positiveoutput'])
                                outputresetnames.append(channel['negativeoutput'])
                            elif action < 0:
                                print("set negative output on")
                                outputsetnames.append(channel['negativeoutput'])
                                outputresetnames.append(channel['positiveoutput'])
                            elif action == 0:
                                statusmsg += 'No action. '
                                outputresetnames.append(channel['positiveoutput'])
                                outputresetnames.append(channel['negativeoutput'])
                            else:
                                statusmsg += 'Algorithm error. Doing nothing.'
                                outputsetname = None

                            # Check to see if outputs are ready to enable/disable
                            # If not, pull them from list of set/reset

                            outputstoset=[]
                            for outputname in outputsetnames:
                                if channelalgorithmname in algorithmnames:
                                    offtime = dblib.sqlitedatumquery(pilib.controldatabase, "select offtime from outputs where name='" + outputname + "'")
                                    if datalib.timestringtoseconds(
                                            datalib.gettimestring()) - datalib.timestringtoseconds(offtime) > controlalgorithms[algorithmnames.index(channelalgorithmname)]['minofftime']:
                                        outputstoset.append(outputname)
                                    else:
                                        statusmsg += 'Output ' + outputname + ' not ready to enable. '
                                else:
                                    statusmsg += 'Algorithm Error: Not found. '

                            outputstoreset=[]
                            for outputname in outputresetnames:
                                if channelalgorithmname in algorithmnames:
                                    ontime = dblib.sqlitedatumquery(pilib.controldatabase, "select ontime from outputs where name='" + outputname + "'")
                                    if datalib.timestringtoseconds(
                                            datalib.gettimestring()) - datalib.timestringtoseconds(ontime) > controlalgorithms[algorithmnames.index(channelalgorithmname)]['minontime']:
                                        outputstoreset.append(outputname)
                                    else:
                                        statusmsg += 'Output ' + outputname + ' not ready to disable. '
                                else:
                                    statusmsg += 'Algorithm Error: Not found. '
                            """ TODO: Change reference to controlinputs to name rather than id. Need to double-check
                            enforcement of no duplicates."""

                            # Find output in list of outputs if we have one to set

                            time = datalib.gettimestring()
                            if len(outputstoset) > 0 or len(outputstoreset) > 0:
                                for output in outputs:
                                    if output['name'] in outputstoset:
                                        # check current status
                                        currvalue = output['value']
                                        if currvalue == 0: # No need to set if otherwise. Will be different for analog out
                                            # set ontime
                                            querylist.append('update outputs set ontime=\'' + time + '\' ' + 'where id=\'' + output['id'] + '\'')
                                            # set value
                                            querylist.append("update outputs set value = 1 where id='" + output['id'] + '\'')
                                            statusmsg += 'Output ' + output['name'] + ' enabled. '
                                        else:
                                            statusmsg += 'Output ' + output['name'] + ' already enabled. '

                                    if output['name'] in outputstoreset:
                                        # check current status
                                        currvalue = output['value']
                                        if currvalue == 1:  # No need to set if otherwise. Will be different for analog out
                                            # set ontime
                                            querylist.append('update outputs set offtime=\'' + time + '\' ' + 'where id=\'' + output['id'] + '\'')
                                            # set value
                                            querylist.append('update outputs set value = 0 where id=\'' + output['id'] + '\'')
                                            statusmsg += 'Output ' + output['name'] + ' disabled. '
                                        else:
                                            statusmsg += 'Output ' + output['name'] + ' already disabled. '

                        else:
                            statusmsg += 'Channel outputs disabled. '
                            action = 0

                    else:
                        statusmsg += 'System outputs disabled. '
                        action = 0

                    # Insert entry into control log
                    dblib.makesqliteinsert(pilib.logdatabase, logtablename, [time, controlinput, controlvalue, setpointvalue, action, channelalgorithmname, channel['enabled'], statusmsg])
                    dblib.sqliteinsertsingle(pilib.logdatabase, logtablename,
                                             [time, controlinput, controlvalue, setpointvalue, action, channelalgorithmname,
                                              channel['enabled'], statusmsg])

                    # Size log
                    dblib.sizesqlitetable(pilib.logdatabase, logtablename, logpoints)
                    # print(statusmsg)

            else:
                # print('channel not enabled')
                statusmsg += 'Channel not enabled. '

            # If active reset and we didn't set channel modes, disable outputs
            # Active reset is not yet explicitly declared, but implied

            if disableoutputs:
                statusmsg += 'Disabling Outputs. '
                for output in outputs:
                    if output['name'] in [channel['positiveoutput'], channel['negativeoutput']]:
                            # set value
                            querylist.append("update outputs set value = 0 where id='" + output['id'] + '\'')
                            statusmsg += 'Output ' + output['name'] + ' disabled. '


            # Set status message for channel
            # print(statusmsg)
            querylist.append('update channels set statusmessage=\'' + statusmsg + '\'' + 'where channelindex=' + channelindex)

            # Set update time for channel
            querylist.append('update channels set controlupdatetime=\'' + time + '\'' + 'where channelindex=' + channelindex)
            # Execute query

            dblib.sqlitemultquery(pilib.controldatabase, querylist)

        # We do this system status again to refresh settings
        systemstatus = dblib.readalldbrows(pilib.controldatabase, 'systemstatus')[0]

        from actions import processactions
        processactions()

        # Wait for delay time
        #print('sleeping')
        # spilights.updatelightsfromdb(pilib.controldatabase, 'indicators')
        if runonce:
            break

        utility.log(pilib.syslog, 'Picontrol Sleeping for ' + str(systemstatus['picontrolfreq']), 2, pilib.sysloglevel)
        utility.log(pilib.controllog, 'Picontrol Sleeping for ' + str(systemstatus['picontrolfreq']), 2, pilib.sysloglevel)
        sleep(systemstatus['picontrolfreq'])

    utility.log(pilib.syslog, 'picontrol not enabled. exiting.', 1, pilib.sysloglevel)

if __name__ == "__main__":
    runpicontrol()