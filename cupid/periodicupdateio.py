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
        first_run=True

    # print("quiet : {}, {}, {} ".format(systemdb.settings['quiet'], logdb.settings['quiet'], controldb.settings['quiet']))

    while updateioenabled:

        # print(
        # "quiet2 : {}, {}, {} ".format(systemdb.settings['quiet'], logdb.settings['quiet'], controldb.settings['quiet']))

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

        systemsdict = systemdb.read_table_row('systemstatus', 0)[0]

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
        Update controlvalues in channels
        """

        channels = controldb.read_table('channels')
        for channel in channels:
            # Get controlinput for each channel
            channelname = channel['name']
            controlinput = channel['controlinput']

            # Get the input for the name from inputs info
            # Then get the value and readtime from the input if it
            # can be found

            if controlinput and controlinput not in ['none', 'None']:

                values = controldb.get_values('inputs', ['value', 'polltime'], condition="name='" + controlinput + "'")
                controlvalue = values['value']
                controlvalue = values['polltime']

                # Only update channel value if value was found
                # print('CONTROLVALUE: ', controlvalue)
                if controlvalue or controlvalue == 0:
                    # print('control value for channel ' + channelname + ' = ' + str(controlvalue))
                    controldb.set_single_value('channels', 'controlvalue', str(controlvalue), "controlinput='" + controlinput + "'", queue=True)
                    # pilib.sqlitequery(pilib.dirs.dbs.control, 'update channels set controlvalue=' + str(
                    #     controlvalue) + ' where controlinput = ' + "'" + controlinput + "'")
                    controldb.set_single_value('channels', 'controlvaluetime', str(controltime), "controlinput='" + controlinput + "'", queue=True)
                    # pilib.sqlitequery(pilib.dirs.dbs.control,
                    #                   'update channels set controlvaluetime=\'' + controltime + '\' where controlinput = ' + "'" + controlinput + "'")

            else:  # input is empty
                controldb.set_single_value('channels', 'statusmessage', 'No controlinput found', "name='" + channelname + "'", queue=True)

                # disable channel
                #pilib.sqlitequery(dirs.dbs.control,"update channels set enabled=0 where controlinput = \'" + controlinput + "'")

            if channel['controlsetpoint'] and channel['controlsetpoint'] not in ['none', 'None']:

                value = controldb.set_single_value('inputs', 'value', "name='" + channel['controlsetpoint'] + "'", queue=True)


                # Only update channel value if value was found
                if value or value==0:
                    # print('control value for channel ' + channelname + ' = ' + str(controlvalue))
                    controldb.set_single_value('channels', 'setpointvalue', str(value), "controlsetpoint='" + channel['controlsetpoint'] + "'", queue=True)

            if channel['enabledinput'] and channel['enabledinput'] not in ['none', 'None']:

                value = controldb.set_single_value('inputs', 'value', "name='" + channel['enabledinput'] + "'", queue=True)


                # Only update channel value if value was found
                if value or value==0:
                    # print('control value for channel ' + channelname + ' = ' + str(controlvalue))
                    controldb.set_single_value('channels', 'enabled', str(value), "enabledinput='" + channel['enabledinput'] + "'", queue=True)

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
                log_db.size_table(logtablename, logpoints)
            else:
                pass
                # print('invalid poll time')

        """
        log metadata
        """

        dblib.getandsetmetadata(pilib.dirs.dbs.log)

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
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == 'debug':
            runperiodicio(force_run=True, run_once=True, debug=True)
        elif sys.argv[1].lower() == 'force':
            runperiodicio(force_run=True)
        elif sys.argv[1].lower() == 'force_once':
            runperiodicio(force_run=True, run_once=True)
    else:
        runperiodicio()

