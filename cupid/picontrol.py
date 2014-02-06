#!/usr/bin/env python

import pilib
import spilights
import controllib 
import RPi.GPIO as GPIO
from time import sleep
 
T=True
F=False
GPIO.setmode(GPIO.BCM)

# Run the script periodically based on systemstatus

systemstatus = pilib.readalldbrows(pilib.controldatabase,'systemstatus')[0]

while systemstatus['picontrolenabled']:
    
    # Set poll date. While intuitively we might want to set this
    # after the poll is complete, if we error below, we will know 
    # from this stamp when it barfed. This is arguably more valuable
    # then 'last time we didn't barf'

    pilib.sqlitequery(pilib.controldatabase,'update systemstatus set lastpicontrolpoll=\'' + pilib.gettimestring() + '\'')

    channels = pilib.readalldbrows(pilib.controldatabase,'channels')
    outputs = pilib.readalldbrows(pilib.controldatabase,'outputs')
    controlalgorithms = pilib.readalldbrows(pilib.controldatabase,'controlalgorithms')

    # Cycle through channels and set action based on setpoint
    # and algorithm if set to auto mode

    for channel in channels:
        statusmessage =''
        channelindex=str(int(channel['channelindex']))
        channelname=channel['name']
        logtablename=channel['name'] + '_log'
        time=pilib.gettimestring()

        # Make sure channel is enabled
        if channel['enabled']:

            query = 'create table if not exists \'' + logtablename + '\' (time text, controlinput text, controlvalue real, setpointvalue real, action real, algorithm text, enabled real, statusmessage text)'

            pilib.sqlitequery(pilib.logdatabase,query)

            statusmessage=''
            if 'setpointvalue' in channel:
                setpointvalue = float(channel['setpointvalue'])
            else:
                statusmessage+='No setpoint. '
 
            if 'controlvalue' in channel:
                controlvalue = float(channel['controlvalue'])
            else:
                statusmessage+= 'No controlvalue. '

            # Test to see if key exists and is true
            if 'enabled' in channel: 
                if channel['enabled']:
                    pass
                else:
                    statusmessage+= 'Channel disabled. '
            else:
                statusmessage+= 'Error. Enabled key does not exist'

            mode=channel['mode']
            algorithm = channel['controlalgorithm']
            controlinput = channel['controlinput']
            logpoints=channel['logpoints']

            if channel['enabled'] and 'controlvalue' in locals() and 'setpointvalue' in locals():
 
                # grab the names of the outputs for the channel
                # these could be things like 'output1', 'output2', etc.

                channeloutputnames=[]
                channeloutputnames.append(channel['positiveoutput'])
                channeloutputnames.append(channel['negativeoutput'])

                # create a dict array of just the outputs for this channe
                # this will ignore 'none' values in channeloutputnames
                # as there will not be an output of this name
 
                channeloutputs=[]
                for output in outputs:
                    if output['name'] in channeloutputnames:
                        channeloutputs.append(output) 

                statusmessage+='Channel Enabled. '

                if mode=='auto':
                    statusmessage+='Mode:Auto. '
                    #print('running auto sequence')

                    # run algorithm on channel

                    response = controllib.runalgorithm(pilib.controldatabase,pilib.recipedatabase, channelname)
                    action=response[0]
                    message=response[1]

                    statusmessage+= ' ' + response[1] + ' ' 
                    statusmessage+='Action: '+str(action)+ '. ' 

                    # Set action in channel
                
                    controllib.setaction(pilib.controldatabase,channelname,action)

                elif mode == 'manual':
                    #print('manual mode')
                    statusmessage+='Mode:Manual. '
                    action=controllib.getaction(pilib.controldatabase,channelname)
                else:
                    #print('error, mode= ' + mode)
                    statusmessage+='Mode:Error. '
                
                # Enable outputs if outputs are enabled:
                #  1. Globally     : systemstatus['enableoutputs']
                #  2. On channel   : channels['outputsenabled']
                #  3. Individually : outputs['enabled']

                if systemstatus['enableoutputs']:
                    statusmessage+='System outputs enabled. '
                    if channel['outputsenabled']:
                        statusmessage+='Channel outputs enabled. '

                        # find out whether action is positive or negative or
                        # not at all.

                        # and act. for now, this is binary, but in the future
                        # this will be a duty cycle daemon

                        if action > 0:
                            #print("set positive GPIO on")
                            outputsetname=channel['positiveoutput']
                        elif action < 0:
                            #print("set negative GPIO on")
			                outputsetname=channel['negativeoutput']
                        elif action ==0:
                            statusmessage+='No action. '
                            outputsetname=''
                        else:
                            statusmessage+='Algorithm error. '

                        # Initialize for find algorithm

                        gpionum=-1
                        outputactionlist=[]

                        # Find output in list of channeloutputs
                        for output in channeloutputs:
                            gpionum=int(output['address'])

                            # We found our output
                            # Check if it's ready to be set
                            # Add to GPIO action list and update controldatabase

                            if output['name']==outputsetname:
                                if controllib.checkifenableready(output['name'],outputs):
                                    outputactionlist.append([gpionum,T])

                                    # set ontime if the output is currently off

                                    if output['status'] == 0:
                                        ontime=pilib.gettimestring()
                                        pilib.sqlitequery(pilib.controldatabase,'update outputs set ontime=\'' + ontime +'\'' + 'where name=\'' + output['name'] + '\'')
                                        pilib.sqlitequery(pilib.controldatabase,'update outputs set status=1 ' + 'where name=\'' + output['name'] + '\'')

                                else:
                                    statusmessage+='Output ' + output['name'] + ' not ready to enable. '

                                # The output was not found in our list to be set (enabled)
                                # disable the output if it is ready to be disabled

                            else:
                                if controllib.checkifdisableready(output['name'],outputs):
                                    outputactionlist.append([gpionum,F])

                                    # set offtime if the output is currently on
                                    if output['status'] == 1:
                                        offtime=pilib.gettimestring()
                                        pilib.sqlitequery(pilib.controldatabase,'update outputs set offtime=\'' + offtime +'\'' + 'where name=\'' + output['name'] + '\'')
                                        pilib.sqlitequery(pilib.controldatabase,'update outputs set status=0 ' + 'where name=\'' + output['name'] + '\'')

                                else:
                                    statusmessage+='Output ' + output['name'] + ' not ready to disable. '

                            #print(outputactionlist)

                            # This bit used to be at the top, but it's not necessary if we're
                            # not acting on anything

                            #if outputactionlist:
                                # Setup RPi input/outputs
                                #for output in outputs:
                                    #GPIO.setup(int(output['GPIO']), GPIO.OUT)
                                    #GPIO.output(int(output['GPIO']), F)


                        for actionitem in outputactionlist:
                                GPIO.setup(actionitem[0], GPIO.OUT)
                                GPIO.output(actionitem[0], actionitem[1])
                                if actionitem[1]==T:
                                    statusmsg='enabled'

                                elif actionitem[1]==F:
                                    statusmsg='disabled'
                                    # set off time
                                statusmessage+='Output  (GPIO ' + str(actionitem[0]) + ') ' + statusmsg + '. '

                    else:
                        statusmessage+='Channel outputs disabled. '
                        #print('Channel outputs disabled. ')
                else:
                    statusmessage+='System outputs disabled. '
                    #print('System outputs disabled. ')
                    
                    # we should probably turn everything off here
                    for output in outputs:
                        if output['interface']=='GPIO' and output['type']=='GPIO':
                            #print('enabling GPIO')
                            GPIO.setup(int(output['address']), GPIO.OUT)    
                            GPIO.output(int(output['address']), F)    


                # Insert entry into control log
                pilib.sqliteinsertsingle(pilib.logdatabase,logtablename, [time, controlinput,controlvalue,setpointvalue,action,algorithm,channel['enabled'],statusmessage])

                # Size log 
                pilib.sizesqlitetable(pilib.logdatabase,logtablename,logpoints)
        else:
            statusmessage+='Channel not enabled. '

        # Set status message for channel
        pilib.sqlitequery(pilib.controldatabase,'update channels set statusmessage=\'' + statusmessage +'\'' + 'where channelindex=' + channelindex)

        # Set update time for channel 
        pilib.sqlitequery(pilib.controldatabase,'update channels set controlupdatetime=\'' + time +'\'' + 'where channelindex=' + channelindex)

    # Wait for delay time 
    #print('sleeping')

    spilights.updatelightsfromdb(pilib.controldatabase,'indicators')
    sleep(systemstatus['picontrolfreq'])

    # We do this system status again to refresh settings
    systemstatus = pilib.readalldbrows(pilib.controldatabase,'systemstatus')[0]
