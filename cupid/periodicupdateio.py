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


from iiutilities import utility
from iiutilities import datalib
from cupid import pilib
from cupid import updateio
from time import sleep

readtime = 10  # default, seconds

"""
Read from systemstatus to make sure we should be running
"""


def runperiodicio(**kwargs):

    settings = {'force_run': False, 'run_once': False, 'debug': False, 'quiet':True, 'logerrors':True}
    settings.update(kwargs)

    systemdb = pilib.cupidDatabase(pilib.dirs.dbs.system, **settings)
    logdb = pilib.cupidDatabase(pilib.dirs.dbs.log, **settings)
    controldb = pilib.cupidDatabase(pilib.dirs.dbs.control, **settings)


    if settings['force_run']:
        updateioenabled = True
    else:
        updateioenabled = systemdb.get_single_value('systemstatus', 'updateioenabled')


    if settings['debug']:
        pilib.set_debug()
        settings['quiet'] = False

    if updateioenabled:
        import pigpio
        pi = pigpio.pi()
        io_objects = {}
        first_run = True

    # print("quiet : {}, {}, {} ".format(systemdb.settings['quiet'], logdb.settings['quiet'], controldb.settings['quiet']))

    while updateioenabled:

        utility.log(pilib.dirs.logs.io, 'Running periodicupdateio', 3, pilib.loglevels.io)
        utility.log(pilib.dirs.logs.system, 'Running periodicupdateio', 3, pilib.loglevels.system)

        # Set last run time
        systemdb.set_single_value('systemstatus', 'lastupdateiopoll', datalib.gettimestring())
        systemdb.set_single_value('systemstatus', 'updateiostatus', '1')

        # Read and record everything as specified in dirs.dbs.control
        # Update database of inputs with read data

        # DEBUG
        runupdate = True
        if runupdate:
            try:
                reply = updateio.updateiodata(piobject=pi, io_objects=io_objects, first_run=first_run, settings=settings)
            except:
                import traceback
                formatted_lines = traceback.format_exc().splitlines()

                error_mail = utility.gmail()
                import socket
                hostname = socket.gethostname()
                error_mail.subject = 'Error running ioupdate on host ' + hostname + '. '
                error_mail.message = error_mail.subject + ' Traceback: ' + '\n'.join(formatted_lines)
                error_mail.send()

        else:
            utility.log(pilib.dirs.logs.io, 'DEBUG: Update IO disabled', 1, pilib.loglevels.io)
            utility.log(pilib.dirs.log.system, 'DEBUG: Update IO disabled', 1, pilib.loglevels.system)

        systemsdict = systemdb.read_table_row('systemstatus')[0]

        readtime = systemsdict['updateiofreq']

        """
        Defaults.
        TODO: We need to get these from a db entry that the user can set on the main control panel. These will live in
        the 'defaults' table. Imagine that.

        Then, we can set the logpoints for each input and channel. We'll store them in the ioinfo table
        """

        plotpoints = 20
        logpoints = 1000

        try:
            logsettings = logdb.read_table('logsettings')
            for setting in logsettings:
                if setting['item'] == 'defaultlogpoints':
                    logpoints = int(setting['value'])
                    # print('logpoints found and set to ' + str(logpoints))
        except:
            pass
            # print('not found or other error. oops. ')

        """
        Update process_values in channels
        """

        channels = controldb.read_table('channels')
        for channel in channels:
            # Get pv_input for each channel
            channelname = channel['name']
            pv_input = channel['pv_input']

            # Get the input for the name from inputs info
            # Then get the value and readtime from the input if it
            # can be found

            if pv_input and pv_input not in ['none', 'None']:

                values = controldb.get_values('inputs', ['value', 'polltime'], condition="name='" + pv_input + "'")
                if values:
                    process_value = values['value']
                    process_value_time = values['polltime']

                    # Only update channel value if value was found
                    # print('process_value: ', process_value)
                    if process_value or process_value == 0:
                        # print('control value for channel ' + channelname + ' = ' + str(process_value))
                        controldb.set_single_value('channels', 'process_value', str(process_value), "pv_input='" + pv_input + "'", queue=True)
                        # pilib.sqlitequery(pilib.dirs.dbs.control, 'update channels set process_value=' + str(
                        #     process_value) + ' where pv_input = ' + "'" + pv_input + "'")
                        controldb.set_single_value('channels', 'process_value_time', str(process_value_time), "pv_input='" + pv_input + "'", queue=True)
                        # pilib.sqlitequery(pilib.dirs.dbs.control,
                        #                   'update channels set process_valuetime=\'' + controltime + '\' where pv_input = ' + "'" + pv_input + "'")
                else:
                    print('input not found. ')

            else:  # input is empty
                controldb.set_single_value('channels', 'statusmessage', 'No pv_input found', "name='" + channelname + "'", queue=True)

                # disable channel
                #pilib.sqlitequery(dirs.dbs.control,"update channels set enabled=0 where pv_input = \'" + pv_input + "'")

            if channel['sv_input'] and channel['sv_input'] not in ['none', 'None']:

                value = controldb.set_single_value('inputs', 'value', "name='" + channel['sv_input'] + "'", queue=True)

                # Only update channel value if value was found
                if value or value==0:
                    # print('control value for channel ' + channelname + ' = ' + str(process_value))
                    controldb.set_single_value('channels', 'setpoint_value', str(value), "sv_input='" + channel['sv_input'] + "'", queue=True)

            if channel['enabled_input'] and channel['enabled_input'] not in ['none', 'None']:

                value = controldb.set_single_value('inputs', 'value', "name='" + channel['enabled_input'] + "'", queue=True)


                # Only update channel value if value was found
                if value or value==0:
                    # print('control value for channel ' + channelname + ' = ' + str(process_value))
                    controldb.set_single_value('channels', 'enabled', str(value), "enabled_input='" + channel['enabled_input'] + "'", queue=True)

        if controldb.queued_queries:
            controldb.execute_queue()

        """
        Log value into tabled log

        Get data for all sensors online
        """

        inputsdata = controldb.read_table('inputs')
        for inputrow in inputsdata:
            logtablename = 'input_' + inputrow['id'] + '_log'
            utility.log(pilib.dirs.logs.io, 'Logging: ' + logtablename, 5, pilib.loglevels.io)
            # print( 'Logging: ' + logtablename, 5, pilib.loglevels.io)

            if datalib.isvalidtimestring(inputrow['polltime']):
                # Create table if it doesn't exist

                # query = 'create table if not exists \'' + logtablename + '\' ( value real, time text primary key)'
                # print('we are logging')

                log_db = pilib.cupidDatabase(pilib.dirs.dbs.log, **settings)

                # Includes 'if not exists' , so will not overwrite
                log_db.create_table(logtablename, pilib.schema.standard_datalog, dropexisting=False, queue=True)
                # dblib.sqlitequery(pilib.dirs.dbs.log, query)

                # Enter row
                insert = {'time':inputrow['polltime'], 'value':inputrow['value']}
                log_db.insert(logtablename, insert, queue=True)

                # query = dblib.makesqliteinsert(logtablename, [inputrow['value'], inputrow['polltime']],['value', 'time'])
                # dblib.sqlitequery(pilib.dirs.dbs.log, query)

                # print(log_db.queued_queries)
                log_db.execute_queue()

                # Clean log
                log_db.clean_log(logtablename)

                # Size log based on specified size
                log_options = datalib.parseoptions(inputrow['log_options'])
                log_db.size_table(logtablename, **log_options)
            else:
                pass
                # print('invalid poll time')

        """
        log metadata
        """

        pilib.get_and_set_logdb_metadata(pilib.dirs.dbs.log)

        if not settings['run_once']:
            utility.log(pilib.dirs.logs.io, 'Sleeping for ' + str(readtime), 1, pilib.loglevels.io)
            sleep(readtime)
        else:
            break

        if not settings['force_run']:
            # Read from systemstatus to make sure we should be running
            updateioenabled = systemdb.get_single_value('systemstatus', 'updateioenabled')

        # Signal to io reads that we just started.
        first_run = False

    systemdb.set_single_value('systemstatus', 'updateiostatus', '0')

if __name__ == "__main__":
    debug = False
    force = False
    run_once = False
    if 'debug' in sys.argv:
        print('running in debug')
        debug = True
    if 'force' in sys.argv:
        print('running force')
        force = True
    if 'run_once' in sys.argv:
        print('running run_once')
        run_once = True
    runperiodicio(debug=debug, force=force, run_once=run_once)

