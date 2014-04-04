#!/usr/bin/env python

import pilib
import spilights
import controllib
import RPi.GPIO as GPIO
from time import sleep

T = True
F = False
GPIO.setmode(GPIO.BCM)

# Run the script periodically based on systemstatus

# This script does the following:
# Processes channels data into output settings and channels data (action, etc)
# Log data

# What it does not do:
# Read inputs (done by updateio, through periodicreadio)
# Set physical outputs (this is done by updateio)

systemstatus = pilib.readalldbrows(pilib.controldatabase, 'systemstatus')[0]

while systemstatus['picontrolenabled']:

    # Set poll date. While intuitively we might want to set this
    # after the poll is complete, if we error below, we will know 
    # from this stamp when it barfed. This is arguably more valuable
    # then 'last time we didn't barf'

    pilib.sqlitequery(pilib.controldatabase,
                      'update systemstatus set lastpicontrolpoll=\'' + pilib.gettimestring() + '\'')

    channels = pilib.readalldbrows(pilib.controldatabase, 'channels')
    outputs = pilib.readalldbrows(pilib.controldatabase, 'outputs')
    controlalgorithms = pilib.readalldbrows(pilib.controldatabase, 'controlalgorithms')

    # Cycle through channels and set action based on setpoint
    # and algorithm if set to auto mode

    for channel in channels:
        statusmsg = ''
        querylist = []
        channelindex = str(int(channel['channelindex']))
        channelname = channel['name']
        logtablename = channel['name'] + '_log'
        time = pilib.gettimestring()

        # Get outputs to avoid multiple queries
        outputs = pilib.readalldbrows(pilib.controldatabase,'outputs')

        # Make sure channel is enabled
        if channel['enabled']:

            # Create log if it doesn't exist
            query = 'create table if not exists \'' + logtablename + '\' (time text, controlinput text, controlvalue real, setpointvalue real, action real, algorithm text, enabled real, statusmsg text)'

            pilib.sqlitequery(pilib.logdatabase, query)

            statusmsg = ''
            if 'setpointvalue' in channel:
                setpointvalue = float(channel['setpointvalue'])
            else:
                statusmsg += 'No setpoint. '

            if 'controlvalue' in channel:
                try:
                    controlvalue = float(channel['controlvalue'])
                except ValueError:
                    statusmsg += 'Invalid control value. '
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
            algorithm = channel['controlalgorithm']
            controlinput = channel['controlinput']
            logpoints = channel['logpoints']

            # Move forward if everything is defined for control
            if channel['enabled'] and 'controlvalue' in locals() and 'setpointvalue' in locals():

                # grab the names of the outputs for the channel
                # these could be things like 'output1', 'output2', etc.

                # channeloutputnames = []
                # channeloutputnames.append(channel['positiveoutput'])
                # channeloutputnames.append(channel['negativeoutput'])

                # create a dict array of just the outputs for this channe
                # this will ignore 'none' values in channeloutputnames
                # as there will not be an output of this name

                # channeloutputs = []
                # for output in outputs:
                #     if output['name'] in channeloutputnames:
                #         channeloutputs.append(output)

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
                    # action = controllib.getaction(pilib.controldatabase, channelname)
                else:
                    #print('error, mode= ' + mode)
                    statusmsg += 'Mode:Error. '

                if systemstatus['enableoutputs']:
                    statusmsg += 'System outputs enabled. '
                    if channel['outputsenabled']:
                        statusmsg += 'Channel outputs enabled. '

                        # find out whether action is positive or negative or
                        # not at all.

                        # and act. for now, this is binary, but in the future
                        # this will be a duty cycle daemon

                        outputsetnames = []
                        outputresetnames = []
                        if action > 0:
                            #print("set positive output on")
                            outputsetnames.append(channel['positiveoutput'])
                            outputresetnames.append(channel['negativeoutput'])
                        elif action < 0:
                            #print("set negative GPIO on")
                            outputsetnames.append(['negativeoutput'])
                            outputresetnames.append(['negativeoutput'])
                        elif action == 0:
                            statusmsg += 'No action. '
                            outputresetnames.append(['positiveoutput'])
                            outputresetnames.append(['negativeoutput'])
                        else:
                            statusmsg += 'Algorithm error. Doing nothing.'
                            outputsetname = None

                        # Find output in list of outputs if we have one to set
                        
                        # Temporary
                        readytoenable = True
                        time = pilib.gettimestring()
                        if len(outputsetnames) > 0 or len(outputresetnames)>0:
                            for output in outputs:
                                if output['name'] in outputsetnames > 0:
                                    # check current status
                                    currvalue = output['value']
                                    if currvalue == 0: # No need to set if otherwise. Will be different for analog out
                                        # Check if ready to enable
                                        if readytoenable:
                                            # set ontime
                                            querylist.append('update outputs set ontime=\'' + time + '\'' + 'where id=\'' + output['id'] + '\'')
                                            # set value
                                            querylist.append("update outputs set value = 1 where id='" + output['id'] + '\'')
                                            statusmsg += 'Output ' + output['name'] + ' enabled. '
                                        else:
                                            statusmsg += 'Output ' + output['name'] + ' not ready to enable. '
                                    statusmsg += 'Output ' + output['name'] + ' already enabled. '

                                if output['name'] in outputresetnames > 0:
                                    
                                    # check current status
                                    currvalue = output['value']
                                    if currvalue == 1: # No need to set if otherwise. Will be different for analog out
                                         # Check if ready to disable
                                         if readytoenable:
                                             # set ontime
                                             querylist.append('update outputs set ontime=\'' + time + '\'' + 'where id=\'' +
                                                      output['id'] + '\'')
                                             # set value
                                             querylist.append('update outputs set value = 0 where id=\'' + output['id'] + '\'')
                                             statusmsg += 'Output ' + output['name'] + ' disabled. '
                                         else:
                                             statusmsg += 'Output ' + output['name'] + ' not ready to disable. '
                                    statusmsg += 'Output ' + output['name'] + ' already disabled. '

                    else:
                        statusmsg += 'Channel outputs disabled. '
                        #print('Channel outputs disabled. ')
                        # Disable outputs, or leave alone?
                else:
                    statusmsg += 'System outputs disabled. '
                    #print('System outputs disabled. ')
                     # Disable outputs, or leave alone?

                # Insert entry into control log
                pilib.sqliteinsertsingle(pilib.logdatabase, logtablename,
                                         [time, controlinput, controlvalue, setpointvalue, action, algorithm,
                                          channel['enabled'], statusmsg])

                # Size log 
                pilib.sizesqlitetable(pilib.logdatabase, logtablename, logpoints)
                # print(statusmsg)
        else:
            print('i am actually here')
            statusmsg += 'Channel not enabled. '

        # Set status message for channel
        # print(statusmsg)
        querylist.append('update channels set statusmessage=\'' + statusmsg + '\'' + 'where channelindex=' + channelindex)

        # Set update time for channel 
        querylist.append('update channels set controlupdatetime=\'' + time + '\'' + 'where channelindex=' + channelindex)
        # Execute query

        pilib.sqlitemultquery(pilib.controldatabase, querylist)
    # Wait for delay time 
    #print('sleeping')

    # spilights.updatelightsfromdb(pilib.controldatabase, 'indicators')
    sleep(systemstatus['picontrolfreq'])

    # We do this system status again to refresh settings
    systemstatus = pilib.readalldbrows(pilib.controldatabase, 'systemstatus')[0]

    from processactions import processactions
    processactions()