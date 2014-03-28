#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2014, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"


def updateiodata(database):

    # This recreates all input and output tables based on the interfaces table.
    # Thus way we don't keep around stale data values. We could at some point incorporate
    # a retention feature that keeps them around in case they disappear temporarily.
    # It also reads the elements if they are enabled and it's time to read them

    import pilib
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)

    tables = pilib.gettablenames(pilib.controldatabase)
    if 'interfaces' in tables:
        interfaces = pilib.readalldbrows(pilib.controldatabase, 'interfaces')
    else:
        print('interfaces table not found. Exiting')
        return
    if 'inputs' in tables:
        previnputs = pilib.readalldbrows(pilib.controldatabase, 'inputs')

        # Make list of IDs for easy indexing
        previnputids=[]
        for input in previnputs:
            previnputids.append(input['id'])

    if 'outputs' in tables:
        prevoutputs = pilib.readalldbrows(pilib.controldatabase, 'outputs')

        # Make list of IDs for easy indexing
        prevoutputids=[]
        for output in prevoutputs:
            prevoutputids.append(output['id'])

    if 'defaults' in tables:
        defaults = pilib.readalldbrows(pilib.controldatabase, 'defaults')[0]
        defaultinputpollfreq = defaults['inputpollfreq']
        defaultoutputpollfreq = defaults['outputpollfreq']
    else:
        defaultinputpollfreq = 60
        defaultoutputpollfreq = 60

    # We drop all inputs and outputs and recreate
    # Add all into one query so there is no time when the IO don't exist.

    querylist=[]
    querylist.append('drop table if exists inputs')
    querylist.append('drop table if exists outputs')
    querylist.append('create table outputs (id text primary key, interface text, type text, address text, name text, value real, unit text, polltime text, pollfreq real)')
    querylist.append('create table inputs (id text primary key, interface text, type text, address text, name text, value real, unit text, polltime text, pollfreq real)')
    pilib.sqlitemultquery(pilib.controldatabase,querylist)

    querylist=[]
    for interface in interfaces:

        if interface['interface'] == 'GPIO':

            options = pilib.parseoptions(interface['options'])

            # TODO : respond to more option, like pullup and pulldown

            address = interface['id'][4:]

            # Check if interface is enabled

            if interface['enabled']:

                # Get name from ioinfo table to give it a colloquial name
                name = pilib.sqlitedatumquery(database, 'select name from ioinfo where id=\'' + interface['id'] + '\'')
                print('name = ' + name + ' for id ' + interface['id'])

                # Append to inputs and update name, even if it's an output (can read status as input)

                if options['mode'] == 'output':
                    GPIO.setup(int(address), GPIO.OUT)
                    value = GPIO.input(int(address))

                    # Get output settings and keep them if the GPIO previously existed
                    if interface['id'] in prevoutputids:
                        pollfreq = prevoutputs[prevoutputids.index(interface['id'])]['pollfreq']
                        polltime = prevoutputs[prevoutputids.index(interface['id'])]['polltime']
                    else:
                        pollfreq = defaultoutputpollfreq
                        polltime = ''

                    # Add entry to outputs tables
                    querylist.append("insert into outputs values (\'" + interface['id'] + "\',\'" + interface['interface'] + "\',\'" + interface['type'] + "\',\'" + address + "\',\'" + name + "\'," + str(value) + ",\'\',\'" + str(polltime) + "\'," + str(pollfreq) + ")")
                else:
                    GPIO.setup(int(address), GPIO.IN)
                    value = GPIO.input(int(address))

                # Get input settings and keep them if the GPIO previously existed
                if interface['id'] in prevoutputids:
                    pollfreq = previnputs[prevoutputids.index(interface['id'])]['pollfreq']
                    polltime = previnputs[prevoutputids.index(interface['id'])]['polltime']
                else:
                    pollfreq = defaultinputpollfreq
                    polltime = ''


                # Add entry to outputs tables
                querylist.append("insert into inputs values (\'" + interface['id'] + "\',\'" + interface['interface'] + "\',\'" + interface['type'] + "\',\'" + address + "\',\'" + name + "\'," + str(value) + ",\'\',\'" + str(polltime) + "\',\'" + str(pollfreq) + "\')")

            else:
                GPIO.setup(int(address), GPIO.IN)

        elif interface['interface'] == 'I2C':
            if interface['enabled']:
                print("processing enabled I2C")
                if interface['type'] == 'DS2483':
                    # Check if interface is enabled
                    from owfslib import updateowfstable, updateowfsdatatable
                    #updateowfstable(database, 'owfs')
                    updateowfsdatatable(database, 'inputs')

        elif interface['interface'] == 'SPI':
            print("processing SPI")
            if interface['type'] == 'SPITC':
                import readspi
                spidata = readspi.readspitc()
                readspi.recordspidata(database, spidata)
            elif interface['type'] == 'CuPIDLights':
                import spilights
                spilights.updatelightsfromdb(pilib.controldatabase, 'indicators')

    # Set tables
    #print(querylist)
    pilib.sqlitemultquery(pilib.controldatabase, querylist)

    return ("io updated")


def updateioinfo(database,table):
    from pilib import readalldbrows, sqlitedatumquery, sqlitemultquery

    tabledata = readalldbrows(database, table)
    querylist = []
    for item in tabledata:
        itemid = item['id']
        name = sqlitedatumquery(database, 'select name from ioinfo where id=\'' + itemid + '\'')
        querylist.append(database, 'update ' + table + ' set name=\'' + name + '\' where id = \'' + itemid + '\'')
    if querylist:
        sqlitemultquery(querylist)


if __name__ == "__main__":
    import pilib
    updateiodata(pilib.controldatabase)

