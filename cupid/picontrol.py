#!/usr/bin/python3

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


# Run the script periodically based on systemstatus

# This script does the following:
# Processes channels data into output settings and channels data (action, etc)
# Log data

# What it does not do:
# Read inputs (done by updateio, through periodicreadio)
# Set physical outputs (this is done by updateio)
from iiutilities import datalib, dblib
from cupid import pilib, controllib

control_db = pilib.cupidDatabase(pilib.dirs.dbs.control)
log_db = pilib.cupidDatabase(pilib.dirs.dbs.log)
system_db = pilib.cupidDatabase(pilib.dirs.dbs.system)

default_control_algorithm = {'minofftime': 0, 'minontime': 0, 'ondelay': 0, 'offdelay': 0}


def process_channel(**kwargs):

    systemstatus = system_db.read_table_row('systemstatus')[0]
    if 'channel' in kwargs:
        channel = kwargs['channel']
    elif 'channel_name' in kwargs:
        channels = control_db.read_table('channels', '"name"=\'' + kwargs['channel_name'] + "'")
        if len(channels) == 1:
            channel = channels[0]
        else:
            print('wrong number of channels returned. aborting')
            return


    # channelindex = str(int(channel['channelindex']))
    logtablename = 'channel' + '_' + channel['name'] + '_log'
    time = datalib.gettimestring()
    disableoutputs = True

    status_msg = channel['name'] + ': '

    log_tablenames = log_db.get_table_names()

    # Channel enabled means different things for different types of channels

    channel_condition = '"name"=\'{}\''.format(channel['name'])

    # Create log if it doesn't exist
    if logtablename not in log_tablenames:
        log_db.create_table(logtablename, pilib.schema.channel_datalog)

    if channel['type'] == 'local':

        if channel['enabled']:

            status_msg = ''
            try:
                setpoint_value = float(channel['setpoint_value'])
            except:
                channel['enabled'] = 0
                status_msg += 'Error with setpoint. Disabling'
                control_db.set_single_value('channels', 'enabled', 0, channel_condition)

            # Need to test for age of data. If stale or disconnected, invalidate
            try:
                process_value = float(channel['process_value'])
            except:
                status_msg += 'Invalid control value. Disabling channel. '
                channel['enabled'] = 0
                control_db.set_single_value('channels', 'enabled', 0, channel_condition)

        # Move forward if still enabled after error-checking
        if channel['enabled']:

            status_msg += 'Channel Enabled. '

            # TODO : look at channel auto mode.
            if channel['mode'] == 'auto':
                status_msg += 'Mode:Auto. '
                # print('running auto sequence')

                # run algorithm on channel

                response = controllib.runalgorithm(pilib.dirs.dbs.control, pilib.dirs.dbs.session, channel['name'])
                action = response[0]
                message = response[1]

                status_msg += ' ' + response[1] + ' '
                status_msg += 'Action: ' + str(action) + '. '

                # Set action in channel

                controllib.setaction(pilib.dirs.dbs.control, channel['name'], action)

            elif channel['mode'] == 'manual':
                # print('manual mode')
                status_msg += 'Mode:Manual. '
                action = controllib.getaction(pilib.dirs.dbs.control, channel['name'])
            else:
                # print('error, mode= ' + mode)
                status_msg += 'Mode:Error. '

            if systemstatus['enableoutputs']:
                status_msg += 'System outputs enabled. '
                if channel['outputs_enabled']:
                    status_msg += 'Channel outputs enabled. '
                    disableoutputs = False

                    # find out whether action is positive or negative or
                    # not at all.

                    # and act. for now, this is binary, but in the future
                    # this will be a duty cycle daemon

                    outputsetnames = []
                    outputresetnames = []
                    if action > 0:
                        print("set positive output on")
                        outputsetnames.append(channel['positive_output'])
                        outputresetnames.append(channel['negative_output'])
                    elif action < 0:
                        print("set negative output on")
                        outputsetnames.append(channel['negative_output'])
                        outputresetnames.append(channel['positive_output'])
                    elif action == 0:
                        status_msg += 'No action. '
                        outputresetnames.append(channel['positive_output'])
                        outputresetnames.append(channel['negative_output'])
                    else:
                        status_msg += 'Algorithm error. Doing nothing.'

                    # Check to see if outputs are ready to enable/disable
                    # If not, pull them from list of set/reset

                    control_algorithm = control_db.read_table('controlalgorithms', condition='"name"=\'' + channel['controlalgorithm'] + "'")
                    if len(control_algorithm) == 1:
                        algorithm = control_algorithm[0]
                    else:
                        status_msg += 'Algorithm Error: Not found (or multiple?). Using default. '
                        algorithm = default_control_algorithm

                    outputstoset = []
                    for outputname in outputsetnames:
                        offtime = control_db.get_single_value('outputs', 'offtime',
                                                              condition='"name"=\'' + outputname + "'")
                        if datalib.timestringtoseconds(
                                datalib.gettimestring()) - datalib.timestringtoseconds(offtime) > algorithm[
                            'minofftime']:
                            outputstoset.append(outputname)
                        else:
                            status_msg += 'Output ' + outputname + ' not ready to enable. '

                    outputstoreset = []
                    for outputname in outputresetnames:
                        ontime = control_db.get_single_value('outputs', 'ontime',
                                                             condition='"name"=\'' + outputname + "'")
                        if datalib.timestringtoseconds(
                                datalib.gettimestring()) - datalib.timestringtoseconds(ontime) > algorithm[
                            'minontime']:
                            outputstoreset.append(outputname)
                        else:
                            status_msg += 'Output ' + outputname + ' not ready to disable. '

                    """ TODO: Change reference to controlinputs to name rather than id. Need to double-check
                    enforcement of no duplicates."""

                    # Find output in list of outputs if we have one to set

                    time = datalib.gettimestring()
                    if len(outputstoset) > 0 or len(outputstoreset) > 0:
                        for output in outputs:
                            id_condition = '"id"=\'' + output['id'] + "'"
                            if output['name'] in outputstoset:

                                # check current status
                                currvalue = output['value']
                                if not currvalue:  # No need to set if otherwise. Will be different for analog out
                                    # set ontime
                                    control_db.set_single_value('outputs', 'ontime', time, id_condition, queue=True)
                                    # set value
                                    control_db.set_single_value('outputs', 'value', 1, id_condition, queue=True)
                                    status_msg += 'Output ' + output['name'] + ' enabled. '
                                else:
                                    status_msg += 'Output ' + output['name'] + ' already enabled. '

                            if output['name'] in outputstoreset:
                                # check current status
                                currvalue = output['value']
                                if currvalue:  # No need to set if otherwise. Will be different for analog out
                                    # set ontime
                                    control_db.set_single_value('outputs', 'offtime', time, id_condition,
                                                                queue=True)
                                    # set value
                                    control_db.set_single_value('outputs', 'value', 0, id_condition, queue=True)
                                    status_msg += 'Output ' + output['name'] + ' disabled. '
                                else:
                                    status_msg += 'Output ' + output['name'] + ' already disabled. '

                else:
                    status_msg += 'Channel outputs disabled. '
                    action = 0

            else:
                status_msg += 'System outputs disabled. '
                action = 0

            # Insert entry into control log
            insert = {'time': time, 'process_value': channel['process_value'],
                      'setpoint_value': channel['setpoint_value'],
                      'action': channel['action'], 'algorithm': channel['algorithm_name'],
                      'enabled': channel['enabled'],
                      'status_msg': status_msg}
            control_db.insert(logtablename, insert, queue=True)

            log_options = datalib.parseoptions(channel['log_options'])
            log_db.size_table(logtablename, **log_options)
        else:
            # Chanel is disabled. Need to do active disable here.
            pass

    elif channel['type'] == 'remote':
        status_msg += 'Remote channel. '

        if channel['pending']:

            from iiutilities.datalib import parseoptions, dicttojson
            status_msg += 'Processing pending action. '
            pending = parseoptions(channel['pending'])

            if 'setpoint_value' in pending:
                status_msg += 'processing setpoint_value. '
                # Get control output and have a look at it.
                input_name = channel['sv_input']

                # try:
                inputs = control_db.read_table('inputs', '"name"=\'' + input_name + "'")
                # except:
                #     status_msg += 'Inputs query error. '
                #     return status_msg

                if len(inputs) == 1:
                    input = inputs[0]
                else:
                    status_msg += 'wrong number of query items returned, length: ' + str(len(inputs)) + ' for query on input name: ' + input_name
                    print('ERROR: ' + status_msg)
                    return status_msg


                # write_to_input(input, value)
                if input['type'] == 'MBTCP':

                    input_id = input['id']

                    # Now, using this id, we can determine uniquely which MBTCP entry it came from
                    splits = input_id.split('_')
                    interfaceid = splits[0]
                    register = splits[1]
                    length = splits[2]

                    string_condition = dblib.string_condition_from_lists(['interfaceid', 'register', 'length'],
                                                                         [interfaceid, register, length])
                    input_mb_entry = control_db.read_table('modbustcp', string_condition)[0]

                    # Get IP address
                    address = control_db.get_single_value('interfaces', 'address',
                                                          '"id"=\'' + input_mb_entry['interfaceid'] + "'")

                    from iiutilities import netfun

                    if input_mb_entry['options']:
                        input_options = parseoptions(input_mb_entry['options'])
                        if 'scale' in input_options:
                            pending['setpoint_value'] = float(pending['setpoint_value'])/float(input_options['scale'])

                    try:
                        result = netfun.writeMBcodedaddresses(address, register, [float(pending['setpoint_value'])], convert=input_mb_entry['format'])
                    except:
                        status_msg += 'Error in modbus'
                    else:
                        if result['statuscode'] == 0:

                            # Clear pending setpoint_value
                            pending.pop('setpoint_value', None)
                            pending_string = dicttojson(pending)
                            print('setting pending in setpointvaleu mbtcp')

                            control_db.set_single_value('channels','pending',pending_string, channel_condition)
                        else:
                            status_msg += 'modbus write operation returned a non-zero status of ' + str(result['status'])

                elif input['type'] == 'MOTE':
                    mote_node = input['address'].split(':')[0]
                    mote_address = input['address'].split(':')[1]
                    if mote_node == '1':
                        message = '~setsv;' + mote_address + ';' + str(pending['setpoint_value'])
                    else:
                        message = '~sendmsg;' + str(mote_node) + ';;~setsv;' + mote_address + ';' + str(pending['setpoint_value'])

                    motes_db = pilib.cupidDatabase(pilib.dirs.dbs.motes)
                    from time import sleep
                    for i in range(2):
                        time = datalib.gettimestring(datalib.timestringtoseconds(datalib.gettimestring()) + i)
                        motes_db.insert('queued', {'queuedtime':time, 'message':message})

                    # Clear pending setpoint_value
                    pending.pop('setpoint_value', None)
                    pending_string = dicttojson(pending)
                    print('setting pending in setpoint_value mote')

                    control_db.set_single_value('channels', 'pending', pending_string, channel_condition)

            if 'enabled' in pending:
                status_msg += 'processing enabledvalue. '

                # Get control output and have a look at it.
                input_name = channel['enabled_input']

                try:
                    inputs = control_db.read_table('inputs', '"name"=\'' + input_name + "'")
                except:
                    status_msg += 'Inputs query error. '
                    return status_msg

                if len(inputs) == 1:
                    input = inputs[0]
                else:
                    status_msg += 'wrong number of query items returned, length: ' + str(len(inputs)) + '. '
                    return status_msg

                # write_to_input(input, value)
                if input['type'] == 'MBTCP':

                    input_id = input['id']

                    # Now, using this id, we can determine uniquely which MBTCP entry it came from
                    splits = input_id.split('_')
                    interfaceid = splits[0]
                    register = splits[1]
                    length = splits[2]

                    string_condition = dblib.string_condition_from_lists(
                        ['interfaceid', 'register', 'length'],
                        [interfaceid, register, length])
                    input_mb_entry = control_db.read_table('modbustcp', string_condition)[0]

                    # Get IP address
                    address = control_db.get_single_value('interfaces', 'address',
                                                          '"id"=\'' + input_mb_entry['interfaceid'] + "'")

                    from iiutilities import netfun
                    # print(address, register,input_mb_entry['format'], int(pending['enabled']))

                    if input_mb_entry['options']:
                        input_options = parseoptions(input_mb_entry['options'])


                    try:
                        result = netfun.writeMBcodedaddresses(address, register,
                                                              [int(pending['enabled'])],
                                                              convert=input_mb_entry['format'])
                    except:
                        status_msg += 'Error in modbus'
                    else:
                        if result['statuscode'] == 0:
                            status_msg += 'That seems to have worked ok?'
                            # Clear pending setpoint_value
                            pending.pop('enabled', None)
                            pending_string = dicttojson(pending)
                            print('setting pending in enabled mbtcp')
                            control_db.set_single_value('channels', 'pending', pending_string,
                                                        channel_condition)
                        else:
                            status_msg += 'modbus write operation returned a non-zero status of ' + str(
                                result['status'])

                elif input['type'] == 'MOTE':
                    mote_node = input['address'].split(':')[0]
                    mote_address = input['address'].split(':')[1]
                    if mote_node == '1':
                        message = '~setrun;' + mote_address + ';' + str(pending['enabled'])
                    else:
                        message = '~sendmsg;' + str(mote_node) + ';;~setrun;' + mote_address + ';' + str(
                            pending['enabled'])

                    motes_db = pilib.cupidDatabase(pilib.dirs.dbs.motes)
                    from time import sleep
                    for i in range(2):
                        time = datalib.gettimestring(datalib.timestringtoseconds(datalib.gettimestring() + i))
                        motes_db.insert('queued', {'queuedtime': time, 'message': message})

                    # Clear pending setpoint_value
                    pending.pop('enabled', None)
                    pending_string = dicttojson(pending)

                    control_db.set_single_value('channels', 'pending', pending_string, channel_condition)


        # Insert entry into control log
        insert = {'time': time, 'process_value': channel['process_value'],
                  'setpoint_value': channel['setpoint_value'],
                  'action': channel['action'], 'algorithm': channel['control_algorithm'],
                  'enabled': channel['enabled'],
                  'status_msg': status_msg}
        # print(insert)
        log_db.insert(logtablename, insert)

        # Size log
        log_options = datalib.parseoptions(channel['log_options'])
        log_db.size_table(logtablename, **log_options)


    # If active reset and we didn't set channel modes, disable outputs
    # Active reset is not yet explicitly declared, but implied

    if disableoutputs and channel['type'] not in ['remote']:
        status_msg += 'Disabling Outputs. '
        for id in [channel['positive_output'], channel['negative_output']]:
            control_db.set_single_value('outputs','value',0,'"id"=\'' + id + "'", queue=True)
            status_msg += 'Outputs disabled for id=' + id + '. '

    # Set status message for channel
    control_db.set_single_value('channels', 'status_message', status_msg, channel_condition, queue=True)

    # Set update time for channel
    control_db.set_single_value('channels', 'control_updatetime', time, channel_condition, queue=True)

    # Execute query
    control_db.execute_queue()
    return status_msg


def runpicontrol(runonce=False):
    from time import sleep
    from iiutilities import dblib
    from iiutilities import utility
    from cupid import pilib
    from iiutilities import datalib
    import actions
    from cupid import controllib

    control_db = pilib.cupidDatabase(pilib.dirs.dbs.control)
    log_db = pilib.cupidDatabase(pilib.dirs.dbs.log)
    system_db = pilib.cupidDatabase(pilib.dirs.dbs.system)

    systemstatus = system_db.read_table_row('systemstatus')[0]

    while systemstatus['picontrolenabled']:

        utility.log(pilib.dirs.logs.system, 'Running picontrol', 3, pilib.loglevels.system)
        utility.log(pilib.dirs.logs.control, 'Running picontrol', 3, pilib.loglevels.control)

        # Set poll date. While intuitively we might want to set this
        # after the poll is complete, if we error below, we will know
        # from this stamp when it barfed. This is arguably more valuable
        # then 'last time we didn't barf'

        system_db.set_single_value('systemstatus', 'lastpicontrolpoll', datalib.gettimestring())

        channels = control_db.read_table('channels')


        # Cycle through channels and set action based on setpoint
        # and algorithm if set to auto mode

        log_tablenames = log_db.get_table_names()

        for channel in channels:
            process_channel(channel=channel)

        # We do this system status again to refresh settings

        systemstatus = system_db.read_table_row('systemstatus')[0]

        # Note that these are also processed in cupiddaemon to catch things like whether this script is running
        # actions.processactions()

        # Wait for delay time
        #print('sleeping')
        # spilights.updatelightsfromdb(pilib.dirs.dbs.control, 'indicators')
        if runonce:
            break

        utility.log(pilib.dirs.logs.system, 'Picontrol Sleeping for ' + str(systemstatus['picontrolfreq']), 2, pilib.loglevels.system)
        utility.log(pilib.dirs.logs.control, 'Picontrol Sleeping for ' + str(systemstatus['picontrolfreq']), 2, pilib.loglevels.system)

        print('sleeping')
        sleep(systemstatus['picontrolfreq'])
        print('done sleeping')

    utility.log(pilib.dirs.logs.system, 'picontrol not enabled. exiting.', 1, pilib.loglevels.system)

if __name__ == "__main__":
    runpicontrol()