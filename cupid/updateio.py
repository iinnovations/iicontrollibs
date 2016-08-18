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


def updateiodata(database, **kwargs):
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

    allowedGPIOaddresses = [18, 23, 24, 25, 4, 17, 27, 22, 5, 6, 13, 19, 26, 16, 20, 21]

    logconfig = pilib.getlogconfig()

    tables = dblib.gettablenames(pilib.dirs.dbs.control)
    if 'interfaces' in tables:
        interfaces = dblib.readalldbrows(pilib.dirs.dbs.control, 'interfaces')
    else:
        utility.log(pilib.dirs.logs.io, 'interfaces table not found. Exiting', 1,
                    logconfig['loglevels.io'])
        return

    # TODO: Sort interfaces to put aux values at the end and prioritize reads. Maybe a priority field?

    if 'inputs' in tables:
        previnputs = dblib.readalldbrows(pilib.dirs.dbs.control, 'inputs')

        # Make list of IDs for easy indexing
        previnputids = []
        for input in previnputs:
            previnputids.append(input['id'])
    else:
        previnputs = []
        previnputids = []

    if 'outputs' in tables:
        prevoutputs = dblib.readalldbrows(pilib.dirs.dbs.control, 'outputs')

        # Make list of IDs for easy indexing
        prevoutputids = []
        prevoutputvalues = []
        for output in prevoutputs:
            prevoutputids.append(output['id'])
            prevoutputvalues.append(output['value'])
    else:
        prevoutputs = {}
        prevoutputids = []

    if 'defaults' in tables:
        defaults = dblib.readalldbrows(pilib.dirs.dbs.control, 'defaults')[0]
        defaultinputpollfreq = defaults['inputpollfreq']
        defaultoutputpollfreq = defaults['outputpollfreq']
    else:
        defaults = []
        defaultinputpollfreq = 60
        defaultoutputpollfreq = 60

    if 'indicators' in tables:
        indicatornames = []
        previndicators = dblib.readalldbrows(pilib.dirs.dbs.control, 'indicators')
        for indicator in previndicators:
            indicatornames.append(indicator['name'])
    else:
        previndicators = []
        indicatornames = []

    # We drop all inputs and outputs and recreate
    # Add all into one query so there is no time when the IO don't exist.

    querylist = []
    querylist.append('delete from inputs')
    querylist.append('delete from outputs')

    '''
    This is temporary. Clearing the table here and adding entries below can result in a gap in time
    where there are no database indicator entries. This is not too much of a problem with indicators, as we
    update the hardware explicitly after we add the entries. If the interface queries the table during
    this period, however, we could end up with an apparently empty table.
    TODO: FIX update on indicators in updateio
    '''

    # We drop this table, so that if SP1 has been disabled, the entries do not appear as valid indicators
    dblib.sqlitequery(pilib.dirs.dbs.control, 'delete from indicators')

    owfsupdate = False
    # Unfortunately, we need to keep track of the IDs we are creating, so we don't run them over as we go

    interfaceids = []
    for interface in interfaces:
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

                    valueentries = processlabjackinterface(interface, previnputs)

                    # print(valueentries)
                    if valueentries:
                        querylist.extend(valueentries)

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
            if entryid in previnputids:
                preventry = previnputs[previnputids.index(entryid)]
                name = preventry['name']
            else:
                preventry = {}
                name = entryid

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

                    query = dblib.makesqliteinsert('inputs', [entryid, interface['interface'], interface['type'],
                          interface['address'], name, str(value), '', str(readtime),
                          str(defaultinputpollfreq), '', ''])
                    querylist.append(query)
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
                    query = dblib.makesqliteinsert('inputs', [entryid, interface['interface'],
                          interface['type'], str(interface['address']), name, str(value), '', str(readtime),
                          str(defaultinputpollfreq), '', ''])
                    querylist.append(query)

        elif interface['interface'] == 'MOTE':

            #determine and then update id based on fields
            entryid = interface['interface'] + '_' + interface['type'] + '_' + interface['address']
            interfaceids.append(entryid)

            condition = '"interface"=\'' + interface['interface'] + '\' and "type"=\'' + interface['type'] + '\' and "address"=\'' + interface['address'] + '\''

            # print(condition)
            dblib.setsinglevalue(pilib.dirs.dbs.control, 'interfaces', 'id', entryid, condition)

            utility.log(pilib.dirs.logs.io, 'Processing Mote interface' + interface['name'] + ', id:' + entryid, 3,
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
                    nodeentries = []
                else:
                    condition = "\"nodeid\"='" + nodeid + "' and \"keyvalue\"='" + keyvalue + "'"
                    nodeentries = dblib.dynamicsqliteread(pilib.dirs.dbs.control, 'remotes', condition=condition)

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
                            dblib.setsinglevalue(pilib.dirs.dbs.control, 'remotes', 'data', datalib.dicttojson(nodedata), condition=condition)

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
                        existingchannels = dblib.readalldbrows(pilib.dirs.dbs.control, 'channels')
                        for channel in existingchannels:
                            if channel['name'] == interface['name']:
                                # print('updating')
                                # print(channel)
                                newchannel.update(channel)
                                # print(newchannel)
                        newchannel.update(newchanneldata)
                        # print(newchannel)

                        keys = []
                        values = []
                        for key, value in newchannel.iteritems():
                            keys.append(key)
                            values.append(value)

                        query = dblib.makesqliteinsert('channels', values, keys)
                        # print(query)
                        dblib.sqlitequery(pilib.dirs.dbs.control, query)
                    else:
                        # print('multiple entries found for channel. not appropriate')
                        pass
                else:
                    # Create queries for table insertion
                    # TODO: process mote pollfreq, ontime, offtime
                    moteentries = []
                    for nodeentry in nodeentries:

                        # THis breaks out all of the strictly json-encoded data.
                        datadict = datalib.parseoptions(nodeentry['data'])
                        try:
                            entrytype = nodeentry['msgtype']

                            # now treat each mote type entry specially
                            # if entrytype == 'channel':

                            entryid = 'MOTE' + str(nodeentry['nodeid']) + '_' + nodeentry['keyvaluename'] + '_' + nodeentry['keyvalue']

                            entrymetareturn = dblib.dynamicsqliteread(pilib.dirs.dbs.control, 'ioinfo', condition="\"id\"='" + entryid + "'")
                            try:
                                entrymeta = entrymetareturn[0]
                            except:
                                entrymeta = []

                            # print(entrymeta)

                            entryoptions={}
                            if entrymeta:
                                entryname = entrymeta['name']
                                if entrymeta['options']:
                                    entryoptions = datalib.parseoptions(entrymeta['options'])
                            else:
                                entryname = '[MOTE' + str(nodeentry['nodeid']) + '] ' + nodeentry['keyvaluename'] + ':' + nodeentry['keyvalue']
                        except KeyError:
                            # print('OOPS KEY ERROR')
                            pass
                        else:
                            if entrytype == 'iovalue':
                                if 'scale' in entryoptions:
                                    entryvalue = str(float(entryoptions['scale']) * float(datadict['ioval']))
                                elif 'formula' in entryoptions:
                                    x = float(datadict['ioval'])
                                    try:
                                        entryvalue = eval(entryoptions['formula'])
                                    except:
                                        entryvalue = float(datadict['ioval'])
                                else:
                                    entryvalue = float(datadict['ioval'])
                            elif entrytype == 'owdev':
                                if 'owtmpasc' in datadict:
                                    if 'scale' in entryoptions:
                                        entryvalue = str(float(entryoptions['scale']) * float(datadict['owtmpasc']))
                                    elif 'formula' in entryoptions:
                                        x = float(datadict['owtmpasc'])
                                        try:
                                            entryvalue = eval(entryoptions['formula'])
                                        except:
                                            entryvalue = float(datadict['owtmpasc'])
                                    else:
                                        entryvalue = datadict['owtmpasc']
                                else:
                                    entryvalue = -1
                            else:
                                entryvalue = -1


                            moteentries.append('insert into inputs values (\'' + entryid + '\',\'' + interface['interface'] + '\',\'' +
                                interface['type'] + '\',\'' + str(address) + '\',\'' + entryname + '\',\'' + str(entryvalue) + "','','" +
                                 nodeentry['time'] + '\',\'' + str(15) + "','" + '' + "','" + '' + "')")
                    # print('querylist')
                    # print(moteentries)
                    querylist.extend(moteentries)

            else:
                utility.log(pilib.dirs.logs.io, 'Mote Interface ' + interface['name'] + ' disnabled', 3,
                            pilib.loglevels.io)
        elif interface['interface'] == 'LAN':
            utility.log(pilib.dirs.logs.io, 'Processing LAN interface' + interface['name'], 3,
                        pilib.loglevels.io)
            if interface['enabled']:
                utility.log(pilib.dirs.logs.io, 'LAN Interface ' + interface['name'] + ' enabled', 3,
                            pilib.loglevels.io)
                if interface['type'] == 'MBTCP':
                    utility.log(pilib.dirs.logs.io, 'Interface ' + interface['name'] + ' type is MBTCP',
                                3, pilib.loglevels.io)

                    try:
                        mbentries = processMBinterface(interface, prevoutputs, prevoutputids, previnputs, previnputids, defaults, logconfig)
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
                        querylist.extend(mbentries)
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
                        GPIOentries = processGPIOinterface(interface, prevoutputs, prevoutputvalues, prevoutputids,
                                                               previnputs, previnputids, defaults, logconfig, piobject=pi)
                    except:
                        utility.log(pilib.dirs.logs.io,
                                           "ERROR handling GPIO interface " + str(address) + '. ', 0,  pilib.loglevels.io)
                        GPIOentries = []
                    if GPIOentries:
                                querylist.extend(GPIOentries)
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
                    spitcentries = readspi.recordspidata(database, {'SPITC1' :tcdict['tctemp']*1.8+32})
                    querylist.extend(spitcentries)

                if interface['type'] == 'CuPIDlights':
                    import spilights
                    print('TOTALLY ENABLED')
                    spilightsentries, setlist = spilights.getCuPIDlightsentries('indicators', 0, previndicators)
                    querylist.extend(spilightsentries)
                    spilights.updatelightsfromdb(pilib.dirs.dbs.control, 'indicators', 0)
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
                    querylist.extend(spilightsentries)
                    print(setlist)
                    spilights.setspilights(setlist, 1)
            else:
                utility.log(pilib.dirs.logs.io, 'SPI1 disaabled', 1, pilib.loglevels.io)

    # Set tables
    dblib.setsinglevalue(pilib.dirs.dbs.system, 'systemstatus', 'lastiopoll', datalib.gettimestring())

    if owfsupdate:
        from iiutilities.owfslib import runowfsupdate
        utility.log(pilib.dirs.logs.io, 'Running owfsupdate', 1, pilib.loglevels.io)
        devices, owfsentries = runowfsupdate(execute=False)
        querylist.extend(owfsentries)
    else:
        utility.log(pilib.dirs.logs.io, 'owfsupdate disabled', 3, pilib.loglevels.io)

    utility.log(pilib.dirs.logs.io, 'Executing query:  ' + str(querylist), 5, pilib.loglevels.io)
    try:
        dblib.sqlitemultquery(pilib.dirs.dbs.control, querylist)
    except:
        errorstring = traceback.format_exc()
        utility.log(pilib.dirs.logs.io, 'Error executing query, message:  ' + errorstring, 0, pilib.loglevels.io)
        utility.log(pilib.dirs.logs.error, 'Error executing updateio query, message:  ' + errorstring)
        utility.log(pilib.dirs.logs.error, 'Query:  ' + str(querylist))


def updateioinfo(database, table):
    from iiutilities.dblib import readalldbrows
    from iiutilities.dblib import sqlitedatumquery
    from iiutilities.dblib import sqlitemultquery

    tabledata = readalldbrows(database, table)
    querylist = []
    for item in tabledata:
        itemid = item['id']
        name = sqlitedatumquery(database, 'select name from ioinfo where id=\'' + itemid + '\'')
        querylist.append(database, 'update ' + table + ' set name=\'' + name + '\' where id = \'' + itemid + '\'')
    if querylist:
        sqlitemultquery(querylist)


def testupdateio(times):
    from pilib import dirs

    for i in range(times):
        updateiodata(dirs.dbs.control)


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


def processlabjackinterface(interface, previnputs):
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
    labjackentries = readalldbrows(pilib.dirs.dbs.control, 'labjack', 'interfaceid=\'' + interface['id'] + '\'')
    # print(labjackentries)
    for entry in labjackentries:
        usbid = entry['interfaceid'] + '_' + str(entry['address']) + '_' + str(entry['mode'])

        # print(usbid)
        # Process entry
        data = processlabjackentry(interface, entry)
        # print(data)

        # Now find previnput entry, if it exists
        preventry = {}
        for input in previnputs:
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

        query = "insert into inputs values ('" + usbid + "','" + interface['interface'] + "','" + \
        interface['type'] + "','" + str(entry['address']) + "','" + name + "','" + str(data['value']) + "','','" + \
        str(data['readtime']) + "','" + str(pollfreq) + "','" + ontime + "','" + offtime + "')"

        # print(query)

        querylist.append(query)
    return querylist


def processMBinterface(interface, prevoutputs, prevoutputids, previnputs, previnputids, defaults, logconfig):
    from iiutilities.netfun import readMBcodedaddresses, MBFCfromaddress
    from iiutilities import dblib, utility, datalib

    import pilib
    # get all modbus reads that have the same address from the modbus table
    try:
        modbustable = dblib.readalldbrows(pilib.dirs.dbs.control, 'modbustcp')
    except:
        utility.log(pilib.dirs.logs.io, 'Error reading modbus table', 0, pilib.loglevels.io)
    else:
        utility.log(pilib.dirs.logs.io, 'Read modbus table', 4, pilib.loglevels.io)

    querylist = []
    for entry in modbustable:
        # Get name from ioinfo table to give it a colloquial name
        # First we have to give it a unique ID. This is a bit difficult with modbus

        if entry['mode'] == 'read':
            shortmode = 'R'
        elif entry['mode'] == 'write':
            shortmode = 'W'
        elif entry['mode'] == 'readwrite':
            shortmode = 'RW'
        else:
            utility.log(pilib.dirs.logs.io, 'modbus mode error', 1, pilib.loglevels.io)
        try:
            mbid = entry['interfaceid'] + '_' + str(entry['register']) + '_' + str(entry['length']) + '_' + shortmode
        except KeyError:
            utility.log(pilib.dirs.logs.io, 'Cannot form mbid due to key error', 0, pilib.loglevels.io)
            return

        utility.log(pilib.dirs.logs.io, 'Modbus ID: ' + mbid, 4, pilib.loglevels.io)

        mbname = dblib.sqlitedatumquery(pilib.dirs.dbs.control, "select name from ioinfo where id='" + mbid + "'")
        polltime = datalib.gettimestring()
        if entry['interfaceid'] == interface['id']:
            # For now, we're going to read them one by one. We'll assemble these into block reads
            # in the next iteration
            if entry['mode'] == 'read':

                # Get previous metadata and data
                # Get input settings and keep them if the input previously existed

                if mbid in previnputids:
                    pollfreq = previnputs[previnputids.index(mbid)]['pollfreq']
                    ontime = previnputs[previnputids.index(mbid)]['ontime']
                    offtime = previnputs[previnputids.index(mbid)]['offtime']
                    prevvalue = previnputs[previnputids.index(mbid)]['offtime']
                    prevpolltime = previnputs[previnputids.index(mbid)]['offtime']

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
                try:
                    readresult = readMBcodedaddresses(interface['address'], entry['register'], entry['length'])
                except:
                    utility.log(pilib.dirs.logs.io, 'Uncaught reror reading modbus value', 0, pilib.loglevels.io)
                else:
                    if readresult['statuscode'] == 0:
                        values = readresult['values']
                        try:
                            FC = MBFCfromaddress(int(entry['register']))
                        except ValueError:
                            utility.log(pilib.dirs.logs.io, 'Malformed address for FC determination : ' + str(entry['address']), 0, pilib.loglevels.io)
                        else:
                            utility.log(pilib.dirs.logs.io, 'Function code : ' + str(FC), 4, pilib.loglevels.io)
                        returnvalue = 0
                        if len(values) > 0:
                            utility.log(pilib.dirs.logs.io, 'Multiple values returned', 4, pilib.loglevels.io)
                            if not entry['bigendian']:
                                try:
                                    values.reverse()
                                except AttributeError:
                                    utility.log(pilib.dirs.logs.io, 'Error on reverse of MB values: ' + str(values), 0, pilib.loglevels.io)
                            if entry['format'] == 'float32':
                                import struct
                                byte2 = values[0] % 256
                                byte1 = (values[0] - byte2)/256
                                byte4 = values[1] % 256
                                byte3 = (values[1] - byte4)/256

                                byte1hex = chr(byte1)
                                byte2hex = chr(byte2)
                                byte3hex = chr(byte3)
                                byte4hex = chr(byte4)
                                hexstring = byte1hex + byte2hex + byte3hex + byte4hex

                                returnvalue = struct.unpack('>f',hexstring)[0]
                            else:
                                for index, val in enumerate(values):
                                    if FC in [0, 1]:
                                        returnvalue += val * 2 ** index
                                    elif FC in [3, 4]:
                                        returnvalue += val * 256 ** index
                                    else:
                                         utility.log(pilib.dirs.logs.io, 'Invalid function code', 0, pilib.loglevels.io)
                        else:
                            returnvalue = values[0]
                        if entry['options'] != '':
                            options = datalib.parseoptions(entry['options'])
                            if 'scale' in options:
                                # try:
                                    returnvalue = returnvalue * float(options['scale'])
                                # except:
                                #     pilib.writedatedlogmsg(pilib.dirs.logs.io, 'Error on scale operation', 0, pilib.loglevels.io)
                            if 'precision' in options:
                                # try:
                                    returnvalue = round(returnvalue, int(options['precision']))
                                # except:
                                #     pilib.writedatedlogmsg(pilib.dirs.logs.io, 'Error on precision operation', 0, pilib.loglevels.io)


                        utility.log(pilib.dirs.logs.io, 'Values read: ' + str(values), 4, pilib.loglevels.io)
                        utility.log(pilib.dirs.logs.io, 'Value returned: ' + str(returnvalue), 4, pilib.loglevels.io)


                        # Contruct entry for newly acquired data
                        querylist.append('insert into inputs values (\'' + mbid + '\',\'' + interface['id'] + '\',\'' +
                            interface['type'] + '\',\'' + str(entry['register']) + '\',\'' + mbname + '\',\'' + str(
                            returnvalue) + "','','" + str(polltime) + '\',\'' + str(pollfreq) + "','" + ontime + "','" + offtime + "')")

                    else:
                        utility.log(pilib.dirs.logs.io, 'Statuscode ' + str(readresult['statuscode']) + ' on MB read : ' + readresult['message'], 0, pilib.loglevels.io)

                        # restore previous value and construct entry if it existed (or not)
                        querylist.append('insert into inputs values (\'' + mbid + '\',\'' + interface['interface'] + '\',\'' +
                            interface['type'] + '\',\'' + str(entry['register']) + '\',\'' + mbname + '\',\'' + str(prevvalue) + "','','" + str(prevpolltime) + '\',\'' + str(pollfreq) + "','" + ontime + "','" + offtime + "')")


    utility.log(pilib.dirs.logs.io, 'Querylist: ' + str(querylist), 4, pilib.loglevels.io)

    return querylist


def processGPIOinterface(interface, prevoutputs, prevoutputvalues, prevoutputids, previnputs, previnputids, defaults, logconfig, **kwargs):

    import pilib
    from iiutilities import utility, datalib, dblib

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
    gpioname = dblib.sqlitedatumquery(pilib.dirs.dbs.control, 'select name from ioinfo where id=\'' + interface['id'] + '\'')
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
            pollfreq = prevoutputs[prevoutputids.index(interface['id'])]['pollfreq']
            ontime = prevoutputs[prevoutputids.index(interface['id'])]['ontime']
            offtime = prevoutputs[prevoutputids.index(interface['id'])]['offtime']
        else:
            try:
                pollfreq = defaults['defaultoutputpollfreq']
            except:
                pollfreq = 60
            ontime = ''
            offtime = ''

        # Add entry to outputs tables
        querylist.append('insert into outputs values (\'' + interface['id'] + '\',\'' +
                         interface['interface'] + '\',\'' + interface['type'] + '\',\'' + str(
            address) + '\',\'' +
                         gpioname + '\',\'' + str(value) + "','','" + str(polltime) + '\',\'' +
                         str(pollfreq) + "','" + ontime + "','" + offtime + "')")
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
            pollfreq = previnputs[previnputids.index(interface['id'])]['pollfreq']
            ontime = previnputs[previnputids.index(interface['id'])]['ontime']
            offtime = previnputs[previnputids.index(interface['id'])]['offtime']
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
    querylist.append(
        'insert into inputs values (\'' + interface['id'] + '\',\'' + interface['interface'] + '\',\'' +
        interface['type'] + '\',\'' + str(address) + '\',\'' + gpioname + '\',\'' + str(
            value) + "','','" +
        str(polltime) + '\',\'' + str(pollfreq) + "','" + ontime + "','" + offtime + "')")

    if method == 'pigpio' and 'piobject' not in kwargs:
        pi.stop()

    return querylist


if __name__ == '__main__':
    from pilib import dirs
    updateiodata(dirs.dbs.control)

