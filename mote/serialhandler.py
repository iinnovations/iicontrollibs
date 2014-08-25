#!/usr/bin/env python

# do this stuff to access the pilib for sqlite
import os, sys, inspect

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)


def write(message, port='/dev/ttyAMA0',baudrate=115200, timeout=1):
    ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
    ser.write(message)


def monitor(port='/dev/ttyAMA0',baudrate=115200, timeout=1):
    import serial
    from cupid.pilib import sqliteinsertsingle, controldatabase, gettimestring
    ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)

    print "Monitoring serial port " + ser.name
    data = []
    while True:
        ch = ser.read(1)
        if len(ch) == 0:
            # rec'd nothing print all
            if len(data) > 0:
                s = ''
                for x in data:
                    s += '%s' % x # ord(x)

                # Here for diagnostics
                # print '%s [len = %d]' % (s, len(data))

                # now process data
                datadict, message = processserialdata(s)
                if 'nodeid' in datadict:
                    print('entering data')
                    sqliteinsertsingle(controldatabase, 'remotes', [datadict['nodeid'], message, gettimestring()])

            data = []
        else:
            data.append(ch)


def processserialdata(data):
    try:
        message = data.strip().split('BEGIN RECEIVED')[1].split('END RECEIVED')[0]
        # print('message:')
        # print(message)
    except:
        print('there was an error processing the message')
        return
    else:
        from cupid.pilib import parseoptions
        datadict = parseoptions(message)
        return datadict, message