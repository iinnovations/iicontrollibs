#!/usr/bin/env python

__author__ = 'Colin Reese'
__copyright__ = 'Copyright 2014, Interface Innovations'
__credits__ = ['Colin Reese']
__license__ = 'Apache 2.0'
__version__ = '1.0'
__maintainer__ = 'Colin Reese'
__email__ = 'support@interfaceinnovations.org'
__status__ = 'Development'


def updateiodata(database):
    # This recreates all input and output tables based on the interfaces table.
    # Thus way we don't keep around stale data values. We could at some point incorporate
    # a retention feature that keeps them around in case they disappear temporarily.
    # It also reads the elements if they are enabled and it's time to read them

    import pilib
    import RPi.GPIO as GPIO

    allowedGPIOaddresses = [18, 23, 24, 25, 4, 17, 21, 22]

    dontrun = False
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    tables = pilib.gettablenames(pilib.controldatabase)
    if 'interfaces' in tables:
        interfaces = pilib.readalldbrows(pilib.controldatabase, 'interfaces')
    else:
        pilib.writedatedlogmsg(pilib.systemstatuslog,'interfaces table not found. Exiting',1,pilib.systemstatusloglevel)
        return
    if 'inputs' in tables:
        previnputs = pilib.readalldbrows(pilib.controldatabase, 'inputs')

        # Make list of IDs for easy indexing
        previnputids = []
        for input in previnputs:
            previnputids.append(input['id'])
    else:
        previnputs = []
        previnputids = []

    if 'outputs' in tables:
        prevoutputs = pilib.readalldbrows(pilib.controldatabase, 'outputs')

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
        defaults = pilib.readalldbrows(pilib.controldatabase, 'defaults')[0]
        defaultinputpollfreq = defaults['inputpollfreq']
        defaultoutputpollfreq = defaults['outputpollfreq']
    else:
        defaults = []
        defaultinputpollfreq = 60
        defaultoutputpollfreq = 60

    if 'indicators' in tables:
        indicatornames = []
        previndicators = pilib.readalldbrows(pilib.controldatabase, 'indicators')
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

    # This is temporary. Clearing the table here and adding entries below can result in a gap in time
    # where there are no database indicator entries. This is not too much of a problem with indicators, as we
    # update the hardware explicitly after we add the entries. If the interface queries the table during
    # this period, however, we could end up with an apparently empty table.
    # The reason they are updated within the table rather than compiling
    pilib.sqlitequery(pilib.controldatabase, 'delete from indicators')

    owfsupdate = False
    for interface in interfaces:
        if interface['interface'] == 'I2C':
            pilib.writedatedlogmsg(pilib.systemstatuslog, 'Processing I2C interface', 3, pilib.systemstatusloglevel)
            if interface['enabled']:
                pilib.writedatedlogmsg(pilib.systemstatuslog, 'I2C Interface enabled', 3, pilib.systemstatusloglevel)
                if interface['type'] == 'DS2483':
                    pilib.writedatedlogmsg(pilib.systemstatuslog, 'Interface type is DS2483', 3,
                                           pilib.systemstatusloglevel)
                    owfsupdate = True
        elif interface['interface'] == 'USB':
            pilib.writedatedlogmsg(pilib.systemstatuslog, 'Processing USB interface', 3, pilib.systemstatusloglevel)
            if interface['enabled']:
                pilib.writedatedlogmsg(pilib.systemstatuslog, 'USB Interface enabled', 3, pilib.systemstatusloglevel)
                if interface['type'] == 'DS9490':
                    pilib.writedatedlogmsg(pilib.systemstatuslog, 'Interface type is DS9490', 3,
                                           pilib.systemstatusloglevel)
                    owfsupdate = True

        elif interface['interface'] == 'GPIO':
            try:
                address = int(interface['address'])
            except KeyError:
                pilib.writedatedlogmsg(pilib.systemstatuslog, 'GPIO address key not found for ' + interface['name'], 1,
                                       pilib.systemstatusloglevel)
                continue

            pilib.writedatedlogmsg(pilib.systemstatuslog, 'Processing GPIO interface ' + str(interface['address']), 3,
                                   pilib.systemstatusloglevel)
            options = pilib.parseoptions(interface['options'])

            # TODO : respond to more options, like pullup and pulldown

            if address in allowedGPIOaddresses:
                pilib.writedatedlogmsg(pilib.systemstatuslog, 'GPIO address' + str(address) + ' allowed', 4,
                                       pilib.systemstatusloglevel)

                # Check if interface is enabled
                if interface['enabled']:
                    pilib.writedatedlogmsg(pilib.systemstatuslog, 'GPIO address' + str(address) + ' enabled', 4,
                                       pilib.systemstatusloglevel)
                    # Get name from ioinfo table to give it a colloquial name
                    gpioname = pilib.sqlitedatumquery(database, 'select name from ioinfo where id=\'' +
                                                                interface['id'] + '\'')
                    polltime = pilib.gettimestring()

                    # Append to inputs and update name, even if it's an output (can read status as input)
                    if options['mode'] == 'output':
                        pilib.writedatedlogmsg(pilib.systemstatuslog, 'Setting output mode for GPIO address' + str(address), 3,
                                       pilib.systemstatusloglevel)

                        GPIO.setup(address, GPIO.OUT)

                        # Set the value of the gpio.
                        # Get previous value if exists
                        if interface['id'] in prevoutputids:
                            value = prevoutputvalues[prevoutputids.index(interface['id'])]

                        else:
                            value = 0
                        if value == 1:
                            GPIO.output(address, True)
                            pilib.writedatedlogmsg(pilib.systemstatuslog, 'Setting output ON for GPIO address' + str(address), 3,
                                       pilib.systemstatusloglevel)
                        else:
                            GPIO.output(address, False)
                            pilib.writedatedlogmsg(pilib.systemstatuslog, 'Setting output OFF for GPIO address' + str(address), 3,
                                       pilib.systemstatusloglevel)

                        # Get output settings and keep them if the GPIO previously existed
                        if interface['id'] in prevoutputids:
                            pollfreq = prevoutputs[prevoutputids.index(interface['id'])]['pollfreq']
                            ontime = prevoutputs[prevoutputids.index(interface['id'])]['ontime']
                            offtime = prevoutputs[prevoutputids.index(interface['id'])]['offtime']
                        else:
                            pollfreq = defaultoutputpollfreq
                            ontime = ''
                            offtime = ''

                        # Add entry to outputs tables
                        querylist.append('insert into outputs values (\'' + interface['id'] + '\',\'' +
                                         interface['interface'] + '\',\'' + interface['type'] + '\',\'' + str(
                            address) + '\',\'' +
                                         gpioname + '\',\'' + str(value) + "','','" + str(polltime) + '\',\'' +
                                         str(pollfreq) + "','" + ontime + "','" + offtime + "')")
                    else:
                        GPIO.setup(address, GPIO.IN)
                        value = GPIO.input(address)
                        pilib.writedatedlogmsg(pilib.systemstatuslog, 'Setting input mode for GPIO address' + str(address), 3,
                                       pilib.systemstatusloglevel)

                    # Get input settings and keep them if the GPIO previously existed
                    if interface['id'] in previnputids:
                        pollfreq = previnputs[prevoutputids.index(interface['id'])]['pollfreq']
                        ontime = previnputs[prevoutputids.index(interface['id'])]['ontime']
                        offtime = previnputs[prevoutputids.index(interface['id'])]['offtime']
                        pilib.writedatedlogmsg(pilib.systemstatuslog,
                                               'Restoring values from previous inputids: pollfreq = ' + str(
                                                   pollfreq) + ' ontime = ' + str(ontime) + ' offtime = ' + str(
                                                   offtime), 3, pilib.systemstatusloglevel)

                    else:
                        pollfreq = defaultinputpollfreq
                        ontime = ''
                        offtime = ''
                        pilib.writedatedlogmsg(pilib.systemstatuslog,
                                               'Setting values to defaults, defaultinputpollfreq = ' + str(
                                                   defaultoutputpollfreq), 3, pilib.systemstatusloglevel)

                    querylist.append(
                        'insert into inputs values (\'' + interface['id'] + '\',\'' + interface['interface'] + '\',\'' +
                        interface['type'] + '\',\'' + str(address) + '\',\'' + gpioname + '\',\'' + str(
                            value) + "','','" +
                        str(polltime) + '\',\'' + str(pollfreq) + "','" + ontime + "','" + offtime + "')")



                else:
                    pilib.writedatedlogmsg(pilib.systemstatuslog, 'GPIO address' + str(address) + ' disabled', 4,
                                       pilib.systemstatusloglevel)
                    GPIO.setup(address, GPIO.IN)
            else:
                pilib.writedatedlogmsg(pilib.systemstatuslog,
                                       'GPIO address' + str(address) + ' not allowed. Bad things can happen. ', 4,
                                       pilib.systemstatusloglevel)

        elif interface['interface'] == 'SPI0':
            pilib.writedatedlogmsg(pilib.systemstatuslog,'Processing SPI0',1,pilib.systemstatusloglevel)
            if interface['type'] == 'SPITC':
                import readspi

                spidata = readspi.readspitc(0)
                readspi.recordspidata(database, spidata)

            if interface['type'] == 'CuPIDlights':
                import spilights

                spilightsentries, setlist = spilights.getCuPIDlightsentries('indicators', 0, previndicators)
                querylist.extend(spilightsentries)
                spilights.updatelightsfromdb(pilib.controldatabase, 'indicators', 0)
                spilights.setspilights(setlist, 0)

        elif interface['interface'] == 'SPI1':
            pilib.writedatedlogmsg(pilib.systemstatuslog,'Processing SPI1',1,pilib.systemstatusloglevel)

            if interface['type'] == 'CuPIDlights':
                import spilights

                spilightsentries, setlist = spilights.getCuPIDlightsentries('indicators', 1, previndicators)
                querylist.extend(spilightsentries)
                spilights.setspilights(setlist, 1)

    # Set tables
    querylist.append(pilib.makesinglevaluequery('systemstatus', 'lastiopoll', pilib.gettimestring()))

    if owfsupdate:
        from owfslib import runowfsupdate

        devices, owfsentries = runowfsupdate(execute=False)
        querylist.extend(owfsentries)

    pilib.writedatedlogmsg(pilib.systemstatuslog, 'Executing query:  ' + str(querylist), 5, pilib.systemstatusloglevel)
    pilib.sqlitemultquery(pilib.controldatabase, querylist)


def updateioinfo(database, table):
    from pilib import readalldbrows, sqlitedatumquery, sqlitemultquery

    tabledata = readalldbrows(database, table)
    querylist = []
    for item in tabledata:
        itemid = item['id']
        name = sqlitedatumquery(database, 'select name from ioinfo where id=\'' + itemid + '\'')
        querylist.append(database, 'update ' + table + ' set name=\'' + name + '\' where id = \'' + itemid + '\'')
    if querylist:
        sqlitemultquery(querylist)


def testupdateio(times):
    from pilib import controldatabase

    for i in range(times):
        updateiodata(controldatabase)


if __name__ == '__main__':
    from pilib import controldatabase

    updateiodata(controldatabase)

