#!/usr/bin/env python

# do this stuff to access the pilib for sqlite
import os, sys, inspect

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)


def write(message, port='/dev/ttyAMA0',baudrate=115200, timeout=1):
    import serial
    ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
    ser.write(message)


def monitor(port='/dev/ttyAMA0',baudrate=115200, timeout=1):
    import serial

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
                # print(s)
                try:
                    datadicts, messages = processserialdata(s)
                except IOError:
                    print('error processing message')
                else:
                    for datadict, message in zip(datadicts, messages):
                        try:
                            statusresult = processremotedata(datadict, message)
                        except:
                            print('error processing returned datadict, messge:')
                            print(message)

            data = []
        else:
            data.append(ch)


def processserialdata(data):
    from cupid.pilib import parseoptions
    datadicts = []
    messages = []
    # try:
    # Break into chunks
    split1 = data.strip().split('BEGIN RECEIVED')
    for split in split1:
        if split.find('END RECEIVED') >= 0:
            message = split.split('END RECEIVED')[0]
            messages.append(message)
            try:
                datadict = parseoptions(message)
            except:
                print('error parsing message')
            else:
                datadicts.append(datadict)
    # except:
    #     print('there was an error processing the message')
    #     return
    # else:
    return datadicts, messages



def processremotedata(datadict, stringmessage):
    import cupid.pilib as pilib
    if 'nodeid' in datadict:

        # We are going to search for keywords. Message type will not be explicitly declared so
        # as not to waste precious message space in transmission. Or we could tack these on in
        # the gateway, but we won't yet.

        # Then we have to construct a query where we will replace a unique item
        # This will take the form :
        #   update or replace in remotes where nodeid=3 and msgtype='iovalue' and iopin=3
        #   update or repalce in remotes where nodeid=2 and msgtype='owdev' and owrom='28XXXXXXXXXXXXXX'
        #               (and later which IO on this device)
        #   update or replace in remotes where nodeid=2 and msgtype='chanstat' channum=1
        #               (need to see if all channel variables can be fit into one message:
        #               channum, sv,pv,mode,state
        runquery = False
        nodeid = datadict['nodeid']
        querylist = []
        if 'iovalue' in datadict:
            # check to see if entry exists with node and ionum. Need to generalize these.
            # Might make sense to put then into an ID to compare. Other database, compatible?
            # iovalue type message
            try:
                msgtype = 'iovalue'
                keyvalue = datadict['iopin']
                keyvaluename = 'iopin'
            except:
                print('oops')
            else:
                runquery = True

        elif 'owdev' in datadict:
            try:
                msgtype = 'owdev'
                keyvalue = datadict['owrom'][2:]
                keyvaluename = 'owrom'
            except:
                print('oops')
            else:
                runquery = True
        if runquery:
            deletequery = pilib.makedeletesinglevaluequery('remotes', {'conditionnames': ['nodeid', 'keyvalue', 'keyvaluename'], 'conditionvalues': [nodeid ,keyvalue, keyvaluename]})
            insertquery = pilib.makesqliteinsert('remotes',  [nodeid, msgtype, keyvaluename, keyvalue, stringmessage, pilib.gettimestring()], ['nodeid', 'msgtype', 'keyvaluename', 'keyvalue', 'data', 'time'])
            querylist.append(deletequery)
            querylist.append(insertquery)
            pilib.sqlitemultquery(pilib.controldatabase, querylist)

            return 'all done'
        else:
            print('not running query')

if __name__ == '__main__':
    monitor()