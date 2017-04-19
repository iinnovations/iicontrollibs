#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2016, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

import inspect
import os
import sys

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)


def updateiodata(**kwargs):
    """
    updateiodata

    This recreates all input and output tables based on the interfaces table.
    This way we don't keep around stale data values. We could at some point incorporate
    a retention feature that keeps them around in case they disappear temporarily.
    It also reads the elements if they are enabled and it's time to read them

    """

    from cupid import pilib
    from iiutilities import dblib, utility, datalib

    import traceback

    if 'piobject' in kwargs:
        pi = kwargs['piobject']
    else:
        import pigpio
        pi = pigpio.pi()

    if 'io_objects' in kwargs:
        io_objects = kwargs['io_objects']
    else:
        # print('WARNING, NO io_objects PASSED')
        io_objects ={}

    allowedGPIOaddresses = [18, 23, 24, 25, 4, 17, 27, 22, 5, 6, 13, 19, 26, 16, 20, 21, 35]

    logconfig = pilib.reload_log_config()

    # Defaults
    settings = {'database':pilib.dirs.dbs.control, 'debug':False}
    settings.update(kwargs)

    if settings['debug']:
        pilib.set_debug()

    control_db = dblib.sqliteDatabase(settings['database'])
    io_info = control_db.read_table('ioinfo')

    tables = control_db.get_table_names()
    interfaces = control_db.read_table('interfaces')

    # TODO: Sort interfaces to put aux values at the end and prioritize reads. Maybe a priority field?

    # TODO: just .. .clean this all up wtih objects.
    last_data = utility.Bunch()
    last_data.interfaces = interfaces
    last_data.inputs = control_db.read_table('inputs')
    last_data.outputs = control_db.read_table('outputs')
    last_data.indicators = control_db.read_table('indicators')

    defaults = control_db.read_table('defaults')

    defaultinputpollfreq = 60
    defaultoutputpollfreq = 60
    if 'defaults' in tables:
        defaults = control_db.read_table('defaults')

        for default in defaults:
            if default['valuename'] == 'defaultinputpollfreq':
                try:
                    defaultinputpollfreq = float(default['value'])
                except:
                    pass
            elif default['valuename'] == 'defaultoutputpollfreq':
                try:
                    defaultoutputpollfreq = float(default['value'])
                except:
                    pass

    previndicators = []
    indicatornames = []

    # We drop all inputs and outputs and recreate
    # Add all into one query so there is no time when the IO don't exist.

    control_db.empty_table('inputs',queue=True)
    control_db.empty_table('outputs',queue=True)

    '''
    This is temporary. Clearing the table here and adding entries below can result in a gap in time
    where there are no database indicator entries. This is not too much of a problem with indicators, as we
    update the hardware explicitly after we add the entries. If the interface queries the table during
    this period, however, we could end up with an apparently empty table.
    TODO: FIX update on indicators in updateio
    '''

    # We drop this table, so that if SP1 has been disabled, the entries do not appear as valid indicators
    control_db.empty_table('indicators')

    owfsupdate = False
    # Unfortunately, we need to keep track of the IDs we are creating, so we don't run them over as we go

    interfaceids = []
    for interface in interfaces:
        # print(interface)
        if interface['interface'] == 'I2C':
            utility.log(pilib.dirs.logs.io, 'Processing I2C interface ' + interface['name'], 3,
                        pilib.loglevels.io)
            if interface['enabled']:
                utility.log(pilib.dirs.logs.io, 'I2C Interface ' + interface['name'] + ' enabled', 3,
                            pilib.loglevels.io)
                if interface['type'] == 'DS2483':
                    utility.log(pilib.dirs.logs.io, 'Interface type is DS2483', 3,
                                pilib.loglevels.io)
                    owfsupdate = True
                elif interface['type'] in ['ADS1115', 'ADS1015']:
                    result = process_ads1x15_interface(interface)
                    if not result['status']:
                        name = get_or_insert_iface_metadata(interface['id'], io_info, control_db)['name']

                        input_entry = {'id':interface['id'], 'interface':interface['interface'], 'type':interface['type'],
                                                'address':interface['address'], 'name':name, 'value':result['value'],
                                                'polltime':result['readtime'], 'pollfreq':defaultinputpollfreq}
                        control_db.insert('inputs', input_entry, queue=True)

            else:
                 utility.log(pilib.dirs.logs.io, 'I2C Interface ' + interface['name'] + ' disabled', 3,
                             pilib.loglevels.io)
        elif interface['interface'] == 'USB':
            utility.log(pilib.dirs.logs.io, 'Processing USB interface ' + interface['name'], 3,
                        pilib.loglevels.io)
            if interface['enabled']:
                utility.log(pilib.dirs.logs.io, 'USB Interface ' + interface['name'] + ' enabled', 3,
                            pilib.loglevels.io)
                if interface['type'] == 'DS9490':
                    utility.log(pilib.dirs.logs.io, 'Interface type is DS9490', 3,
                                pilib.loglevels.io)
                    owfsupdate = True
                elif interface['type'] in ['U6', 'U3', 'U9', 'U12']:
                    utility.log(pilib.dirs.logs.io, 'Interface type is LabJack of type: ' + interface['type'], 3, pilib.loglevels.io)
                    # address = int(interface['address'])

                    valueentries = processlabjackinterface(control_db, interface, last_data, io_info)

                    # print(valueentries)
                    if valueentries:
                        control_db.queue_queries(valueentries)

            else:
                 utility.log(pilib.dirs.logs.io, 'USB Interface ' + interface['name'] + ' disabled', 3,
                             pilib.loglevels.io)
        elif interface['interface'] == 'AUX':

            # For aux variables, need to decide how to do polltime. For a single value translation, this is easy.
            # For multiple values, we need to somehow annotate the time difference, average times together ... something
            # The address of the interface will be unique and determine the ID of the input.
            entryid = interface['interface'] + '_' + interface['type'] + '_' + interface['address']

            condition = '"interface"=\'' + interface['interface'] + '\' and "type"=\'' + interface['type'] + '\' and "address"=\'' + interface['address'] + '\''

            # print(condition)
            dblib.setsinglevalue(pilib.dirs.dbs.control, 'interfaces', 'id', entryid, condition)

            # Does this entry already exist in inputs?
            prev_meta = get_or_insert_iface_metadata(entryid, io_info, control_db)
            name = prev_meta['name']

            if interface['type'] == 'ratecounter':

                # All we do here is specify an input ID
                # try:
                options = datalib.parseoptions(interface['options'])
                rateresult = datalib.calcinputrate(options['inputid'])
                if rateresult:
                    value = rateresult['rate']
                    readtime = rateresult['ratetime']
                    # except:
                    #
                    #     value = 'NaN'
                    #     readtime =''
                    # else:
                    # print('RATE COUNTER SUCCESS')
                    if 'formula' in options:
                        try:
                            adjustedrate = datalib.calcastevalformula(options['formula'].replace('x', str(value)))
                        except:
                            pass
                        else:
                            value = adjustedrate

                    # TODO: Handle pollfreq appropriately.
                    input_entry = {'id':entryid, 'interface':interface['interface'], 'type':interface['type'],
                                                'address':interface['address'], 'name':name, 'value':value,
                                                'polltime':str(readtime), 'pollfreq':defaultinputpollfreq}
                    control_db.insert('inputs', input_entry, queue=True)

                    # query = dblib.makesqliteinsert('inputs', [entryid, interface['interface'], interface['type'],
                    #       interface['address'], name, str(value), '', str(readtime),
                    #       str(defaultinputpollfreq), '', ''])
                    # querylist.append(query)
                else:
                    # print('BAD RATE COUNTER VALUE')
                    utility.log(pilib.dirs.logs.io, 'Rate data returned None. Beginning of data set?')

            if interface['type'] in ['value', 'formula']:
                """
                At the moment, both single value and complex formula translation are done here. These may fork as
                necessary.

                By default, the formula or value is assigned a readtime of NOW. This is principally bad: the value is
                guaranteed to be wrong. Best case scenario, and one we hope to fall back to by putting the aux value
                processing last, is that these values are calculated IMMEDIATELY after data is read. Still, these read
                operations take time. The worst case scenario is when we have a poll time that is significant, and we
                do not post-process an aux value until next time the poll is run. In this case, the aux value's time
                stamp will be systemically offset by the polling period.

                To mitigate this, we allow pulling a timestamp from an arbitrary location using the 'timestamp' keyword
                in the options field. If this fails, we will fall back gracefully to NOW. Note that the function
                'dbvntovalue' is used rather than the formula, which only returns float values and will barf on a
                timestamp.
                """

                readtime = datalib.gettimestring()
                options = []
                try:
                    options = datalib.parseoptions(interface['options'])
                    # print(options['formula'])
                    value = datalib.evaldbvnformula(options['formula'])

                    if 'minvalue' in options:
                        try:
                            if value < float(options['minvalue']):
                                value = float(options['minvalue'])
                        except:
                            pass
                    if 'maxvalue' in options:
                        try:
                            if value > float(options['maxvalue']):
                                value = float(options['maxvalue'])
                        except:
                            pass
                    if 'readtime' in options:
                        try:
                            # we grab a string time from where we are told
                            exttime = dblib.dbvntovalue(options['readtime'])
                        except:
                            pass
                            # print('Fail with time entry: ' + options['readtime'])
                        else:
                            if datalib.isvalidtimestring(exttime):
                                # print('SUCCESS ON EXT TIME, yielded: ' + exttime)
                                readtime = exttime

                except:
                    pass
                    # print("error calculating aux value")
                else:
                    input_entry = {'id': entryid, 'interface': interface['interface'], 'type': interface['type'],
                                   'address': interface['address'], 'name': name, 'value': value,
                                   'polltime': str(readtime), 'pollfreq': defaultinputpollfreq}
                    control_db.insert('inputs', input_entry, queue=True)

        elif interface['interface'] == 'MOTE':

            # TODO: My god this needs to be in a sub
            #determine and then update id based on fields
            try:
                entryid = interface['interface'] + '_' + interface['type'] + '_' + interface['address']
            except:
                print('error with entryid + ',interface['interface'], interface['type'], interface['address'])
            interfaceids.append(entryid)

            condition = '"interface"=\'' + interface['interface'] + '\' and "type"=\'' + interface['type'] + '\' and "address"=\'' + interface['address'] + '\''

            # print(condition)
            # Immediately?
            control_db.set_single_value('interfaces', 'id', entryid, condition)

            utility.log(pilib.dirs.logs.io, 'Processing Mote interface ' + interface['name'] + ', id:' + entryid, 3,
                        pilib.loglevels.io)
            if interface['enabled']:
                utility.log(pilib.dirs.logs.io, 'Mote Interface ' + interface['name'] + ', id:' + entryid + ' enabled', 3,
                            pilib.loglevels.io)

                # TODO: put this all in a subroutine

                '''
                Grab mote entries from remotes table
                nodeid and keyvalue are keyed into address in remotes table
                keyvalues are :
                  channel: channel number
                  iovalue: ionumber
                  owdev: ROM


                This would look like, for example
                1:1 for a nodeid:channel scenario for a controller
                '''

                split = interface['address'].split(':')
                nodeid = split[0]
                if len(split) > 1:
                    keyvalue = split[1]
                else:
                    keyvalue = '*'

                '''
                so we used to enable an interface and then take all entries from a node
                Now, we have to explicitly add an interface for each device, unless the keychar * is used as the
                keyvalue. This will allow us to insert all automatically, for example for owdevs or iovals from a
                node.

                This pulls out all mote entries that have nodeid and keyvalue that match the interface address
                We should just find one, ideally
                '''

                if keyvalue == '*':
                    nodeentries =  control_db.read_table('remotes', condition='"nodeid"=\'' + nodeid + "'")
                else:
                    condition = "\"nodeid\"='" + nodeid + "' and \"keyvalue\"='" + keyvalue + "'"
                    nodeentries = control_db.read_table('remotes', condition=condition)

                # print(nodeentries)
                # print("WE FOUND MOTE")
                # print(condition)
                # print(len(nodeentries))

                if interface['type'] == 'channel':
                    # print('channel')
                    if len(nodeentries) == 1:
                        # print('one entry found')

                        nodeentry = nodeentries[0]
                        nodedata = datalib.parseoptions(nodeentry['data'])

                        newchanneldata = {'name':interface['name'],'controlvaluetime': datalib.gettimestring(), 'data':nodeentry['data'], 'type': 'remote'}

                        if 'svcmd' in nodedata:
                            # Delete from node data
                            nodedata.pop('svcmd',None)

                            # Delete from remotes data by inserting entry without svcmd
                            control_db.set_single_value('remotes','data',utility.dicttojson(nodedata), condition=condition)

                            # Nuke pending entry
                            newchanneldata['pending'] = ''

                        findentries = ['sv', 'pv', 'prop']
                        findentrydictnames = ['setpointvalue', 'controlvalue', 'action', 'pending']

                        # Insert if found, otherwise leave untouched.
                        for entry, entryname in zip(findentries, findentrydictnames):
                            if entry in nodedata:
                                newchanneldata[entryname] = nodedata[entry]

                        # Find existing channel so we can get existing data, settings, etc., and retain channel ordering
                        # TODO: Reorder starting at 1 for when things get wonky

                        newchannel = {}
                        existingchannels = control_db.read_table('channels')
                        for channel in existingchannels:
                            if channel['name'] == interface['name']:
                                # print('updating')
                                # print(channel)
                                newchannel.update(channel)
                                # print(newchannel)
                        newchannel.update(newchanneldata)
                        # # print(newchannel)
                        #
                        # keys = []
                        # values = []
                        # for key, value in newchannel.iteritems():
                        #     keys.append(key)
                        #     values.append(value)

                        control_db.insert('channels',newchannel)
                        # query = dblib.makesqliteinsert('channels', values, keys)
                        # print(query)
                        # dblib.sqlitequery(pilib.dirs.dbs.control, query)
                    else:
                        # print('multiple entries found for channel. not appropriate')
                        pass
                else:
                    # Create queries for table insertion
                    # TODO: process mote pollfreq, ontime, offtime
                    for nodeentry in nodeentries:

                        # THis breaks out all of the strictly json-encoded data.
                        datadict = datalib.parseoptions(nodeentry['data'])
                        try:
                            entrytype = nodeentry['msgtype']

                            # now treat each mote type entry specially
                            # if entrytype == 'channel':

                            entryid = 'MOTE' + str(nodeentry['nodeid']) + '_' + nodeentry['keyvaluename']

                            default_name = '[MOTE' + str(nodeentry['nodeid']) + '] ' + nodeentry['keyvaluename']
                            address = nodeentry['nodeid']
                            entry_meta = get_or_insert_iface_metadata(id, io_info, control_db, default_name)
                            entry_options = datalib.parseoptions(entry_meta['options'])

                        except KeyError:
                            print('OOPS KEY ERROR')
                            pass
                        else:
                            if entrytype == 'iovalue':
                                if 'scale' in entry_options:
                                    entryvalue = str(float(entry_options['scale']) * float(datadict['ioval']))
                                elif 'formula' in entry_options:
                                    x = float(datadict['ioval'])
                                    try:
                                        entryvalue = eval(entry_options['formula'])
                                    except:
                                        entryvalue = float(datadict['ioval'])
                                else:
                                    entryvalue = float(datadict['ioval'])
                            elif entrytype == 'owdev':
                                if 'owtmpasc' in datadict:
                                    if 'scale' in entry_options:
                                        entryvalue = str(float(entry_options['scale']) * float(datadict['owtmpasc']))
                                    elif 'formula' in entry_options:
                                        x = float(datadict['owtmpasc'])
                                        try:
                                            entryvalue = eval(entry_options['formula'])
                                        except:
                                            entryvalue = float(datadict['owtmpasc'])
                                    else:
                                        entryvalue = datadict['owtmpasc']
                                else:
                                    entryvalue = -1
                            else:
                                entryvalue = nodeentry['keyvalue']

                            # TODO: Properly handle pollfreq for motes
                            mote_insert = {'id': entryid, 'interface': interface['interface'], 'type': interface['type'],
                                   'address': address, 'name': entry_meta['name'], 'value': entryvalue,
                                   'polltime': nodeentry['time'], 'pollfreq':15}
                            # print('ENTRY')
                            # print(mote_insert)
                            control_db.insert('inputs', mote_insert, queue=True)
                            # moteentries.append("insert into inputs values ('" + entryid + "','" + interface['interface'] + "','" +
                            #     interface['type'] + "','" + str(address) + "','" + entryname + "','" + str(entryvalue) + "','','" +
                            #      nodeentry['time'] + "','" + str(15) + "','" + '' + "','" + '' + "')")

            else:
                utility.log(pilib.dirs.logs.io, 'Mote Interface ' + interface['name'] + ' disnabled', 3,
                            pilib.loglevels.io)
        elif interface['interface'] == 'LAN':
            utility.log(pilib.dirs.logs.io, 'Processing LAN interface ' + interface['name'], 3,
                        pilib.loglevels.io)
            if interface['enabled']:
                utility.log(pilib.dirs.logs.io, 'LAN Interface ' + interface['name'] + ' enabled', 3,
                            pilib.loglevels.io)
                if interface['type'] == 'MBTCP':
                    utility.log(pilib.dirs.logs.io, 'Interface ' + interface['name'] + ' type is MBTCP',
                                3, pilib.loglevels.io)

                    try:
                        mbentries = processMBinterface(control_db, interface, last_data, io_info, defaults)
                    except:
                        utility.log(pilib.dirs.logs.io,
                                               'Error processing MBTCP interface ' + interface['name'], 0,
                                    pilib.loglevels.io)
                        errorstring = traceback.format_exc()
                        utility.log(pilib.dirs.logs.io, 'Error of kind: ' + errorstring, 0,
                                    pilib.loglevels.io)
                    else:
                        utility.log(pilib.dirs.logs.io,'Done processing MBTCP interface ' + interface['name'], 3,
                                    pilib.loglevels.io)
                        control_db.queue_queries(mbentries)
            else:
                utility.log(pilib.dirs.logs.io, 'LAN Interface ' + interface['name'] + ' disabled', 3, pilib.loglevels.io)
        elif interface['interface'] == 'GPIO':
            try:
                address = int(interface['address'])
            except KeyError:
                utility.log(pilib.dirs.logs.io, 'GPIO address key not found for ' + interface['name'], 1,
                            pilib.loglevels.io)
                continue
            if interface['enabled']:

                utility.log(pilib.dirs.logs.io, 'Processing GPIO interface ' + str(interface['address']), 3,
                            pilib.loglevels.io)

                if address in allowedGPIOaddresses:
                    utility.log(pilib.dirs.logs.io, 'GPIO address' + str(address) + ' allowed. Processing.', 4,
                                pilib.loglevels.io)
                    try:
                        GPIOentries = processGPIOinterface(control_db, interface, last_data, io_info, defaults, piobject=pi, io_objects=io_objects)
                    except:
                        utility.log(pilib.dirs.logs.io,
                                           "ERROR handling GPIO interface " + str(address) + '. ', 0,  pilib.loglevels.io)
                        print traceback.format_exc()
                        GPIOentries = []
                    else:
                        if settings['debug']:
                            print(GPIOentries)
                    if GPIOentries:
                        control_db.queue_queries(GPIOentries)
                else:
                    utility.log(pilib.dirs.logs.io,
                                           'GPIO address' + str(address) + ' not allowed. Bad things can happen. ', 4,
                                pilib.loglevels.io)

            else:
                utility.log(pilib.dirs.logs.io, 'GPIO address' + str(address) + ' disabled. Doing nothing.', 4,
                            pilib.loglevels.io)
        elif interface['interface'] == 'SPI0':
            utility.log(pilib.dirs.logs.io, 'Processing SPI0', 1, pilib.loglevels.io)
            if interface['enabled']:
                utility.log(pilib.dirs.logs.io, 'SPI0 enabled', 1, pilib.loglevels.io)
                if interface['type'] == 'SPITC':
                    utility.log(pilib.dirs.logs.io, 'Processing SPITC on SPI0', 3, pilib.loglevels.io)
                    import readspi

                    tcdict = readspi.getpigpioMAX31855temp(0,0)

                    # Convert to F for now
                    spitcentries = readspi.recordspidata(control_db.path, {'SPITC1' :tcdict['tctemp']*1.8+32})
                    control_db.queue_queries(spitcentries)

                if interface['type'] == 'CuPIDlights':
                    import spilights
                    spilightsentries, setlist = spilights.getCuPIDlightsentries('indicators', 0, previndicators)

                    control_db.queue_queries(spilightsentries)
                    spilights.updatelightsfromdb(control_db.path, 'indicators', 0)
                    spilights.setspilights(setlist, 0)
            else:
                utility.log(pilib.dirs.logs.io, 'SPI0 not enabled', 1, pilib.loglevels.io)

        elif interface['interface'] == 'SPI1':
            utility.log(pilib.dirs.logs.io, 'Processing SPI1', 1, pilib.loglevels.io)
            if interface['enabled']:
                utility.log(pilib.dirs.logs.io, 'SPI1 enabled', 1, pilib.loglevels.io)
                if interface['type'] == 'CuPIDlights':
                    utility.log(pilib.dirs.logs.io, 'Processing CuPID Lights on SPI1', 1, pilib.loglevels.io)
                    import spilights

                    spilightsentries, setlist = spilights.getCuPIDlightsentries('indicators', 1, previndicators)
                    control_db.queue_queries(spilightsentries)
                    # print(setlist)
                    spilights.setspilights(setlist, 1)
            else:
                utility.log(pilib.dirs.logs.io, 'SPI1 disaabled', 1, pilib.loglevels.io)

    # Set tables
    dblib.setsinglevalue(pilib.dirs.dbs.system, 'systemstatus', 'lastupdateiopoll', datalib.gettimestring())

    if owfsupdate:
        from iiutilities.owfslib import runowfsupdate
        utility.log(pilib.dirs.logs.io, 'Running owfsupdate', 1, pilib.loglevels.io)
        devices, owfsentries = runowfsupdate(execute=False)
        control_db.queue_queries(owfsentries)
    else:
        utility.log(pilib.dirs.logs.io, 'owfsupdate disabled', 3, pilib.loglevels.io)

    # utility.log(pilib.dirs.logs.io, 'Executing query:  ' + str(control_db.queued_queries), 5, pilib.loglevels.io)

    if control_db.queued_queries:
        try:
            control_db.execute_queue()
        except:
            errorstring = traceback.format_exc()
            utility.log(pilib.dirs.logs.io, 'Error executing query, message:  ' + errorstring, 0, pilib.loglevels.io)
            utility.log(pilib.dirs.logs.error, 'Error executing updateio query, message:  ' + errorstring)
            utility.log(pilib.dirs.logs.error, 'Query:  ' + str(control_db.queued_queries))
            utility.log(pilib.dirs.logs.error, 'Clearing queue')
            control_db.clear_queue()


def get_or_insert_iface_metadata(id, io_infos, control_db, default_name=None):

    """
    Ok, so we want to choose name for input in order:
    1. ioinfo entry
    2 Default name
    """

    entry = {}
    for io_info in io_infos:
        if io_info['id'] == id:
            entry = io_info
            break

    if not entry:
        name = id
        if default_name:
            name = default_name

        entry = {'name': name, 'id':id, 'options':''}
        control_db.insert('ioinfo', entry)

    return entry


def updateioinfo(db_path, tablename_to_update, meta_tablename='ioinfo'):
    from iiutilities.dblib import sqliteDatabase

    """ I HAVE NO IDEA WHAT THIS IS USED FOR ATM"""

    """ This routing iterates of data of table provided, and searches for a name, using the id field in the provided
    table. It searches for this data in the metatable, which by default is the ioinfo table.
    Current format dictates that they are in the same database.
    """
    database = sqliteDatabase(db_path)
    tabledata = database.read_table(tablename_to_update)
    querylist = []
    for item in tabledata:
        condition = "id='" + item['id'] + "'"
        name = database.get_single_value(meta_tablename, 'name', condition=condition)
        if name:
            database.set_single_value(tablename_to_update, 'name', name, condition=condition)

    if database.queued_queries:
        database.execute_queue()


def testupdateio(times, database=None):
    from pilib import dirs
    if not database:
        database = dirs.dbs.control
    for i in range(times):
        updateiodata(database=database)


def processlabjackentry(interface, entry):
    from iiutilities.datalib import parseoptions, gettimestring
    from iiutilities import utility
    from iiutilities import labjack
    from cupid import pilib

    result = {'readtime':gettimestring()}
    options = parseoptions(entry['options'])

    # print(entry['mode'])

    if entry['mode'] == 'AIN':
        resolutionIndex=0
        gainIndex=0
        # settlingFactor=0
        differential=False

        if 'resolution' in options:
            try:
                resolutionIndex = int(options['resolution'])
            except:
                pass
        if 'gain' in options:
            try:
                gainIndex = int(options['gain'])
            except:
                pass
        if 'settling' in options:
            try:
                settlingFactor = int(options['settling'])
            except:
                pass
        if 'differential' in options:
            if options['differential'] in ['1', 'true', 'True']:
                differential=True

        if interface['type'] == 'U6':
            try:
                # Do we error handle in readAnalog function?
                # Or are we trying to catch it out here? TBD.
                readresult = labjack.readU6Analog(entry['address'], resolutionIndex, gainIndex, differential=differential)
                result['value'] = readresult['value']
                result['readtime'] = readresult['readtime']
            except:
                result['status'] = 1
                result['value'] = 'NaN'
                result['readtime'] = ''
                utility.log(pilib.dirs.logs.io, 'Error reading U6 AIN, ID: ' + entry['interfaceid'])
            else:
                result['status'] = 0

            # print(entry)
            # print(result)

        if 'formula' in options:
            from iiutilities.datalib import calcastevalformula
            try:
                # print('translating ' + str(result['value']))
                formula = options['formula'].replace('x', str(result['value']))
                result['value'] = calcastevalformula(formula)
                # print(' to ' + str(result['value']))
            except:
                # print('error in formula')
                 pass

    elif entry['mode'] == 'CNT':

        if interface['type'] == 'U6':

            try:
                readresult = labjack.readU6Counter(entry['address'])
                result['value'] = readresult['value']
                result['readtime'] = readresult['readtime']
            except:
                result = {'status': 1}
                result['value'] = 'NaN'
                result['readtime'] = ''
            else:
                result['status'] = 0

        if 'formula' in options:
            from iiutilities.utility import calcastevalformula
            try:
                # print('translating ' + str(result['value']))
                formula = options['formula'].replace('x', result['value'])
                result['value'] = calcastevalformula(formula)
                # print(' to ' + str(result['value']))
            except:
                # print('error in formula')
                pass
        # print("COUNTER RESULT: ")
        # print(result)
    return result


def process_ads1x15_interface(interface=None):
    from iiutilities import utility
    from cupid import pilib

    try:
        import Adafruit_ADS1x15
    except ImportError:
        message = 'ADAFRUIT_ADS1x15 DOES NOT APPEAR TO BE INSTALLED'
        print(message)
        return {'status':1,'message':message,'entries':[]}

    from iiutilities import datalib
    if interface and 'options' in interface:
        options = datalib.parseoptions(interface['options'])
    else:
        print('using default options')
        options = {}
    settings = {'gain':1, 'channel':0, 'type':'single', 'address':'1:0x48'}
    settings.update(options)

    settings['busnum'] = int(settings['address'].split(':')[0])
    settings['i2c_address'] = int(settings['address'].split(':')[1], 16)

    # print(settings)

    # Create an ADS1115 ADC (16-bit) instance.
    # adc = Adafruit_ADS1x15.ADS1115(address=settings['i2c_address'], busnum=settings['busnum'])

    return_dict = {'status':0, 'message':'', 'value':None, 'readtime':datalib.gettimestring()}

    try:
        adc = Adafruit_ADS1x15.ADS1115(address=settings['i2c_address'], busnum=settings['busnum'])
    except:
        utility.log(pilib.dirs.logs.io, 'Error connecting to ADC. ', 0, pilib.loglevels.io)
        return  {'status':1, 'message':'Error connecting to ADC', 'value':None, 'readtime':datalib.gettimestring()}


    if settings['type'] in ['diff','differential']:
        try:
            return_dict['value'] = float(adc.read_adc_difference(int(settings['channel']), gain=float(settings['gain']))) / 32768
        except:
            utility.log(pilib.dirs.logs.io, 'Error reading ADS1115 differential value. ', 0, pilib.loglevels.io)
            return_dict['status'] = 1
            return_dict['message'] = 'Error reading device at address ' + str((settings['address'])) + ', channel ' + str(settings['channel']) + ', type ' + settings['type'] + ', with gain ' + str(settings['gain'])

        else:
            scalar = 4.096 / float(settings['gain'])
            return_dict['value'] *= scalar
            return_dict['message'] = 'Read device at address ' + str((settings['address'])) + ', channel ' + str(settings['channel']) + ', type ' + settings['type'] + ', with gain ' + str(settings['gain']) + ' with value ' + str(return_dict['value'])


    else:
        try:
            return_dict['value'] = float(adc.read_adc(int(settings['channel']), gain=float(settings['gain']))) / 32768
        except:
            utility.log(pilib.dirs.logs.io, 'Error reading ADS1115 differential value. ', 0, pilib.loglevels.io)
            return_dict['status'] = 1
            return_dict['message'] = 'Error reading device at address ' + str(
                (settings['address'])) + ', channel ' + str(settings['channel']) + ', type ' + settings[
                                         'type'] + ', with gain ' + str(settings['gain'])
        else:
            scalar = 4.096 / float(settings['gain'])
            return_dict['value'] *= scalar
            return_dict['message'] = 'Read device at address ' + str((settings['address'])) + ', channel ' + str(settings['channel']) + ', type ' + settings['type'] + ', with gain ' + str(settings['gain']) + ' with value ' + str(return_dict['value'])

    return return_dict


def processlabjackinterface(control_db, interface, last_data, ioinfos):
    '''
     As with modbus, we will have an auxiliary table that contains a map of stuff we are supposed to read.
     Later, we can use this to make things faster, detect inconsistencies, e.g. setting a FIO to do multiple things
     incompatibly.
    '''

    from iiutilities.dblib import readalldbrows
    from cupid import pilib

    '''
     From previnputs, we need to grab:
     name, ontime, offtime. If name is empty, we just make it the same as the ID
    '''
    querylist = []
    labjackentries = control_db.read_table('labjack', 'interfaceid=\'' + interface['id'] + '\'')
    for entry in labjackentries:
        usbid = entry['interfaceid'] + '_' + str(entry['address']) + '_' + str(entry['mode'])

        # print(usbid)
        # Process entry
        data = processlabjackentry(interface, entry)
        # print(data)

        # Now find previnput entry, if it exists
        preventry = {}
        for input in last_data.inputs:
            if 'id' == usbid:
                preventry = input

        name = usbid
        if 'name' in preventry:
            if preventry['name']:
                name = preventry['name']

        offtime = ''
        if 'offtime' in preventry:
            if preventry['offtime']:
                offtime = preventry['offtime']

        ontime = ''
        if 'offtime' in preventry:
            if preventry['offtime']:
                offtime = preventry['offtime']

        pollfreq = 60 # crap default value

        '''
        TODO : actually use pollfrequency here (and elsewhere) to add a layer to timing to inputs.
        Currently, we just use the
        interface poll frequency to manage it.
        '''

        if 'pollfreq' in preventry:
            if preventry['pollfreq']:
                offtime = preventry['pollfreq']

        from iiutilities.dblib import make_insert_from_dict
        input_query = {'interface':interface['interface'], 'type':interface['type'], 'address':str(entry['address']),
                       'name':name, 'value':str(data['value']), 'readtime':str(data['readtime']), 'pollfreq':str(pollfreq)}
        query = make_insert_from_dict('input', input_query)
        # query = "insert into inputs values ('" + usbid + "','" + interface['interface'] + "','" + \
        #     interface['type'] + "','" + str(entry['address']) + "','" + name + "','" + str(data['value']) + "','','" + \
        #     str(data['readtime']) + "','" + str(pollfreq) + "','" + ontime + "','" + offtime + "')"

        # print(query)

        querylist.append(query)
    return querylist


def mbid_from_entry(entry):
    if entry['mode'] == 'read':
        shortmode = 'R'
    elif entry['mode'] == 'write':
        shortmode = 'W'
    elif entry['mode'] == 'readwrite':
        shortmode = 'RW'
    else:
        # utility.log(pilib.dirs.logs.io, 'modbus mode error', 1, pilib.loglevels.io)
        shortmode = 'R'
    try:
        mbid = entry['interfaceid'] + '_' + str(entry['register']) + '_' + str(entry['length']) + '_' + shortmode
    except KeyError:
        # utility.log(pilib.dirs.logs.io, 'Cannot form mbid due to key error', 0, pilib.loglevels.io)
        return None
    return mbid


def processMBinterface(control_db, interface, last_data, io_info, defaults):

    from iiutilities.netfun import readMBcodedaddresses, MBFCfromaddress
    from iiutilities import dblib, utility, datalib

    previnputids = [previnput['id'] for previnput in last_data.inputs]

    import pilib
    # get all modbus reads that have the same address from the modbus table
    try:
        modbustable = control_db.read_table('modbustcp')
    except:
        utility.log(pilib.dirs.logs.io, 'Error reading modbus table', 0, pilib.loglevels.io)
        modbustable = []
    else:
        utility.log(pilib.dirs.logs.io, 'Read modbus table', 4, pilib.loglevels.io)

    querylist = []
    for entry in modbustable:
        # Get name from ioinfo table to give it a colloquial name
        # First we have to give it a unique ID. This is a bit difficult with modbus

        mbid = mbid_from_entry(entry)


        utility.log(pilib.dirs.logs.io, 'Modbus ID: ' + mbid, 4, pilib.loglevels.io)

        mb_meta = get_or_insert_iface_metadata(mbid, io_info, control_db)
        mb_name = mb_meta['name']

        polltime = datalib.gettimestring()
        if entry['interfaceid'] == interface['id']:
            # For now, we're going to read them one by one. We'll assemble these into block reads
            # in the next iteration
            if entry['mode'] == 'read':

                # Get previous metadata and data
                # Get input settings and keep them if the input previously existed

                if mbid in previnputids:
                    pollfreq = last_data.inputs[previnputids.index(mbid)]['pollfreq']
                    ontime = last_data.inputs[previnputids.index(mbid)]['ontime']
                    offtime = last_data.inputs[previnputids.index(mbid)]['offtime']
                    prevvalue = last_data.inputs[previnputids.index(mbid)]['offtime']
                    prevpolltime = last_data.inputs[previnputids.index(mbid)]['offtime']

                    utility.log(pilib.dirs.logs.io,
                                           'Restoring values from previous inputids: pollfreq = ' + str(
                                               pollfreq) + ' ontime = ' + str(ontime) + ' offtime = ' + str(
                                               offtime), 3, pilib.loglevels.io)

                else:
                    # set values to defaults if it did not previously exist
                    try:
                        pollfreq = defaults['defaultinputpollfreq']
                    except:
                        pollfreq = 60
                    ontime = ''
                    offtime = ''
                    prevvalue = ''
                    prevpolltime = ''
                    utility.log(pilib.dirs.logs.io,
                                           'Setting values to defaults, defaultinputpollfreq = ' + str(pollfreq), 3, pilib.loglevels.io)

                # Read data
                from iiutilities.datalib import bytestovalue
                try:
                    # Override length entry with format-specific length
                    if entry['format']:
                        from iiutilities.datalib import typetoreadlength
                        readlength = typetoreadlength(entry['format'])
                    else:
                        readlength = entry['length']
                    readresult = readMBcodedaddresses(interface['address'], entry['register'], readlength, boolean_to_int=True)

                except:
                    utility.log(pilib.dirs.logs.io, 'Uncaught error reading modbus value', 0, pilib.loglevels.io)
                else:
                    if readresult['statuscode'] == 0:
                        values = readresult['values']

                        value = bytestovalue(values, entry['format'])
                        # print(value)

                        if entry['options']:
                            options = datalib.parseoptions(entry['options'])
                            # print(options)

                            utility.log(pilib.dirs.logs.io, 'processed value is ' + str(value) + ' for format ' + entry['format'], 2, pilib.loglevels.io)

                            if 'scale' in options:
                                utility.log(pilib.dirs.logs.io, 'Scale attribute value found: ' + options['scale'], 2, pilib.loglevels.io)
                                try:
                                    value = float(value) * float(options['scale'])
                                except:
                                    utility.log(pilib.dirs.logs.io, 'error scaling ' + str(value) + ' with argument ' + options['scale'])

                            if 'formula' in options:
                                # print(options['formula'])
                                from iiutilities.datalib import calcastevalformula
                                utility.log(pilib.dirs.logs.io, 'Processing formula: ' + options['formula'] + ' with value ' + str(value))
                                try:
                                    value = calcastevalformula(options['formula'], x=value)
                                except:
                                    utility.log(pilib.dirs.logs.io, 'Error processing formula: ' + str(options['formula']))

                            if 'precision' in options:
                                try:
                                    value = round(value, int(options['precision']))
                                except:
                                    utility.log(pilib.dirs.logs.io, 'Error on precision operation', 0, pilib.loglevels.io)

                            # override name if requested to
                            # TODO : clean this up. clear as mud
                            if 'name' in options:
                                # Check to see if entry already exists in ioinfo to save extra queries
                                if mb_name == options['name']:
                                    # do nothing. all is ok
                                    pass
                                else:
                                    # Update ioinfo
                                    dblib.sqliteinsertsingle(pilib.dirs.dbs.control, 'ioinfo', [mbid, options['name']], ['id', 'name'])
                                    # mbname = dblib.sqlitedatumquery(pilib.dirs.dbs.control,
                                    #                                 "select name from ioinfo where id='" + mbid + "'")
                                    mb_name = options['name']


                        # print(entry['interfaceid'] + ' ' + entry['format'] + ' ' + str(value))
                        utility.log(pilib.dirs.logs.io, 'Values read: ' + str(values), 4, pilib.loglevels.io)
                        utility.log(pilib.dirs.logs.io, 'Value returned: ' + str(value), 4, pilib.loglevels.io)


                        # Contruct entry for newly acquired data
                        newquery = dblib.makesqliteinsert('inputs', [mbid,interface['id'],
                            interface['type'],str(entry['register']),mb_name,str(value),'',str(polltime), str(pollfreq), ontime,offtime])
                        # print(newquery)
                        querylist.append(newquery)
                        # Old dirty way
                        # querylist.append('insert into inputs values (\'' + mbid + "','" + interface['id'] + "','" +
                        #     interface['type'] + "','" + str(entry['register']) + "','" + mbname + "','" + str(
                        #     value) + "','','" + str(polltime) + '\',\'' + str(pollfreq) + "','" + ontime + "','" + offtime + "')")

                    else:
                        status_message = 'Statuscode ' + str(readresult['statuscode']) + ' on MB read : ' + readresult[
                            'message']
                        utility.log(pilib.dirs.logs.io, status_message, 0, pilib.loglevels.io)



                        # restore previous value and construct entry if it existed (or not)
                        input_entry = {'id':mbid, 'interface':interface['interface'], 'type':interface['type'],
                                                              'address':str(entry['register']), 'name':mb_meta['name'],
                                       'value':str(prevvalue), 'polltime':str(prevpolltime), 'pollfreq':str(pollfreq),
                                                                                'ontime':ontime, 'offtime':offtime}
                        query = dblib.make_insert_from_dict('inputs', input_entry)
                        querylist.append(query)
                        # querylist.append('insert into inputs values (\'' + mbid + "','" + interface['interface'] + "','" +
                        #     interface['type'] + '\',\'' + str(entry['register']) + "','" + mb_meta['name'] + "','" +
                        #                  str(prevvalue) + "','','" + str(prevpolltime) + '\',\'' + str(pollfreq) + "','" + ontime + "','" + offtime + "')")


    utility.log(pilib.dirs.logs.io, 'Querylist: ' + str(querylist), 4, pilib.loglevels.io)

    return querylist


def processGPIOinterface(control_db, interface, last_data, io_info, defaults, **kwargs):

    import pilib
    from iiutilities import utility, datalib, dblib

    previnputids = [previnput['id'] for previnput in last_data.inputs]
    previnputvalues = [previnput['value'] for previnput in last_data.inputs]
    prevoutputids = [prevoutput['id'] for prevoutput in last_data.outputs]
    prevoutputvalues = [prevoutput['value'] for prevoutput in last_data.outputs]

    if 'method' in kwargs:
        method = kwargs['method']
    else:
        method = 'pigpio'

    if method == 'rpigpio':
        import RPi.GPIO as GPIO
    elif method == 'pigpio':
        import pigpio

    try:
        if method == 'rpigpio':
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
        elif method == 'pigpio':
            if 'piobject' in kwargs:
                utility.log(pilib.dirs.logs.io,
                       'Pigpio object already exists. ', 4, pilib.loglevels.io)
                pi = kwargs['piobject']
            else:
                utility.log(pilib.dirs.logs.io,
                       'Instantiating pigpio. ', 4, pilib.loglevels.io)
                pi = pigpio.pi()
    except:
        utility.log(pilib.dirs.logs.io,
                       'Error setting up GPIO. ', 1, pilib.loglevels.io)
    else:
        utility.log(pilib.dirs.logs.io,
                       'Done setting up GPIO. ', 4, pilib.loglevels.io)

    options = datalib.parseoptions(interface['options'])
    address = int(interface['address'])

    utility.log(pilib.dirs.logs.io, 'GPIO address' + str(address) + ' enabled', 4, pilib.loglevels.io)
    # Get name from ioinfo table to give it a colloquial name

    entry_meta = get_or_insert_iface_metadata(interface['id'], io_info, control_db)
    name = entry_meta['name']
    polltime = datalib.gettimestring()

    querylist = []
    # Append to inputs and update name, even if it's an output (can read status as input)
    if options['mode'] == 'output':
        utility.log(pilib.dirs.logs.io, 'Setting output mode for GPIO address' + str(address), 3, pilib.loglevels.io)
        try:
            if method == 'rpigpio':
                GPIO.setup(address, GPIO.OUT)
            elif method == 'pigpio':
                pi.set_mode(address, pigpio.OUTPUT)

        except TypeError:
            utility.log(pilib.dirs.logs.io, 'You are trying to set a GPIO with the wrong variable type : ' +
                        str(type(address)), 0, pilib.loglevels.io)
            utility.log(pilib.dirs.logs.io, 'Exiting interface routine for  ' + interface['id'], 0, pilib.loglevels.io)
            return
        except:
            utility.log(pilib.dirs.logs.io, 'Error setting GPIO : ' +
                        str(address), 1, pilib.loglevels.io)
            utility.log(pilib.dirs.logs.io, 'Exiting interface routine for  ' + interface['id'], 0, pilib.loglevels.io)
            return

        # Set the value of the gpio.
        # Get previous value if exists
        if interface['id'] in prevoutputids:
            value = prevoutputvalues[prevoutputids.index(interface['id'])]

        else:
            value = 0
        if value == 1:
            if method == 'rpigpio':
                GPIO.output(address, True)
            elif method == 'pigpio':
                pi.write(address, 1)
            utility.log(pilib.dirs.logs.io, 'Setting output ON for GPIO address' + str(address), 3,
                        pilib.loglevels.io)
        else:
            if method == 'rpigpio':
                GPIO.output(address, False)
            elif method == 'pigpio':
                pi.write(address,0)
            utility.log(pilib.dirs.logs.io, 'Setting output OFF for GPIO address' + str(address), 3,
                        pilib.loglevels.io)

        # Get output settings and keep them if the GPIO previously existed
        if interface['id'] in prevoutputids:
            pollfreq = last_data.outputs[prevoutputids.index(interface['id'])]['pollfreq']
            ontime = last_data.outputs[prevoutputids.index(interface['id'])]['ontime']
            offtime = last_data.outputs[prevoutputids.index(interface['id'])]['offtime']
        else:
            try:
                pollfreq = defaults['defaultoutputpollfreq']
            except:
                pollfreq = 60
                ontime = ''
                offtime = ''
                utility.log(pilib.dirs.logs.io,
                            'Setting values to defaults, defaultinputpollfreq = ' + str(
                                pollfreq), 3, pilib.loglevels.io)

        # Add entry to outputs tables
        output_entry = {'id':interface['id'], 'interface':interface['interface'], 'type':interface['type'],
                                                'address':interface['address'], 'name':name, 'value':value,
                                                'polltime':polltime, 'pollfreq':pollfreq}
        querylist.append(dblib.make_insert_from_dict('outputs', output_entry))


        # Also add to inputs table for use in other channels
        querylist.append(dblib.make_insert_from_dict('inputs', output_entry))



        # querylist.append('insert into outputs values (\'' + interface['id'] + "','" +
        #                  interface['interface'] + "','" + interface['type'] + "','" + str(
        #     address) + "','" +
        #                  gpioname + "','" + str(value) + "','','" + str(polltime) + "','" +
        #                  str(pollfreq) + "','" + ontime + "','" + offtime + "')")

    elif options['mode'] == 'input':
        if method == 'rpigpio':
            GPIO.setup(address, GPIO.IN)
        elif method == 'pigpio':
            if 'pullupdown' in options:
                if options['pullupdown'] == 'pullup':
                    pi.set_pull_up_down(address, pigpio.PUD_UP)
                elif options['pullupdown'] == 'pulldown':
                    pi.set_pull_up_down(address, pigpio.PUD_DOWN)
                else:
                    pi.set_pull_up_down(address, pigpio.PUD_OFF)
            else:
                try:
                    pi.set_pull_up_down(17, pigpio.PUD_OFF)
                except:
                    pass
            try:
                pi.set_mode(address, pigpio.INPUT)
            except:
                #handle me!
                pass

        if method == 'rpigpio':
            value = GPIO.input(address)
        elif method == 'pigpio':
            value = pi.read(address)

        if 'function' in options:
            if options['function'] == 'shutdown':
                # TODO : The reboot function is still held in a shell script, because it works.
                if 'functionstate' in options:
                    if value == 1 and options['functionstate'] in ['true', 'On', 'True', '1']:
                        from systemstatus import processsystemflags
                        processsystemflags()

        utility.log(pilib.dirs.logs.io, 'Setting input mode for GPIO address' + str(address), 3,
                    pilib.loglevels.io)

        # Get input settings and keep them if the GPIO previously existed
        if interface['id'] in previnputids:
            pollfreq = last_data.inputs[previnputids.index(interface['id'])]['pollfreq']
            ontime = last_data.inputs[previnputids.index(interface['id'])]['ontime']
            offtime = last_data.inputs[previnputids.index(interface['id'])]['offtime']
            utility.log(pilib.dirs.logs.io,
                                   'Restoring values from previous inputids: pollfreq = ' + str(
                                       pollfreq) + ' ontime = ' + str(ontime) + ' offtime = ' + str(
                                       offtime), 3, pilib.loglevels.io)

        else:
            try:
                pollfreq = defaults['defaultinputpollfreq']
            except:
                pollfreq = 60
                ontime = ''
                offtime = ''
                utility.log(pilib.dirs.logs.io,
                                       'Setting values to defaults, defaultinputpollfreq = ' + str(
                                           pollfreq), 3, pilib.loglevels.io)

        # Add entry to outputs tables
        input_entry = {'id': interface['id'], 'interface': interface['interface'], 'type': interface['type'],
                        'address': interface['address'], 'name': name, 'value': value,
                        'polltime': polltime, 'pollfreq': pollfreq}

        querylist.append(dblib.make_insert_from_dict('inputs', input_entry))

    elif options['mode'] == 'counter':
        settings = {'edge': 'falling', 'pullupdown': None, 'debounce_ms': 50, 'event_min_ms': 50, 'watchdog_ms': 100}
        settings.update(options)

        # check io_objects to see if the object already exists. if not, instantiate it
        # We name the objects after the id for now
        if interface['id'] in kwargs['io_objects']:
            pass
            # print('WE FOUNd THE OBJECT')

        else:
            io_object = pilib.pigpiod_gpio_counter(**{'gpio':address, 'pi':pi, 'options':options, 'type': 'counter'})
            kwargs['io_objects'][interface['id']] = io_object

        value = kwargs['io_objects'][interface['id']].get_value()
        # print('VALUE IS ' + str(value))
        rate = kwargs['io_objects'][interface['id']].get_rate()
        # print('RATE IS ' + str(rate))

        # Get input settings and keep them if the GPIO previously existed
        if interface['id'] in previnputids:
            pollfreq = last_data.inputs[previnputids.index(interface['id'])]['pollfreq']
            ontime = last_data.inputs[previnputids.index(interface['id'])]['ontime']
            offtime = last_data.inputs[previnputids.index(interface['id'])]['offtime']
            utility.log(pilib.dirs.logs.io,
                        'Restoring values from previous inputids: pollfreq = ' + str(
                            pollfreq) + ' ontime = ' + str(ontime) + ' offtime = ' + str(
                            offtime), 3, pilib.loglevels.io)

        else:
            try:
                pollfreq = defaults['defaultinputpollfreq']
            except:
                pollfreq = 60
                ontime = ''
                offtime = ''
                utility.log(pilib.dirs.logs.io,
                            'Setting values to defaults, defaultinputpollfreq = ' + str(
                                pollfreq), 3, pilib.loglevels.io)

        input_entry = {'id': interface['id'], 'interface': interface['interface'], 'type': interface['type'],
                        'address': interface['address'], 'name': name, 'value': value,
                        'polltime': polltime, 'pollfreq': pollfreq}
        querylist.append(dblib.make_insert_from_dict('inputs', input_entry))

        rate_id = interface['id'] + '_rate'
        entry_meta = get_or_insert_iface_metadata(rate_id, io_info, control_db)
        name = entry_meta['name']
        input_entry = {'id': rate_id, 'interface': interface['interface'], 'type': interface['type'],
                       'address': interface['address'], 'name': name, 'value': rate,
                       'polltime': polltime, 'pollfreq': pollfreq}
        querylist.append(dblib.make_insert_from_dict('inputs', input_entry))

    if method == 'pigpio' and 'piobject' not in kwargs:
        pi.stop()

    return querylist


if __name__ == '__main__':
    from pilib import dirs
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'debug':
        updateiodata(database=dirs.dbs.control, debug=True)
    else:
        updateiodata()

